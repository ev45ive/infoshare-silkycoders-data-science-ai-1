# Ćwiczenie BC-01: cotygodniowa prognoza popytu w Airflow z monitoringiem dokładności

## 1. Do czego służy to rozszerzenie względem samej analizy

- Analiza (notebook) odpowiada na pytania: jak prognozować tygodniowy popyt, jaka metoda pokonuje dzisiejszą praktykę (średnia z 4 tygodni) i o ile, z jakim przedziałem niepewności. Wynik to **jednorazowa** prognoza na tygodnie 2026-W39 do W42 i plan monitoringu opisany słowami.
- Rozszerzenie zamienia ją w **cotygodniowy proces**: prognoza co poniedziałek, zapis historii prognoz, automatyczne liczenie dokładności prognoz z przeszłości i alarm po przekroczeniu progu.
- Nowe pytania, na które analiza nie odpowiada:
  - jak udowodnić, że proces nie „podgląda przyszłości", skoro dane z przyszłości leżą w tym samym pliku,
  - co zrobić z przyszłymi promocjami, których w momencie prognozy nie znamy,
  - co planista ma zrobić, gdy dokładność spadnie,
  - jak wygląda prognoza w szczycie sezonu, którego backtest nie obejmuje,
  - czy proces jest powtarzalny (te same wyniki po ponownym uruchomieniu).
- Narzędzie: Apache Airflow (harmonogram tygodniowy, powtórka historyczna). Dodatkowo: ten sam kod czytający dane z plików i z hurtowni PostgreSQL.

## 2. Potrzeba biznesowa i jej przełożenie

- **Zlecenie (kierownik merchandisingu i alokacji):** dziś dosyłki planowane są ze średniej 4 tygodni „na oko". Przy zmianie sezonu i nowych kolekcjach raz są braki (kurtki), raz nadmiar. Potrzebna prognoza na 4 tygodnie, żeby zamykać plan dosyłek w poniedziałki, głównie dla top 20 modeli.
- **Co biznes dostaje po wdrożeniu:** w poniedziałek rano prognoza z przedziałem 80%, obok prognoza dzisiejszej praktyki, flagi ostrożności i informacja, czy proces ostatnio się mylił.

| Potrzeba biznesowa | Wymaganie techniczne |
| --- | --- |
| Prognoza co poniedziałek bez analityka | Harmonogram tygodniowy, jawny origin, dane „as of" niedziela przed originem |
| Wiedza, czy prognozie można ufać | Monitoring: WAPE i obciążenie prognoz z przeszłości względem dzisiejszej praktyki, próg alarmu |
| Bezpieczny powrót do starego sposobu | Prognoza dzisiejszej praktyki (B1) dostarczana zawsze obok |
| Rozliczenie decyzji | Historia prognoz (co przewidywaliśmy w danym tygodniu), konfiguracja i wersja kodu w wyniku |
| Ostrożność w szczególnych okresach | Flagi: nowy model, brak historii, szczyt sezonu, podejrzenie braku towaru |
| Jawne założenie o promocjach | Parametr uruchomienia „założenie o przyszłych promocjach" zapisany w wyniku |

## 3. Co musisz mieć

**Wyniki analizy BC-01** (`analizy/bc01-prognoza-popytu/`):
- notebook: zrozumienie zlecenia, audyt danych, eksploracja, hipotezy, baseline'y (B1: średnia 4 tygodni; B2: rok poprzedni × poziom), metody (statystyczna per seria, globalny model gradientowy, analogi dla nowych modeli), backtest z kroczącym originem, diagnostyka, prognoza W39–W42, dziennik pracy, tabela świąt zbudowana przez analityka;
- `raport-biznesowy.md`: tabela prognozy z przedziałami i flagami, kontrakt wejścia i wyjścia, plan monitoringu (próg alarmu, wyzwalacze ponownego uczenia);
- opcjonalnie `src/*.py`, `sql/*.sql`.

**Dane** (`datasets/synthetic/bc01/`, Parquet, sprzedaż 2025-01-01 do 2026-09-20):
- `dim_date`, `dim_store`, `dim_product`, `merch_plan` (kolekcja i planowana data premiery), `fact_sales`, `fact_inventory_daily` (tylko od sierpnia 2026);
- ograniczenia: brak kalendarza promocji, dostaw i historii cennika; `ListPrice` i `SalesAreaM2` bieżące; przebudowa sklepu Kraków Rynek około 2026-04-01.
- definicje: WAPE agregowane po całym zbiorze (nie średnia z WAPE serii), obciążenie, tydzień ISO grupowany po `IsoYear` razem z `IsoWeek`.

**Środowisko (repozytorium):**
- `ds-ml-linux-setup/`: `workshop.sh`, `compose/extras.yaml`, `compose/dags/workshop_smoke.py`, `verify-extras.sh`, `instrukcja-instalacji.md`.
- Airflow: standalone, metadane w SQLite, **2 GB pamięci i 1,5 CPU**, DAG-i tylko do odczytu, brak montowania danych i kodu, logowanie szkoleniowe.
- Baza: `databases/RetailDW-postgres/` (kontener `retaildw-postgres-1`, port 5433, `retaildw_ro`). **`merch_plan` nie ma odpowiednika w hurtowni.**

**Dokumentacja:**
- Backfill: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/backfill.html
- TaskFlow: https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html

**Wiedza wstępna:** prognozowanie szeregów czasowych, backtest z kroczącym originem, podstawy Pythona i Dockera.