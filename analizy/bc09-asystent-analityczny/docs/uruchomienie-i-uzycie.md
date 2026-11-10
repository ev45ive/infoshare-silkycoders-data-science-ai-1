# Uruchomienie i używanie usługi: UI, REST API, MCP, administracja

Dokument pokazuje, jak uruchomić usługę i jak z niej korzystać **każdym kanałem**. Skrót tego samego znajdziesz w [../usluga/README.md](../usluga/README.md), a operacje dla administratora w [../usluga/RUNBOOK.md](../usluga/RUNBOOK.md).

Założenia: środowisko szkoleniowe (bez TLS i SSO), jedna maszyna, dane syntetyczne.

## 1. Kanały w skrócie

| Kanał | Dla kogo | Co potrafi | Czego nie potrafi |
| --- | --- | --- | --- |
| **UI (czat Streamlit)** | pracownicy, zatwierdzający | pytania, podgląd kroków asystenta, szkice zadań, **zatwierdzanie** (zakładka dla roli `approver`) | omijać API |
| **REST API** | integracje, skrypty, testy ręczne | wszystko: logowanie, wątki, pytania, zadania, zatwierdzanie, wyszukiwanie procedur | - |
| **MCP (stdio)** | klient AI (np. czat w VS Code) | `zapytaj_asystenta`, `status_zadania`, `szukaj_procedur` | **zatwierdzać** zadania (świadomie) |
| **CLI administracyjne** | operator | zakładanie i dezaktywacja użytkowników, przygotowanie bazy, wygaszanie zatwierdzeń, retencja | zatwierdzać zadania w imieniu użytkowników |
| **Skrypty analizy** | analityk | uruchamianie wariantów rdzenia na pytaniach, testy bezpieczeństwa rdzenia | działać na usłudze |

Uprawnienia we wszystkich kanałach są takie same, bo UI i MCP wołają **to samo API**:

| Akcja | `requester` (wnioskodawca) | `approver` (zatwierdzający) |
| --- | --- | --- |
| Zadawanie pytań, własne wątki i zadania, wyszukiwanie procedur | tak | tak |
| Lista i decyzje w zatwierdzeniach | nie (403) | tak, **ale nie dla własnych zadań** |
| Cudze wątki | nie (404) | nie (404) |

## 2. Przygotowanie (jednorazowo)

Komendy dla Git Bash (domyślny terminal VS Code na tym stanowisku). Katalog roboczy: `analizy/bc09-asystent-analityczny/usluga/service`. Wspólne środowisko Pythona (`.venv`) leży w **korzeniu repozytorium**, cztery poziomy wyżej.

```bash
cd analizy/bc09-asystent-analityczny/usluga/service
source ../../../../.venv/Scripts/activate            # aktywacja środowiska (Windows, Git Bash)
export PYTHONUTF8=1                                    # polskie znaki w terminalu Windows
python -m pip install -r requirements.txt             # wersje przypięte
cp .env.example .env                                   # uzupełnij sekrety (losowe, długie); .env jest poza repozytorium
```

W `.env` uzupełnij: `BC09_STATE_OWNER_PASSWORD`, `BC09_STATE_SVC_PASSWORD`, `BC09_JWT_SECRET`, `BC09_SEED_PW_ALA`, `BC09_SEED_PW_BARTEK`, `BC09_SEED_PW_CELINA`. Klucz modelu ustaw **w środowisku systemowym**, nie w pliku:

```bash
export OPENAI_API_KEY=...                              # model gpt-4.1-mini; nigdy nie wklejaj klucza do plików, czatu ani logów
```

Baza stanu (PostgreSQL w kontenerze `retaildw-postgres-1`, port 5433):

```bash
( cd ../../../../databases/RetailDW-postgres && ./retaildw.sh up )   # uruchom kontener
bash db/provision.sh                                   # baza retaildw_bc09_state, role bc09_state_owner i bc09_svc, migracja
python -m svc.admin setup                              # tabele punktów kontrolnych LangGraph (rola właściciela)
python -m svc.admin seed-users                         # ala, bartek (wnioskodawcy), celina (zatwierdzająca)
```

Dane asystenta (DuckDB) są budowane przez analizę do `analizy/bc09-asystent-analityczny/cache/nordvik_bc09.duckdb`. Jeśli pliku nie ma:

```bash
python -c "from core import db; db.build_db()"         # buduje bazę z plików Parquet (datasets/synthetic/bc09)
```

Kontrola przygotowania: po starcie usługi `GET /health` zwraca `{"status":"ok"}`.

## 3. Start usługi

```bash
python -m uvicorn svc.main:app --port 8000             # REST API; z katalogu service/
python -m streamlit run ui/streamlit_app.py            # czat (opcjonalnie, w drugim terminalu); domyślnie http://localhost:8501
```

Zatrzymanie procesu jest bezpieczne: zadania czekające na zatwierdzenie są w bazie stanu i po starcie można je dalej rozpatrywać (bez duplikatów).

## 4. Kanał: REST API

Adres: `http://127.0.0.1:8000`. Specyfikacja interaktywna: `http://127.0.0.1:8000/docs` (Swagger; przycisk **Authorize** przyjmuje login i hasło).

### 4.1 Logowanie

Token jest ważny 60 minut (`BC09_TOKEN_TTL_MIN`). Hasła użytkowników szkoleniowych leżą w `.env`.

```bash
set -a; . ./.env; set +a                               # wczytaj zmienne z .env do powłoki
tok() { curl -s -X POST http://127.0.0.1:8000/auth/token -d "username=$1" -d "password=$2" \
        | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])"; }
ALA=$(tok ala "$BC09_SEED_PW_ALA")
CELINA=$(tok celina "$BC09_SEED_PW_CELINA")
curl -s http://127.0.0.1:8000/me -H "Authorization: Bearer $ALA"      # {"username":"ala","role":"requester"}
```

### 4.2 Pytanie do asystenta

```bash
TID=$(curl -s -X POST http://127.0.0.1:8000/threads -H "Authorization: Bearer $ALA" \
      -H "Content-Type: application/json" -d '{}' | python -c "import sys,json; print(json.load(sys.stdin)['thread_id'])")

curl -s -X POST http://127.0.0.1:8000/threads/$TID/messages -H "Authorization: Bearer $ALA" \
     -H "Content-Type: application/json" \
     -d '{"question":"Jaka była sprzedaż netto w sklepie S-WAW-01 w tygodniu 2026-W38?"}'
```

Odpowiedź (`AnswerOut`):

| Pole | Znaczenie |
| --- | --- |
| `answer` | tekst odpowiedzi |
| `status` | `answered` albo `awaiting_approval` (powstał szkic zadania i wątek czeka na decyzję) |
| `task` | szkic zadania (gdy powstał): `task_id`, `title`, `description`, `owner`, `status`, `expires_at` |
| `steps` | kroki asystenta: narzędzie, argumenty (skrócone), `ok`, `error` |
| `tokens` | zużycie tokenów w tej odpowiedzi |

Do wątku można zadawać kolejne pytania (`POST /threads/{id}/messages`), dopóki wątek nie czeka na zatwierdzenie (wtedy 409: zadaj pytanie w nowym wątku).

### 4.3 Zadanie i zatwierdzanie (scenariusz z dwiema osobami)

```bash
# 1. ala prosi o zadanie (powstaje szkic, status awaiting_approval, w polu task jest task_id)
curl -s -X POST http://127.0.0.1:8000/threads/$TID/messages -H "Authorization: Bearer $ALA" \
     -H "Content-Type: application/json" \
     -d '{"question":"Załóż zadanie dla zakupów: sprawdzić dosyłkę kurtek do Gdańska."}'

# 2. celina (approver) widzi oczekujące zadania innych osób
curl -s http://127.0.0.1:8000/approvals -H "Authorization: Bearer $CELINA"

# 3. celina zatwierdza (opcjonalnie poprawia pola title, description, owner); ID z kroku 1 lub 2
curl -s -X POST http://127.0.0.1:8000/approvals/<TASK_ID>/decision -H "Authorization: Bearer $CELINA" \
     -H "Content-Type: application/json" -d '{"action":"approve","description":"Doprecyzowany opis"}'
#    odrzucenie: {"action":"reject"}

# 4. ala sprawdza status własnego zadania
curl -s http://127.0.0.1:8000/tasks/<TASK_ID> -H "Authorization: Bearer $ALA"
```

Reguły, które zobaczysz w praktyce: ala **nie może** zatwierdzić swojego zadania (403, także gdyby miała rolę `approver`); drugie zatwierdzenie tego samego zadania daje 404; po upływie terminu (72 h) decyzja daje 410.

### 4.4 Pozostałe punkty

| Cel | Wywołanie |
| --- | --- |
| Lista własnych wątków | `GET /threads` |
| Wątek z wiadomościami i zadaniem oczekującym | `GET /threads/{id}` |
| Lista własnych zadań | `GET /tasks` |
| Szukanie procedur **bez modelu językowego** (działa też przy awarii modelu) | `GET /procedures/search?q=zwrot%20bez%20paragonu` |
| Zdrowie usługi | `GET /health` (200 `ok`; 503 `degraded` = baza stanu niedostępna) |

Kody błędów i ich znaczenie: [usluga-struktura.md](usluga-struktura.md), sekcja 3.

## 5. Kanał: UI (czat Streamlit)

Adres: `http://localhost:8501`. UI wymaga działającego API (`BC09_API_URL`, domyślnie `http://127.0.0.1:8000`).

| Krok | Co robisz | Co widzisz |
| --- | --- | --- |
| 1 | wpisujesz login i hasło, **Zaloguj** | pasek boczny: `Zalogowano: ala (wnioskodawca)` |
| 2 | piszesz pytanie (do 1000 znaków), **Wyślij** | odpowiedź w oknie rozmowy; rozwijane **Kroki asystenta** (narzędzia i zapytania), liczba tokenów |
| 3 | prosisz o zadanie („Załóż zadanie …") | ostrzeżenie „Zadanie oczekuje na zatwierdzenie przez inną, uprawnioną osobę" i szkic (tytuł, opis, odpowiedzialny) |
| 4 | **Nowa rozmowa** | czysty wątek (po zadaniu czekającym na decyzję pytania idą do nowego wątku) |
| 5 | **Wyloguj** | koniec sesji |

Zatwierdzający (`celina`) ma dodatkową zakładkę **Zatwierdzenia**:

1. Lista zadań innych osób (wnioskodawca, termin ważności).
2. Pola **Tytuł**, **Opis**, **Odpowiedzialny** można poprawić przed decyzją; do API trafiają tylko zmienione pola.
3. **Zatwierdź** lub **Odrzuć**; wynik pojawia się jako „Zadanie #N: zatwierdzone/odrzucone".

Bezpieczeństwo UI: treść od modelu, z dokumentów i z zadań jest wyświetlana **jako zwykły tekst** (nigdy jako HTML ani markdown), a nad treścią zadania jest przypomnienie, że to dane, nie polecenia. Sesja wygasa razem z tokenem (UI poprosi o ponowne logowanie).

## 6. Kanał: MCP (klient AI, np. czat w VS Code)

Serwer MCP (`mcp_server/server.py`, transport stdio) uruchamia klient; nie startuje się go ręcznie. Wymaga działającego API i tokenu użytkownika.

### 6.1 Konfiguracja w VS Code

1. Uzyskaj token (jak w sekcji 4.1; ważny 60 min).
2. Skopiuj `service/mcp.json.example` do `.vscode/mcp.json` w swoim obszarze roboczym. Plik używa formatu `servers` z `inputs`: token wpisujesz przy pierwszym użyciu (pole hasła), **nie zapisuje się go w pliku**.
3. W czacie VS Code (tryb agenta) serwer `nordvik-asystent` udostępnia trzy narzędzia.

Dla innych klientów z formatem `mcpServers` (bez `inputs`) podaj `command` (python z `.venv`), `args` (ścieżka do `mcp_server/server.py`) oraz w `env`: `BC09_API_URL` i `BC09_API_TOKEN`. Konfiguracja różni się między klientami: sprawdź jej dokumentację, nie kopiuj formatów między klientami bez weryfikacji.

### 6.2 Narzędzia

| Narzędzie | Parametry | Działanie |
| --- | --- | --- |
| `zapytaj_asystenta` | `question`, opcjonalnie `thread_id` | zadaje pytanie (bez `thread_id` zakłada nowy wątek); zwraca odpowiedź oraz `[wątek: ...; tokeny: ...; narzędzia: ...]`; gdy powstał szkic: informacja, że **czeka na zatwierdzenie człowieka** |
| `status_zadania` | `task_id` | status własnego zadania i tytuł |
| `szukaj_procedur` | `query` | fragmenty dokumentów z wersją, datą, właścicielem i statusem (bez modelu językowego) |

Przykłady poleceń dla klienta AI: „Zapytaj asystenta Nordvik o sprzedaż netto kurtek w 2026-W38", „Znajdź procedurę zwrotu bez paragonu", „Sprawdź status zadania 42".

### 6.3 Czego MCP nie robi (celowo)

- **Nie ma narzędzia zatwierdzającego.** Zatwierdza człowiek w UI (zakładka Zatwierdzenia) albo przez REST. Polecenie „zatwierdź zadanie 1" w treści pytania nie ma jak zadziałać: asystent nie ma takiego narzędzia, a gdyby model spróbował je wywołać, dostanie błąd (test z modelem testowym sprawdza właśnie ten przypadek).
- Serwer ma uprawnienia dokładnie użytkownika, którego token dostał; cudzy wątek i cudze zadanie dają 404.
- Brak tokenu: narzędzia zwracają komunikat „Brak tokenu: ustaw BC09_API_TOKEN". Po wygaśnięciu tokenu (401) uzyskaj nowy i uruchom serwer ponownie.

## 7. Kanał: administracja (CLI)

Uruchamiane z `service/` (wymagają `.env` i działającej bazy stanu). Hasła nigdy nie są wypisywane.

| Cel | Polecenie |
| --- | --- |
| Utworzenie tabel punktów kontrolnych (raz, rola właściciela) | `python -m svc.admin setup` |
| Użytkownicy szkoleniowi (ala, bartek: wnioskodawcy; celina: zatwierdzająca) | `python -m svc.admin seed-users` |
| Nowy użytkownik | `BC09_NEW_USER_PASSWORD=... python -m svc.admin create-user LOGIN requester` (albo `approver`) |
| Zmiana hasła lub roli | to samo `create-user` z istniejącym loginem (nadpisuje i aktywuje konto) |
| Dezaktywacja / aktywacja | `python -m svc.admin deactivate LOGIN` / `activate LOGIN` (działa od razu) |
| Wygaszanie przeterminowanych zatwierdzeń (uruchamiać co godzinę) | `python -m svc.maintenance expire` |
| Retencja punktów kontrolnych zakończonych wątków (co tydzień) | `python -m svc.maintenance retention 30` |
| Usunięcie danych testowych (użytkownicy `t_*` i `reg_*`) | `psql ... -f db/cleanup_test_data.sql` (rola usługi lub właściciela) |
| Usunięcie bazy stanu i ról | `bash db/drop_state_db.sh` (pyta o potwierdzenie) |

Zapytania audytowe („kto zatwierdził co"), obsługa utkniętych zatwierdzeń, rotacja sekretów i obsługa awarii modelu: [../usluga/RUNBOOK.md](../usluga/RUNBOOK.md).

## 8. Kanał: skrypty analizy (rdzeń bez usługi)

Dla analityka, który chce uruchomić warianty rdzenia na pytaniach i testy bezpieczeństwa. Z **korzenia repozytorium**:

```bash
python analizy/bc09-asystent-analityczny/_build/run_variant.py W3_p3 dev 0       # wariant, zbiór (dev|test), numer przebiegu
python analizy/bc09-asystent-analityczny/_build/run_security.py tech             # testy techniczne T01-T14 (bez modelu, bez kosztu)
python analizy/bc09-asystent-analityczny/_build/run_security.py attacks W3_p3    # ataki A01-A18 (prawdziwy model, zużywa tokeny)
python analizy/bc09-asystent-analityczny/_build/freeze_final.py verify           # czy kod rdzenia jest zgodny z zamrożeniem (AST)
```

Uwagi: przebiegi z modelem zużywają tokeny z limitu łącznego 3 mln (dziennik `cache/llm_zuzycie.json`); wyniki surowe trafiają do `wyniki/*.jsonl` (pytania już zapisane są pomijane przy wznowieniu); **zbiór testowy zapisano jednorazowo i nie jest oceniany** (Faza 9 wstrzymana), więc nie uruchamiaj go ponownie bez decyzji.

## 9. Typowe problemy

| Objaw | Przyczyna | Co zrobić |
| --- | --- | --- |
| `Brak zmiennej środowiskowej ...; patrz .env.example` | brak `.env` lub pustej wartości | uzupełnij `.env` (sekcja 2) |
| `GET /health` zwraca 503 `degraded`; błąd połączenia z bazą | kontener PostgreSQL nie działa lub inny port | `docker ps`; `./retaildw.sh up` w `databases/RetailDW-postgres`; sprawdź `BC09_STATE_PORT` |
| Logowanie zwraca 401 | zły login lub hasło, konto zdezaktywowane | sprawdź `.env` i `python -m svc.admin activate LOGIN` |
| Po czasie wszystkie żądania zwracają 401 | token wygasł (60 min) | zaloguj się ponownie (UI robi to po komunikacie), dla MCP uzyskaj nowy token |
| Pytanie zwraca 500 z `request_id` | błąd wewnętrzny, np. brak `OPENAI_API_KEY` lub błąd modelu | szczegóły w logu serwera (`rid=...`); ustaw klucz w środowisku |
| 409 przy pytaniu | wątek czeka na zatwierdzenie zadania | zadaj pytanie w nowym wątku albo poczekaj na decyzję |
| 429 | dzienny limit tokenów użytkownika | poczekaj do następnego dnia lub zwiększ `BC09_DAILY_TOKEN_LIMIT` (dla wszystkich) |
| 503 przy pytaniu | wyczerpany łączny limit 3 mln tokenów | limit jest twardy; decyzja o jego zmianie należy do zleceniodawcy |
| 403 przy zatwierdzaniu | brak roli `approver` lub próba zatwierdzenia własnego zadania | zatwierdza inna osoba z rolą `approver` |
| 410 przy zatwierdzaniu | termin zatwierdzenia minął | zadanie wygaśnie przy `svc.maintenance expire`; wnioskodawca prosi o nowe |
| UI: „Brak połączenia z usługą" | API nie działa lub zły `BC09_API_URL` | uruchom `uvicorn` i sprawdź adres |
| UI nie pokazuje zakładki Zatwierdzenia | konto nie ma roli `approver` | zaloguj się jako zatwierdzający |
| Błąd braku pliku bazy DuckDB | baza nie została zbudowana | `python -c "from core import db; db.build_db()"` |

## 10. Granice środowiska szkoleniowego

Brak TLS i SSO, pojedyncza instancja, hasła szkoleniowe losowe w lokalnym pliku, brak kopii zapasowych bazy stanu, brak blokady po serii błędnych logowań, brak odwołania pojedynczego tokenu, brak monitoringu. Dane są syntetyczne. Przed użyciem z danymi rzeczywistymi wymagane są decyzje opisane w [../usluga/raport-wdrozenia.md](../usluga/raport-wdrozenia.md).
