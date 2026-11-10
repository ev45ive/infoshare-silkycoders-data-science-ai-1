"""Dostęp do danych: baza DuckDB zbudowana z Parquet; asystent dostaje WYŁĄCZNIE połączenie tylko do odczytu.

Warstwy kontroli (każda działa niezależnie od promptu):
 1. połączenie read_only=True (silnik odrzuca każdy zapis),
 2. enable_external_access=false + lock_configuration (brak czytania plików, brak zmiany ustawień),
 3. walidacja składni (sqlglot): jedna instrukcja SELECT, tylko schematy dbo/reporting,
 4. limit wierszy i limit czasu (przerwanie zapytania).
"""
import re
import threading

import duckdb
import sqlglot
from sqlglot import exp

from . import config

# Funkcje, które czytają pliki, zmieniają ustawienia albo ujawniają metadane serwera (read_*, copy, attach, pragma, duckdb_*, getenv ...).
# To druga linia obrony: pierwszą jest połączenie read_only z wyłączonym dostępem zewnętrznym.
BLOCKED_FUNCS = re.compile(
    r"\b(read_\w+|glob|copy|attach|detach|install|load|pragma|export|import|"
    r"parquet_\w+|duckdb_\w+|sniff_csv|query|query_table|current_setting|getenv)\b", re.I)


def build_db(path=config.DB_PATH, force=False):
    """Zbuduj plik bazy z Parquet (schematy dbo i reporting). To jedyne miejsce zapisu: robi je kod, nie asystent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return path
    if path.exists():
        path.unlink()
    con = duckdb.connect(str(path))
    for s in config.ALLOWED_SCHEMAS:
        con.execute(f"create schema {s}")
    for f in sorted(config.DATA.glob("*.parquet")):
        schema, table = f.stem.split(".", 1)
        con.execute(f'create table {schema}."{table}" as select * from read_parquet(\'{f.as_posix()}\')')
    con.close()
    return path


def open_readonly(path=config.DB_PATH):
    """Połączenie dla asystenta: tylko odczyt, bez dostępu do plików i bez możliwości zmiany ustawień.
    Konfiguracja idzie przy otwarciu (nie przez SET): drugie połączenie do tego samego pliku w procesie dzieli instancję i SET po blokadzie by się nie udał."""
    return duckdb.connect(str(path), read_only=True, config={"enable_external_access": False, "lock_configuration": True})


class SqlRejected(Exception):
    pass


def validate_sql(sql: str) -> str:
    """Zwraca oczyszczone SQL albo rzuca SqlRejected z powodem (powód wraca do modelu jako błąd narzędzia)."""
    if not sql or not sql.strip():
        raise SqlRejected("Puste zapytanie.")
    try:
        stmts = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except Exception as e:
        raise SqlRejected(f"Błąd składni SQL: {str(e)[:200]}")
    if len(stmts) != 1:
        raise SqlRejected("Dozwolona jest dokładnie jedna instrukcja SELECT.")
    # Walidacja działa na drzewie składni (sqlglot), nie na tekście: komentarze, wielkość liter i spacje nie pozwolą jej obejść.
    tree = stmts[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Subquery)):
        raise SqlRejected(f"Dozwolone są wyłącznie zapytania SELECT (otrzymano {type(tree).__name__}).")
    # Zakaz DML, DDL i poleceń administracyjnych w DOWOLNYM miejscu drzewa (także w podzapytaniu lub CTE), nie tylko na szczycie.
    banned = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command,
              exp.Copy, exp.Set, exp.Use, exp.Merge, exp.Pragma)
    for node in tree.walk():
        if isinstance(node, banned):
            raise SqlRejected(f"Niedozwolona operacja: {type(node).__name__}.")
    # Nazwy CTE (WITH nazwa AS ...) są dozwolone bez schematu: to nie są tabele.
    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    # Każda tabela musi mieć schemat z listy dozwolonych. Funkcje tabelaryczne (read_csv(...), duckdb_tables()) nie są identyfikatorem,
    # więc trafiają w pierwszą gałąź i są odrzucane.
    for t in tree.find_all(exp.Table):
        if not isinstance(t.this, exp.Identifier):
            raise SqlRejected("Funkcje tabelaryczne i odwołania do plików są niedozwolone.")
        schema = (t.args["db"].name.lower() if t.args.get("db") else "")
        if not schema:
            if t.name.lower() in ctes:
                continue
            raise SqlRejected(f"Tabela '{t.name}' musi mieć schemat: dbo.<tabela> lub reporting.<widok>.")
        if schema not in config.ALLOWED_SCHEMAS:
            raise SqlRejected(f"Schemat '{schema}' jest niedozwolony (dozwolone: {', '.join(config.ALLOWED_SCHEMAS)}).")
        if t.args.get("catalog"):
            raise SqlRejected("Odwołania do innych baz są niedozwolone.")
    # Funkcje skalarne i tabelaryczne z czarnej listy (pliki, ustawienia, system).
    for f in tree.find_all(exp.Anonymous):
        if BLOCKED_FUNCS.fullmatch(f.name or ""):
            raise SqlRejected(f"Funkcja '{f.name}' jest niedozwolona.")
    return sql.strip().rstrip(";")


def column_warnings(sql: str):
    """Ostrzeżenia z katalogu config.COLUMN_WARNINGS dla kolumn widoków użytych w zapytaniu (zapytanie jest już zwalidowane)."""
    tree = sqlglot.parse_one(sql, read="duckdb")
    tables = {t.name.lower() for t in tree.find_all(exp.Table)}
    cols = {c.name.lower() for c in tree.find_all(exp.Column)}
    return [msg for (view, col), msg in config.COLUMN_WARNINGS.items() if view in tables and col in cols]


def run_select(con, sql: str, max_rows=config.SQL_MAX_ROWS, timeout=config.SQL_TIMEOUT_S):
    """Wykonaj zwalidowane SELECT z limitem wierszy i czasu. Zwraca (kolumny, wiersze, obcięto?)."""
    clean = validate_sql(sql)
    # Limit czasu: osobny wątek przerywa zapytanie po `timeout` sekundach (con.interrupt). Limit wierszy: zapytanie jest opakowane
    # w SELECT ... LIMIT max+1, żeby po jednym nadmiarowym wierszu wiedzieć, że wynik został obcięty.
    timer = threading.Timer(timeout, con.interrupt)
    timer.start()
    try:
        cur = con.execute(f"select * from ({clean}) as _q limit {max_rows + 1}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    except duckdb.InterruptException:
        raise SqlRejected(f"Przekroczono limit czasu {timeout} s.")
    except duckdb.Error as e:
        raise SqlRejected(f"Błąd wykonania: {str(e)[:300]}")
    finally:
        timer.cancel()
    truncated = len(rows) > max_rows
    return cols, rows[:max_rows], truncated
