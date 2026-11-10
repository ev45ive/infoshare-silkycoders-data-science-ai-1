# Uruchomienie asystenta BC-09 na Linuksie (krok po kroku)

Instrukcja dla agenta lub osoby bez kontekstu. Sprawdzona na Ubuntu, Python 3.12, Docker. Każdy krok ma warunek poprawności; jeśli nie jest spełniony, zatrzymaj się i nie zgaduj. Opis kanałów (REST, UI, MCP, administracja): [uruchomienie-i-uzycie.md](uruchomienie-i-uzycie.md) (jego komendy dotyczą Windows).

## 0. Wymagania

- Python 3.12 (`python3 --version`), Docker z uprawnieniami użytkownika (`docker ps` bez `sudo`), `curl`.
- Klucz API OpenAI z dostępem do modelu ustawionego w `usluga/service/core/config.py` (`LLM_MODEL`, obecnie `gpt-5.4-mini`). Klucz podaje użytkownik; nigdy nie wpisuj go do repozytorium, czatu ani logów.
- Kontener PostgreSQL `retaildw-postgres-1` na porcie 5433 (krok 2).

Zmienne używane poniżej (ścieżkę dostosuj):

```bash
export REPO=/sciezka/do/infoshare-silkycoders-data-science-ai-1
export SVC=$REPO/analizy/bc09-asystent-analityczny/usluga/service
export PY=$REPO/.venv/bin/python
```

## 1. Środowisko Pythona

```bash
cd "$REPO"
[ -x "$PY" ] || python3 -m venv .venv
cd "$SVC" && "$PY" -m pip install -r requirements.txt
```

Warunek: ostatnia linia pip zaczyna się od `Successfully installed` (lub `Requirement already satisfied`). Wersje są przypięte; przy konflikcie zgłoś go użytkownikowi.

## 2. PostgreSQL (baza stanu usługi)

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep retaildw-postgres-1
```

Jeśli kontenera nie ma:

```bash
cd "$REPO/databases/RetailDW-postgres"
[ -f .env ] || cp .env.example .env     # uzupełnij hasła w .env, zanim uruchomisz
./retaildw.sh up
```

Warunek: `retaildw-postgres-1 ... (healthy)`.

## 3. Plik `.env` usługi

Plik `$SVC/.env` jest poza repozytorium (gitignore) i nie istnieje po sklonowaniu. Wygeneruj go z szablonu (losowe sekrety), potem dopisz klucz:

```bash
cd "$SVC"
[ -f .env ] || "$PY" - <<'EOF'
import re, secrets
out = []
for line in open(".env.example", encoding="utf-8").read().splitlines():
    m = re.match(r"^(BC09_(?:STATE_OWNER_PASSWORD|STATE_SVC_PASSWORD|JWT_SECRET|SEED_PW_\w+))=$", line)
    out.append(f"{m.group(1)}={secrets.token_urlsafe(24)}" if m else line)
open(".env", "w", encoding="utf-8").write("\n".join(out) + "\n")
EOF
chmod 600 .env
echo 'OPENAI_API_KEY=<KLUCZ OD UŻYTKOWNIKA>' >> .env
```

Warunek: `grep -c '^OPENAI_API_KEY=sk-' .env` zwraca `1`. Po wykonaniu `.env` nie wypisuj na ekran bez maskowania.

## 4. Baza stanu, użytkownicy, dane

Wszystkie komendy z katalogu `$SVC` (wymagane: moduły `core` i `svc` są szukane względem tego katalogu).

```bash
cd "$SVC"
export PYTHONUTF8=1
bash db/provision.sh                  # tworzy bazę retaildw_bc09_state i role, wymaga kontenera z kroku 2
"$PY" -m svc.admin setup              # tabele punktów kontrolnych LangGraph
"$PY" -m svc.admin seed-users         # ala, bartek (requester), celina (approver)
"$PY" -c "from core import db; db.build_db()"   # DuckDB z plików Parquet
```

Warunki:
- `provision.sh` kończy się `gotowe: baza retaildw_bc09_state`.
- `seed-users` wypisuje `użytkownicy szkoleniowi gotowi`.
- Istnieje plik `$REPO/analizy/bc09-asystent-analityczny/cache/nordvik_bc09.duckdb` (ok. 10 MB). Dane źródłowe: `$REPO/datasets/synthetic/bc09/*.parquet`.

Polecenia są powtarzalne (można je uruchomić ponownie).

## 5. Test połączenia z modelem (przed startem usługi)

```bash
cd "$SVC" && set -a && . ./.env && set +a
"$PY" -c "
from core import llm
m,i,o = llm.chat([{'role':'user','content':'Powiedz: ok'}], None, 'smoke')
print('OK', m.content, i, o)"
```

- `OK ok ...`: dalej.
- `403 ... does not have access to model`: projekt nie ma tego modelu. Sprawdź dostępne: `"$PY" -c "from openai import OpenAI; print(sorted(m.id for m in OpenAI().models.list() if m.id.startswith(('gpt-4','gpt-5'))))"` i ustaw wybrany model w `LLM_MODEL` w `core/config.py`. Nie sprawdzano, czy modele starsze niż `gpt-5.4-mini` przyjmują `max_completion_tokens` (zmiana w `core/llm.py`).
- `401`: zły klucz.
- `400 ... max_tokens`: kod `core/llm.py` musi używać `max_completion_tokens`.

Wywołanie zużywa tokeny z twardego limitu 3 mln (`cache/llm_zuzycie.json`).

## 6. Start usługi

```bash
cd "$SVC"
PYTHONUTF8=1 "$PY" -m uvicorn svc.main:app --port 8000          # terminal 1 (proces ciągły)
PYTHONUTF8=1 "$PY" -m streamlit run ui/streamlit_app.py --server.headless true   # terminal 2 (opcjonalnie UI)
```

Uwaga: uruchamiaj z katalogu `$SVC` (inaczej `ui/streamlit_app.py` i moduły nie zostaną znalezione). Po zmianie kodu lub `.env` zrestartuj proces.

Warunki: `curl -s http://127.0.0.1:8000/health` zwraca `{"status":"ok"}`; UI pod `http://localhost:8501`.

## 7. Weryfikacja końcowa

```bash
cd "$SVC" && set -a && . ./.env && set +a
tok() { curl -s -X POST http://127.0.0.1:8000/auth/token -d "username=$1" -d "password=$2" | "$PY" -c "import sys,json; print(json.load(sys.stdin)['access_token'])"; }
ALA=$(tok ala "$BC09_SEED_PW_ALA")
TID=$(curl -s -X POST http://127.0.0.1:8000/threads -H "Authorization: Bearer $ALA" -H "Content-Type: application/json" -d '{}' | "$PY" -c "import sys,json; print(json.load(sys.stdin)['thread_id'])")
ask() { curl -s -X POST http://127.0.0.1:8000/threads/$TID/messages -H "Authorization: Bearer $ALA" -H "Content-Type: application/json" -d "{\"question\":\"$1\"}" | "$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('status'), [s['tool'] for s in d.get('steps',[])]); print((d.get('answer') or str(d))[:300])"; }
ask "Jaka była sprzedaż netto w sklepie S-WAW-01 w tygodniu 2026-W38?"
ask "Jak wygląda procedura zwrotu bez paragonu?"
```

Oczekiwane: pierwsze pytanie `answered ['run_sql']` (233 413,40 PLN), drugie `answered ['search_docs']` (wersja 3.0 od 2026-02-01).

Zatwierdzanie (cztery oczy): `ala` prosi o zadanie („Załóż zadanie dla zakupów: sprawdzić dosyłkę kurtek do Gdańska."), status `awaiting_approval`; `POST /approvals/<task_id>/decision` z `{"action":"approve"}` daje **403** dla `ala` i **200** dla `celina` (token `celina` z `$BC09_SEED_PW_CELINA`).

## 8. Najczęstsze błędy

| Objaw | Przyczyna | Co zrobić |
| --- | --- | --- |
| `500 Błąd wewnętrzny` z `request_id` przy pytaniu | błąd modelu (klucz, dostęp do modelu, parametr) | uruchom krok 5, tam widać właściwy błąd |
| `Brak zmiennej środowiskowej ...` | brak `.env` lub pusta wartość | krok 3 |
| `/health` zwraca 503 `degraded` | PostgreSQL nie działa | krok 2 |
| `provision.sh` nie znajduje kontenera | inna nazwa lub brak kontenera `retaildw-postgres-1` | krok 2 |
| `File does not exist: ui/streamlit_app.py` | zły katalog roboczy | `cd "$SVC"` |
| 401 po godzinie | token wygasa po 60 min | zaloguj się ponownie |
| 429 / 503 przy pytaniu | limit dzienny użytkownika (200 tys.) / łączny (3 mln) tokenów | poczekaj lub zgłoś użytkownikowi; limity są twarde |

## 9. Zasady dla agenta

- Nie uruchamiaj zbioru testowego (Faza 9) ani skryptów `_build/` (nie ma ich w repozytorium).
- Nie zmieniaj `src/asystent/` (rdzeń zamrożony); zmiany modelu dotyczą tylko kopii w `usluga/service/core/`.
- Nie zapisuj kluczy i haseł w repozytorium, dokumentach ani w wynikach komend.
