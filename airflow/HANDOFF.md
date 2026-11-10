# Handoff: BC-01 prognoza tygodniowa w Airflow

Dokument do przejęcia pracy bez kontekstu poprzedniej rozmowy. Ścieżki są względem katalogu głównego repozytorium `infoshare-silkycoders-data-science-ai-1/`.

## Cel
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

## Stan prac

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
| `airflow/config/bc01.yaml` (horyzont, top 20, założenie o promocjach, ziarno) | ✅ | Progi alarmu WAPE i bias są `null`, do ustalenia (patrz pytanie 3). |
| Start Airflow i sprawdzenie połączenia z bazą `airflow` | ✅ | `airflow db check` OK, kontener `healthy`, `dags list-import-errors` bez błędów. Start: `docker compose up -d` w `airflow/`. |

### Faza 3: Kod wspólny
| Zadanie | Status | Uwagi |
| --- | --- | --- |
| `airflow/src/bc01/`: wczytanie danych „as of” (sekcja 3) | ⏳ | Dane do originu, bez danych po originie. |
| Transformacje (sekcja 5) | ⏳ | |
| Baseline B1 i metody M1, M2, analogi (sekcja 6) | ⏳ | M2 jest wynikiem do zapisu. Sekcja 4 zostaje poza kodem produkcyjnym. |
| Wyniki i flagi (sekcja 7) | ⏳ | |
| Testy kontraktu „as of” | ⏳ | |

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

## Pliki
- `databases/RetailDW-postgres/db/migrations/V026__create_forecast_schema.sql`
- `databases/RetailDW-postgres/db/airflow-setup.sql`
- `airflow/.env` (lokalny, nie w repo, zawiera hasło)
- `airflow/HANDOFF.md` (ten plik)

## Otwarte pytania
1. Przedział 80% jest na sumie 4 tygodni. Czy DAG ma też publikować przedziały tygodniowe?
2. Widok w `reporting` dla wyników prognoz: dodać jako `V027`?
3. Progi alarmu monitoringu (WAPE i bias): notebook i ticket ich nie podają. Do ustalenia ze zleceniodawcą; w `airflow/config/bc01.yaml` są `null`.
