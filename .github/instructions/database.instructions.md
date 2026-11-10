---
description: "Use when querying, exploring schema, validating or modifying the RetailDW PostgreSQL database (schemas dw, reporting, src, stg, etl, ops), running pgsql tools, or writing migrations and seeds for retaildw. Covers connection profile, read-only default, schema checks, metric definitions and migration rules."
applyTo: "databases/**"
---
# Baza RetailDW (PostgreSQL)

## Połączenie
- Profil: `RetailDW` (id `E9FAC3AA-A4DB-4CA6-9CFD-B89E85C5E95E`), baza `retaildw`, `127.0.0.1:5433`.
- Hasła są tylko w `databases/RetailDW-postgres/.env`. Nie wpisuj ich do plików ani zapytań.
- Analizy wykonuj jako `retaildw_ro` (odczyt), jeśli to możliwe.
- Skrypt `retaildw.sh` nie ma prawa wykonania; uruchamiaj go przez `bash retaildw.sh <komenda>`.

## Schematy
- `src`: dane surowe (`sales_raw`, `inventory_raw`, `returns_raw`).
- `stg`: staging (`sales`, `inventory`, `returns`).
- `dw`: hurtownia (wymiary `dim_*`, fakty `fact_*`).
- `reporting`: widoki do raportów (`sales_daily`, `sales_weekly`, `margin_analysis`, `product_performance`, `stock_availability`, `store_scorecard`).
- `etl`: `load_log`, procedury `etl.load_*`. `ops`: `schema_migrations`.

## Zapytania
- Przed zapytaniem sprawdź schemat (`pgsql_db_context` albo `information_schema`). Nazw tabel i kolumn nie zgaduj.
- Przed policzeniem metryki sprawdź definicję w [docs/slownik-metryk.md](../../docs/slownik-metryk.md) i podaj źródło.
- „Sprzedaż” bez doprecyzowania = `net_amount` (netto przed zwrotami).
- Nie używaj `SELECT *`. Podawaj kolumny jawnie.
- Literały (kanał, sklep, daty, sezon) waliduj zapytaniem sprawdzającym.
- Duże wyniki eksportuj do pliku (`pgsql_export_query_results`), nie wczytuj ich do kontekstu.
- Zapytania zapisane do `.sql` mają nagłówek i sekcję `-- Notes:` zgodnie z [sql.instructions.md](sql.instructions.md).

## Modyfikacje
- Zmiany danych i schematu (`pgsql_modify`, `retaildw.sh seed`, `load`) wykonuj tylko po wyraźnym potwierdzeniu użytkownika.
- Nowa zmiana schematu = nowy plik `db/migrations/V###__opis.sql`. Nie edytuj zastosowanych migracji (`migrate` sprawdza sumę kontrolną).
- Skrypty uruchamiane na bazie wymagają `BEGIN`/`COMMIT` lub `--single-transaction`.

## Ścieżki w `databases/RetailDW-postgres/`
- `compose.yaml`: kontener PostgreSQL (pgvector pg17, port z `PG_PORT`).
- `retaildw.sh`: zarządzanie bazą (`up`, `migrate`, `seed`, `load`, `status`, `query`).
- `.env`: hasła lokalne (nie wpisuj ich do odpowiedzi). `.env.example`: wzór.
- `db/baseline.sql`: role, baza, schematy, uprawnienia.
- `db/migrations/`:
  - `V001`–`V003`: wymiary `dw` (`dim_date`, `dim_product`, `dim_store`).
  - `V004`: `etl.load_log`.
  - `V005`–`V007`: fakty `dw` (`fact_sales`, `fact_inventory_daily`, `fact_returns`).
  - `V008`–`V010`: `src` (surowe dane).
  - `V011`–`V013`: `stg` (staging).
  - `V014`–`V016`: funkcje pomocnicze ETL (`try_int`, `try_date`, `try_numeric`).
  - `V017`–`V019`: procedury `etl.load_*`.
  - `V020`–`V025`: widoki `reporting`.
- `db/seed/`:
  - `00_dim_date.sql`, `01_dim_product.sql`, `02_dim_store.sql`: wymiary.
  - `10_generate_source_data.sql`: generowanie danych do `src`.

## Polecenia `retaildw.sh`
Uruchamiaj z katalogu `databases/RetailDW-postgres/` przez `bash retaildw.sh <komenda>`.

Cykl życia:
- `up`: uruchamia kontener (jeśli trzeba), potem `baseline` i `migrate`.
- `down`: zatrzymuje i usuwa kontener; wolumen z danymi zostaje.
- `reset [-y]`: USUWA wolumen z danymi i buduje bazę od nowa. Wymaga potwierdzenia użytkownika.
- `setup`: `up` + `seed` + `load`, pełna baza od zera; można powtarzać.

Schemat i dane:
- `baseline`: role (hasła z `.env`), baza, schematy, uprawnienia; idempotentne.
- `migrate`: stosuje `db/migrations/V###__*.sql`, każdą w transakcji, zapis w `ops.schema_migrations` z sumą SHA-256. Ostrzega, gdy zastosowana migracja została zmieniona.
- `seed`: wypełnia wymiary i dane źródłowe w `src.*`; pomija, gdy są już wypełnione.
- `load`: pełne przeładowanie `stg.*` i `dw.*` z `src.*` przez procedury `etl.load_*`; wyniki w `etl.load_log`.

Podgląd:
- `status`: stan kontenera, liczba zastosowanych migracji, liczby wierszy w tabelach.
- `query [--ro] [--csv] "SQL"` lub `query [--ro] [--csv] -f plik.sql`: wykonuje SQL; `--ro` używa roli `retaildw_ro`. Wymaga działającego kontenera.
- `psql [--ro]`: interaktywna sesja psql.
- `logs [args]`: logi kontenera (domyślnie ostatnie 100 linii).

## Pliki poza zakresem
- Nie czytaj bezpośrednio plików w `datasets/` (duże). Używaj zapytań lub Pythona.
