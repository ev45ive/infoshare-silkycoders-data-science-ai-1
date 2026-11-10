# BC-04 w MLflow (E0–E4)

Śledzenie porównania metod z `../bc04-sell-through-przecena.ipynb` w MLflow 3.5.0. Zakres: setup, test klienta, jedno uruchomienie na metodę, parytet z notebookiem. Rejestr modelu i ocena tygodniowa (E5–E9) nie są zrobione.

## Uruchomienie

```bash
# 1. serwer (PostgreSQL + MLflow 3.5.0), poza repo, bez edycji plików
bash ~/infoshare-data-science-setup/ds-ml-linux-setup/workshop.sh up core
# UI: http://127.0.0.1:5000

# 2. środowisko (klient musi mieć tę samą wersję co serwer)
cd analizy/bc04-sell-through-przecena/mlflow
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m ipykernel install --user --name bc04-mlflow --display-name "BC04 MLflow (.venv)"

# 3. skrypty (adres tylko ze zmiennej środowiskowej)
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
export PYTHONPATH=src
.venv/bin/python src/e1_client_check.py     # E1: test klienta
.venv/bin/python src/run_reference.py       # liczby referencyjne z kopii notebooka (reference/)
.venv/bin/python src/check_core_parity.py   # parytet rdzenia bez MLflow
.venv/bin/python src/log_runs.py            # E3: uruchomienia w MLflow (każde wywołanie dodaje nowy zestaw, tag suite_id)
.venv/bin/python -m pytest tests -q         # parytet rejestru i brak sekretów (ostatni zestaw)
```

Notebook `bc04-mlflow-wdrozenie.ipynb` czyta ostatni zestaw (`reference/last_suite.json`); logowanie z notebooka włącza flaga `RUN_LOGGING`.

## Zawartość

| Ścieżka | Rola |
| --- | --- |
| `src/bc04_core.py` | kod z notebooka BC-04 (fazy 2–7) bez zmian logiki |
| `src/log_runs.py` | logowanie: parametry, metryki zbiorcze i per kolekcja, tagi wersji, małe artefakty |
| `src/run_reference.py` | wykonuje **kopię** oryginalnego notebooka i zapisuje `reference/ref_*` |
| `tests/test_parity.py` | rejestr = notebook; wersja klienta = serwera; brak sekretów w parametrach i tagach |

Zmienna `NORDVIK_BC04_DATA` nadpisuje ścieżkę do `datasets/synthetic/bc04`.
