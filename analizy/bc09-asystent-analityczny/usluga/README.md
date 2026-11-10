# BC-09: asystent analityczny jako usługa (pilotaż, środowisko szkoleniowe)

Zamienia zamrożony prototyp z `../src/asystent` w usługę dla wielu użytkowników: logowanie i role, trwałe rozmowy, zatwierdzanie zadań przez inną, uprawnioną osobę
(także po restarcie), REST z dokumentacją, czat (Streamlit) i serwer MCP (bez zatwierdzania). **Nie poprawia jakości odpowiedzi** (jakość = wynik analizy, patrz `../raport-biznesowy.md`).

## Uruchomienie (z katalogu `service/`, środowisko `.venv` w korzeniu repozytorium, cztery poziomy wyżej)

Pełny opis kanałów (API, UI, MCP, administracja): [../docs/uruchomienie-i-uzycie.md](../docs/uruchomienie-i-uzycie.md). Skrót:

```bash
python -m pip install -r requirements.txt            # wersje przypięte
cp .env.example .env                                  # uzupełnij sekrety (losowe); .env jest poza repozytorium
cd ../../../../databases/RetailDW-postgres && ./retaildw.sh up && cd -                # PostgreSQL (kontener retaildw-postgres-1, port 5433)
bash db/provision.sh                                  # baza stanu retaildw_bc09_state, role bc09_state_owner i bc09_svc, migracja
python -m svc.admin setup                             # tabele punktów kontrolnych LangGraph (rola właściciela)
python -m svc.admin seed-users                        # ala, bartek (wnioskodawcy), celina (zatwierdzająca); hasła w .env
export OPENAI_API_KEY=...                             # model: gpt-4.1-mini (rdzeń); klucz tylko ze zmiennej środowiskowej
python -m uvicorn svc.main:app --port 8000            # REST; Swagger: http://127.0.0.1:8000/docs (przycisk Authorize)
python -m streamlit run ui/streamlit_app.py           # czat i widok zatwierdzeń (woła tylko API)
python -m pytest tests -q                             # testy (model testowy bez kosztu; baza stanu i DuckDB prawdziwe)
python -m svc.maintenance expire                      # wygaszanie zatwierdzeń; retention: python -m svc.maintenance retention 30
bash db/drop_state_db.sh                              # USUNIĘCIE bazy stanu i ról (pyta o potwierdzenie)
```

Dane asystenta: DuckDB tylko do odczytu (`../cache/nordvik_bc09.duckdb`, budowany przez analizę z Parquet). Adapter do PostgreSQL: poza zakresem tego etapu (patrz `ADR.md`).

## Układ

| Katalog | Zawartość |
| --- | --- |
| `service/core/` | kopia zamrożonego rdzenia + 3 łatki wstrzykiwania zależności (`agent.py`, `config.py`, `tools.py`); test `tests/test_persistence_and_core.py` pilnuje, że reszta jest bez zmian |
| `service/svc/` | `api.py` (FastAPI), `graph.py` (LangGraph), `store.py` (stan), `auth.py`, `gateway.py` (limity), `schemas.py`, `admin.py`, `maintenance.py` |
| `service/ui/`, `service/mcp_server/` | czat Streamlit, serwer MCP (stdio) |
| `service/db/` | migracje SQL, `provision.sh`, `drop_state_db.sh` |
| `service/tests/` | testy bezpieczeństwa i funkcji, regresja przez REST, serwer testowy |
| `ADR.md`, `RUNBOOK.md`, `raport-wdrozenia.md`, `bc09-usluga.ipynb` | decyzje, operacje, raport, notebook z dowodami |

## Zmienne środowiskowe

Patrz `service/.env.example`. Sekrety (hasła ról bazy, `BC09_JWT_SECRET`, hasła użytkowników szkoleniowych) są losowe i leżą tylko w `.env`. Limity (dzienny limit tokenów, długość pytania, ważność zatwierdzenia)
są konfigurowalne i **domyślnie takie same dla każdego użytkownika**.

## Podłączenie serwera MCP (np. VS Code)

Skopiuj `service/mcp.json.example` do `.vscode/mcp.json` w swoim obszarze roboczym (format `servers` z `inputs`; token wpisywany przy pierwszym użyciu, nie w pliku). Token: `POST /auth/token`.
Dla przenośnego `.mcp.json` użyj klucza `mcpServers` **bez** `inputs` i ustaw `BC09_API_TOKEN` w środowisku (nie kopiuj konfiguracji między formatami bez sprawdzenia). Narzędzia: `zapytaj_asystenta`, `status_zadania`, `szukaj_procedur`; **nie ma** narzędzia zatwierdzającego.
