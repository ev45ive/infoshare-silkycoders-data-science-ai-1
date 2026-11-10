# Runbook pilotażu: asystent BC-09 (środowisko szkoleniowe)

## Start i stop
- Start: `./retaildw.sh up` (w `databases/RetailDW-postgres`), `python -m uvicorn svc.main:app --port 8000`, opcjonalnie `python -m streamlit run ui/streamlit_app.py` (z `service/`).
- Kontrola: `GET /health` (200 `ok`; 503 `degraded` = baza stanu niedostępna). Logi: stdout procesu, wiersze `rid=<request-id> METODA ŚCIEŻKA -> KOD czas` (bez treści, bez nagłówków, bez sekretów).
- Stop: zatrzymanie procesu jest bezpieczne: wstrzymane zatwierdzenia leżą w bazie stanu i po starcie wznawiają się bez duplikatów (test: awaria procesu w trakcie oczekiwania).

## Użytkownicy
- Zakładanie: `BC09_NEW_USER_PASSWORD=... python -m svc.admin create-user LOGIN requester|approver` (hasło tylko ze zmiennej środowiskowej).
- Dezaktywacja: `python -m svc.admin deactivate LOGIN` (działa od razu: token przestaje być akceptowany; zadania i audyt zostają).
- Zmiana hasła/roli: ponowne `create-user` z tym samym loginem (nadpisuje hasło i rolę, aktywuje konto).
- Polityka haseł w pilotażu: do ustalenia ze zleceniodawcą (pytanie nr 4 w raporcie); środowisko szkoleniowe ma losowe hasła w `.env`.

## Audyt: kto zatwierdził co
```sql
SELECT a.at, u.username AS kto, a.action, a.task_id, a.detail
FROM svc.audit_log a LEFT JOIN svc.users u ON u.user_id = a.actor_id
WHERE a.task_id = <ID> ORDER BY a.audit_id;                 -- pytanie -> task_pending -> task_approve/reject (z poprawkami w detail.edits)
SELECT t.task_id, t.status, r.username AS wnioskodawca, p.username AS zatwierdzajacy, t.decided_at, t.edited
FROM svc.tasks t JOIN svc.users r ON r.user_id=t.requester_id LEFT JOIN svc.users p ON p.user_id=t.approver_id ORDER BY t.task_id DESC;
```

## Utknięte zatwierdzenia
- Lista oczekujących i ich wiek: `SELECT task_id, requester_id, expires_at FROM svc.tasks WHERE status='oczekuje' ORDER BY expires_at;`
- Wygaszanie (co godzinę): `python -m svc.maintenance expire` oznacza przeterminowane (`wygasle`) i kończy ich wątki. Decyzja po terminie: HTTP 410. Domyślny termin: 72 h (`BC09_APPROVAL_TTL_HOURS`).
- Zatwierdzający jest nieosiągalny: dezaktywuj konto wnioskodawcy tylko jeśli to konieczne; **operator nie zatwierdza zadań w imieniu użytkowników** (cztery oczy).

## Podejrzenie wstrzyknięcia poleceń (treść dokumentu lub zadania)
1. Sprawdź `audit_log` i `messages.trace` wątku (jakie narzędzia, jakie zapytania). Zapis bez zatwierdzenia jest niemożliwy z konstrukcji, więc ocenia się **treść** (czy asystent powtórzył fałszywą procedurę).
2. Dokument: usuń lub popraw u źródła (właściciel dokumentu); sanityzacja regułowa nie wychwytuje przeformułowań, więc przeglądaj nowe dokumenty ręcznie przed dodaniem do korpusu.
3. Zadanie z podejrzaną treścią: odrzuć (`reject`); wnioskodawcę poinformuj; zachowaj audyt.

## Koszt i limity
- Dzienny limit tokenów na użytkownika (`BC09_DAILY_TOKEN_LIMIT`, domyślnie 200 000, taki sam dla każdego); HTTP 429 po wyczerpaniu. Zużycie: `SELECT * FROM svc.usage_daily ORDER BY day DESC, tokens DESC;`.
- Limit czasu żądania 180 s (`BC09_REQUEST_TIMEOUT_S`), długość pytania 1000 znaków, limity rdzenia: 8 rund, 14 wywołań narzędzi, 60 000 tokenów na pytanie, łączny limit 3 mln tokenów w rejestrze (HTTP 503 po wyczerpaniu).

## Awaria modelu językowego
Objaw: HTTP 500 z `request_id` (szczegół w logach serwera) lub 503. Pytania wymagające modelu nie działają, **wyszukiwanie procedur (`GET /procedures/search`, MCP `szukaj_procedur`) działa bez modelu**. Wątki wstrzymane na zatwierdzenie nie zależą od modelu i dalej mogą być rozpatrywane.

## Sekrety i rotacja
- Sekrety: `.env` poza repozytorium; w repozytorium tylko `.env.example`. Rotacja `BC09_JWT_SECRET`: zmiana wartości i restart wylogowuje wszystkich (tokeny starego sekretu przestają działać). Rotacja haseł ról bazy: `ALTER ROLE` jako administrator + aktualizacja `.env`.
- Nigdy nie wklejaj zawartości `.env` ani tokenów do czatu, zgłoszeń ani logów.

## Retencja
- Punkty kontrolne rosną z każdym pytaniem: `python -m svc.maintenance retention 30` (kasuje punkty zakończonych wątków starszych niż 30 dni; wstrzymane zostają). Uruchamiać co tydzień. Wiadomości, zadania i audyt zostają (retencja do ustalenia ze zleceniodawcą).
- Testy i regresja zakładają użytkowników `t_*` i `reg_*` w tej samej bazie stanu: usunięcie ich danych (z wątkami, zadaniami, audytem, punktami kontrolnymi) robi `service/db/cleanup_test_data.sql`; użytkownicy szkoleniowi zostają.

## Granice środowiska szkoleniowego (czego brakuje do produkcji)
Brak TLS i SSO, pojedyncza instancja bez wysokiej dostępności, hasła szkoleniowe losowe lecz w pliku lokalnym, brak kopii zapasowych bazy stanu, brak blokady po serii błędnych logowań, brak odwołania pojedynczego tokenu,
brak monitoringu i alarmów, dane syntetyczne, model w chmurze zewnętrznego dostawcy (decyzja o zgodności należy do zleceniodawcy), adapter do PostgreSQL dla danych asystenta niezbudowany.
