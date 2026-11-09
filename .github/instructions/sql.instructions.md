---
description: "Use when writing, editing, reviewing, or explaining SQL queries in .sql files or SQL snippets for Nordvik sales, returns, margin, stores, or inventory analysis. Covers query header, metric definitions from slownik-metryk, query structure, and documenting pitfalls."
applyTo: "**/*.sql"
---
# Zasady dla zapytań SQL

## Definicje i źródła
- Przed napisaniem zapytania sprawdź metrykę w [slownik-metryk.md](../../docs/slownik-metryk.md) i podaj źródło (tabela, kolumna).
- Nazwy tabel i kolumn bierz ze słownika lub z istniejących plików w `sql/`. Nie zgaduj nazw.
- Przykłady w [sql-dokumentacja-i-przykłady.md](../../docs/sql-dokumentacja-i-przykłady.md) używają innych nazw tabel i definicji niż słownik. Przy konflikcie obowiązuje słownik.
- Słowo „sprzedaż” bez doprecyzowania oznacza sprzedaż netto przed zwrotami. Sprzedaż brutto używaj tylko, gdy pytanie dotyczy kwoty zapłaconej przez klienta.

## Nagłówek
- Każde nowe zapytanie zaczyna się nagłówkiem: `Query Name`, `Author`, `Created`, `Updated`, `Purpose` (wzór w [sql-dokumentacja-i-przykłady.md](../../docs/sql-dokumentacja-i-przykłady.md)).
- Przy edycji zapytania aktualizuj `Updated`; jeśli nagłówka brak, dodaj go.
- Pole `Author` wypełniaj tylko wtedy, gdy użytkownik podał autora.

## Struktura
- Nie używaj `SELECT *`. Wymieniaj kolumny jawnie, z czytelnymi aliasami.
- Zakresy dat zapisuj jako `>= data_start AND < data_end`, jak w [weekly_sales.sql](../../sql/weekly_sales.sql).
- Zapytania dłuższe niż 100 linii rozbijaj na CTE (`WITH`).
- Nie używaj `CROSS JOIN`.
- Wartości stałe (sezon, kanał, daty) opisz w komentarzu lub przekaż jako parametr.
- Pułapki (NULL, opóźnienia danych, zwroty, duplikaty) opisz w sekcji `-- Notes:` na końcu pliku.

## Bezpieczeństwo
- Nie wpisuj haseł ani connection stringów do plików SQL.

## Weryfikacja
- Przed oddaniem zapytania przejdź checklistę z sekcji „Checklist SQL” w [sql-dokumentacja-i-przykłady.md](../../docs/sql-dokumentacja-i-przykłady.md).
