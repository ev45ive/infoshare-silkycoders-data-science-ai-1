# Handoff: BC-01 prognoza tygodniowa w Airflow

Ostatnia aktualizacja: 2026-11-10. Ścieżki względem katalogu głównego repozytorium.

## Następny krok
Uzupełnić Fazę 3 o transformacje i metody M1 oraz M2 (sekcje 5 i 6 notebooka) w `airflow/src/bc01/`, potem porównać B1 z `analizy/bc01-prognoza-popytu/prognoza-W39-W42-top20.csv`. Sprawdzenie: `cd airflow && PYTHONPATH=src /tmp/bc01-test-venv/bin/python -m pytest -q tests`.

## Kryteria akceptacji
- Cel: cotygodniowa prognoza BC-01 zapisywana w `forecast.*`, z monitoringiem WAPE i bias oraz alarmem.
- Kryteria akceptacji:
  - [ ] Dane wczytane tylko sprzed originu (test kontraktu przechodzi)
  - [ ] B1 zgodny z CSV referencyjnym w fazie 5
  - [ ] Dwa uruchomienia tego samego tygodnia dają identyczne wyniki
  - [ ] `airflow dags list-import-errors` bez błędów

## Źródła
| Źródło | Ścieżka | Do czego służy |
| --- | --- | --- |
| Ticket | `zgloszenia/Analizy/BC-01-prognoza-popytu--airflow.md` | Specyfikacja (poza zakresem agenta bez przekazania pliku) |
| Notebook | `analizy/bc01-prognoza-popytu/bc01-prognoza-popytu.ipynb` | Źródło logiki |
| Wynik referencyjny | `analizy/bc01-prognoza-popytu/prognoza-W39-W42-top20.csv` | Punkt odniesienia |
| SQL agregacji | `analizy/bc01-prognoza-popytu/sql/weekly_sales_style_store.sql` | Definicja tygodniowej sprzedaży |
| Konfiguracja | `airflow/config/bc01.yaml` | Parametry (horyzont, top 20, progi testowe) |
| Kontrakt | `airflow/tests/test_bc01_contract.py` | Testy as-of i B1 |

## Ograniczenia
- Hasła i klucze nie trafiają do plików, argv ani czatu. Przechowywane tylko w `airflow/.env` (w `.gitignore`).
- Zmiana hasła roli `airflow` (`ALTER ROLE`) wymaga potwierdzenia.
- Zmiany schematu tylko przez nową migrację, po potwierdzeniu użytkownika. Nie edytować zastosowanych migracji.
- Nie czytać `.specstory/`, `notatki/`, `docs/ai-sessions/`. `zgloszenia/` tylko po przekazaniu pliku przez użytkownika.
- Sekcja 4 notebooka (eksploracja) nie trafia do kodu produkcyjnego.
- Nie commitować `airflow/.env`.

## Rejestr decyzji
| ID | Data | Decyzja | Uzasadnienie | Zatwierdził | Status |
| --- | --- | --- | --- | --- | --- |
| D-01 | 2026-11-10 | Metadane Airflow w PostgreSQL (baza `airflow`, rola `airflow`) | Decyzja użytkownika zamiast SQLite | użytkownik | przyjęta |
| D-02 | 2026-11-10 | Dane wejściowe z Parquet, nie z RetailDW | `merch_plan` nie istnieje w RetailDW | użytkownik | przyjęta |
| D-03 | 2026-11-10 | Przedział 80% liczony na sumie 4 tygodni | Tak jest w `analizy/bc01-prognoza-popytu/prognoza-W39-W42-top20.csv` | użytkownik | przyjęta |
| D-04 | 2026-11-10 | Progi alarmu WAPE 0,30 i bias 0,10 | Wartości testowe | użytkownik | do zmiany |

## Kontekst

Dokument do przejęcia pracy bez kontekstu poprzedniej rozmowy. Ścieżki są względem katalogu głównego repozytorium `infoshare-silkycoders-data-science-ai-1/`.

Cotygodniowa prognoza popytu z analizy BC-01 uruchamiana przez Apache Airflow: prognoza co poniedziałek, zapis historii, monitoring dokładności, alarm.

Specyfikacja (ticket): `zgloszenia/Analizy/BC-01-prognoza-popytu--airflow.md`.
Notebook źródłowy: `analizy/bc01-prognoza-popytu/bc01-prognoza-popytu.ipynb`.
Punkt odniesienia wyników: `analizy/bc01-prognoza-popytu/prognoza-W39-W42-top20.csv`.

## Ustalenia
- Dane wejściowe: Parquet w `datasets/synthetic/bc01/` (montowane do kontenera). `merch_plan` nie istnieje w RetailDW, więc hurtownia nie jest źródłem.
- Metadane Airflow: osobna baza `airflow` na instancji RetailDW (port 5433), rola `airflow`. Nie używać bazy `retaildw`.
- Wyniki prognoz: schemat `forecast` w RetailDW.
- Hasła nigdy nie wpisywać do plików ani zapytań. Hasło roli `airflow` jest w `airflow/.env` (w `.gitignore`).
- Zasady pracy z bazą: `.github/instructions/database.instructions.md`. Zmiany schematu tylko przez nową migrację, po potwierdzeniu użytkownika.

## Plan i status

Legenda statusów: ✅ zrobione, ⏳ do zrobienia, ℹ️ ustalone (bez akcji do wykonania).

### Faza 0: Rozpoznanie
| Zadanie | Status | Uwagi |
| --- | --- | --- |
| Sprawdzenie Dockera | ✅ | Kontener `retaildw-postgres-1` działa i jest zdrowy. |
| Brak `ds-ml-linux-setup/` w workspace | ℹ️ | Konfiguracja Airflow powstaje od zera. |
| Brak `raport-biznesowy.md` i `src/` | ℹ️ | Do utworzenia w fazach 3 i 4. |
| Nagłówki notebooka | ✅ | Sekcje: 2 Setup, 3 Load, 4 Explore, 5 Transform, 6 Analyze, 7 Results. |

### Faza 1: Baza danych
| Zadanie | Status | Uwagi |
| --- | --- | --- |
| Migracja `V026__create_forecast_schema.sql` | ✅ | Zastosowana przez `bash retaildw.sh migrate`. |
| Skrypt `db/airflow-setup.sql` (rola i baza `airflow`, uprawnienia) | ✅ | Uruchomiony po migracji. Hasło przez stdin jako psql `airflow_password`. |
| Weryfikacja uprawnień | ✅ | Schemat `forecast` ma 3 tabele, baza `airflow` należy do roli `airflow`, rola ma INSERT do `forecast.run`. |
| Migracja `V027` z widokiem w `reporting` | ⏳ | Wymaga potwierdzenia użytkownika. |

### Faza 2: Konfiguracja Airflow
| Zadanie | Status | Uwagi |
| --- | --- | --- |
| `airflow/compose.yaml`: Airflow standalone 3.4.0, metadane w PostgreSQL | ✅ | Limit 2 GB RAM i 1,5 CPU. DAG-i i kod read-only. Dane Parquet read-only. Sieć `retaildw_default`, host `postgres`. Wymaga działającego stacku RetailDW. |
| `airflow/config/bc01.yaml` (horyzont, top 20, założenie o promocjach, ziarno) | ✅ | Progi alarmu są TESTOWE: WAPE 0,30, bias 0,10. Użytkownik je zmieni później (patrz pytanie 3). |
| `airflow/.env.example` (wzorzec sekretów, bez wartości) | ✅ | Kopiuj do `airflow/.env` i uzupełnij `change-me`. Plik `.env` jest w `.gitignore`. Ten wzorzec nie zawiera żadnych wartości. |
| Start Airflow i sprawdzenie połączenia z bazą `airflow` | ✅ | `airflow db check` OK, kontener `healthy`, `dags list-import-errors` bez błędów. Start: `docker compose up -d` w `airflow/`. |

### Faza 3: Kod wspólny
| Zadanie | Status | Uwagi |
| --- | --- | --- |
| `airflow/src/bc01/data.py`: wczytanie danych „as of” (sekcja 3), agregacja tygodniowa, top N | ✅ | Filtr `Date < origin`, origin musi być poniedziałkiem. Tylko warstwa wspólna, nie pełny potok. |
| `airflow/src/bc01/baseline.py`: B1 (średnia 4 tygodni x 4) | ✅ | Uproszczenie: brak zer przed startem serii i brak uzupełnień kalendarza z notebooka. Do zgodności z CSV w fazie 5. |
| `airflow/src/bc01/calendar.py`: kalendarz sklepów (święta PL, niedziele handlowe, dni otwarcia tygodnia) | ✅ | Testy w `test_bc01_data_layer.py`, przechodzą. Dane zaczynają się w 2025, więc reguła dla lat wcześniejszych nie ma wpływu (Q-04 zamknięte). Zależność: pakiet `holidays`. |
| `airflow/src/bc01/panel.py`: panel tygodniowy model x lokalizacja, start serii, maska przed startem | ✅ | Testy w `test_bc01_data_layer.py`. |
| `airflow/src/bc01/stockouts.py`: flagi podejrzenia braku towaru (port komórki 50) | ✅ | Test syntetyczny w `test_bc01_data_layer.py`. Brak jeszcze czyszczenia `YI`. |
| `load_catalog` w `data.py` (modele, lokalizacje, kolekcja BASIC z `merch_plan`) | ✅ | Używane przez test zgodności z CSV. |
| Zgodność B1 i flag z `prognoza-W39-W42-top20.csv` (origin 2026-09-21) | ✅ | 120 wierszy, B1 w tolerancji 0,05 (CSV zaokrąglony do 1 miejsca), flagi identyczne. Test pomijany bez danych. |
| `airflow/src/bc01/features.py`: czyszczenie `YI` (`clean_sales`), `aggregates` (MT, CT), `feature_rows` (port komórek 48–52) | ✅ | Testy w `test_bc01_features.py`: tylko oflagowane tygodnie zmieniane w `YI`, brak wycieku z tygodni ≥ origin do cech. Zgodność M1/M2 z cache jeszcze do sprawdzenia. |
| Kalendarz tygodniowy: `special_days`, `week_calendar` w `calendar.py` | ✅ | Cechy `wk_*`, dni otwarcia, niedziele handlowe, `holidays_monsat`. |
| Reguły zer (sekcja 5) | ⏳ | Do przeniesienia razem z M1. |
| Metody M1, M2 (LightGBM), analogi, B2 (sekcja 6) | ⏳ | M2 jest wynikiem do zapisu. Sekcja 4 zostaje poza kodem produkcyjnym. |
| Przedziały i wyniki, flagi (sekcja 7) | ⏳ | |
| Testy kontraktu „as of” i B1 | ✅ | `airflow/tests/test_bc01_contract.py`, 4 testy przechodzą (pytest w venv poza repo). |

### Faza 4: DAG-i
| Zadanie | Status | Uwagi |
| --- | --- | --- |
| `airflow/dags/bc01_prognoza_tygodniowa.py` | ⏳ | Poniedziałki. Zapis do `forecast.*` z wersją konfiguracji i kodu. |
| `airflow/dags/bc01_monitoring_dokladnosci.py` | ⏳ | WAPE i obciążenie względem B1. Alarm po przekroczeniu progu. |
| Backfill historyczny | ⏳ | Ręczne uruchomienie z parametrem daty. |

### Faza 5: Weryfikacja
| Zadanie | Status | Uwagi |
| --- | --- | --- |
| `airflow dags list-import-errors` i testy DAG-ów | ⏳ | |
| Zgodność z `prognoza-W39-W42-top20.csv` | ⏳ | |
| Dwa uruchomienia tego samego tygodnia dają identyczne wyniki | ⏳ | Powtarzalność. |
| Flagi i alarm na danych historycznych | ⏳ | |

## Ustalenia techniczne z fazy 1
- Schemat `forecast` (V026):
  - `forecast.run`: jeden przebieg (origin, as_of, horyzont, wersja konfiguracji i kodu, założenie o promocjach, status).
  - `forecast.series_forecast`: suma 4 tygodni na model x lokalizacja (p10, prognoza, p90, B1, flagi). Odpowiada kolumnom CSV.
  - `forecast.weekly_units`: rozbicie tygodniowe (ISO rok, tydzień).
- Przedziały p10/p90 w CSV dotyczą sumy 4 tygodni, nie pojedynczego tygodnia.
- Kolejność provisioningu: `bash retaildw.sh migrate`, potem `db/airflow-setup.sql` (wymaga schematu `forecast`).
- Uruchomienie `airflow-setup.sql` (wzorzec, bez zapisywania hasła do pliku):
  `PW="$(openssl rand -hex 24)"` ... `{ printf "\\set airflow_password '%s'\n" "$PW"; cat db/airflow-setup.sql; } | docker compose exec -T postgres psql -U postgres -d postgres -v ON_ERROR_STOP=1 -q`
  Uruchamiać z `databases/RetailDW-postgres/`. Ponowne uruchomienie zmienia hasło w bazie, więc nowe hasło trzeba zapisać w `airflow/.env`.

## Jak weryfikować
- `docker compose ps --format '{{.Health}}'` (w `airflow/`) — oczekiwany wynik: `healthy`4
- `docker compose exec -T airflow airflow dags list-import-errors` — oczekiwany wynik: `No data found`
- `PYTHONPATH=src /tmp/bc01-test-venv/bin/python -m pytest -q tests` (w `airflow/`) — oczekiwany wynik: 10 passed. Venv tymczasowy: pandas, pyarrow, pytest, numpy, python-dateutil, holidays; w razie braku odtworzyć.

## Pliki
- `databases/RetailDW-postgres/db/migrations/V026__create_forecast_schema.sql`
- `databases/RetailDW-postgres/db/airflow-setup.sql`
- `airflow/.env` (lokalny, nie w repo, zawiera hasło)
- `airflow/HANDOFF.md` (ten plik)
- `airflow/src/bc01/features.py`, `airflow/tests/test_bc01_features.py`
- `airflow/src/bc01/calendar.py`, `panel.py`, `stockouts.py`, `load_catalog` w `data.py`
- `airflow/tests/test_bc01_data_layer.py`

## Otwarte pytania
1. Przedział 80% jest na sumie 4 tygodni. Czy DAG ma też publikować przedziały tygodniowe?
2. Widok w `reporting` dla wyników prognoz: dodać jako `V027`?
3. Progi alarmu monitoringu (WAPE i bias): notebook i ticket ich nie podają. Obecnie w `airflow/config/bc01.yaml` są wartości TESTOWE: WAPE 0,30, bias 0,10. Użytkownik je zmieni później.
4. Q-04 zamknięte: dane zaczynają się w 2025, reguła niedziel handlowych dla wcześniejszych lat nie jest potrzebna.
5. Zamknięte: `holidays==0.108` i `python-dateutil` dodane w `compose.yaml` przez `_PIP_ADDITIONAL_REQUIREMENTS` (decyzja użytkownika). Instalacja przy starcie kontenera; po zmianie wersji trzeba przebudować pin.

Właściciel pytań Q-01…Q-03: użytkownik. Założenia tymczasowe: Q-01 tylko suma 4 tygodni; Q-02 brak migracji V027; Q-03 progi testowe z `bc01.yaml`.
 (etap cech): `features.py` (`clean_sales`, `aggregates`, `feature_rows`), kalendarz tygodniowy (`week_calendar`), `test_bc01_features.py`; sprawdzono: 14 testów przechodzi (w tym brak wycieku z tygodni ≥ origin); otwarte: zgodność M1/M2 z cache, M3, przedziały, DAG-i.
- 2026-11-10 — zrobiono
## Dziennik postępu
- 2026-11-10 — zrobiono (etap danych, faza 3): `load_catalog`, `calendar.py`, `panel.py`, `stockouts.py`, testy `test_bc01_data_layer.py`; sprawdzono: 10 testów przechodzi, B1 i flagi zgodne z CSV dla origin 2026-09-21; otwarte: YI, features, M1, M2, M3, przedziały, DAG-i; Q-04, zależność `holidays`.
- 2026-11-10 — zrobiono: migracja V026, rola `airflow`, `.env.example`, Compose, `config/bc01.yaml`, `src/bc01/data.py` (as-of), `src/bc01/baseline.py` (B1), testy kontraktu, handoff zgodny z szablonem; sprawdzono: 4 testy przechodzą, `airflow db check` OK, kontener `healthy`, brak błędów importu DAG; commit `83e32da`; otwarte: M1/M2, DAG-i, Q-01…Q-03
