# Raport wdrożenia: asystent analityczny Nordvik jako usługa (pilotaż)

**Dla:** dyrektor operacyjny | **Stan:** środowisko szkoleniowe, dane syntetyczne | **Data:** 2026-11-10

## Decyzja

**Pilotaż może ruszyć w wąskim zakresie (poziom A: tylko odczyt)**, pod warunkami poniżej. Usługa jest gotowa technicznie, ale **nie poprawia jakości odpowiedzi** ponad wynik analizy (`../raport-biznesowy.md`).
Poziom B (szkice zadań do zatwierdzenia) działa technicznie i jest przetestowany, ale pozostaje warunkowy ze względu na jakość procedur, a nie na zabezpieczenia usługi.

## Co usługa gwarantuje (dowody w testach: 25 testów, wszystkie przechodzą)

| Gwarancja | Dowód |
| --- | --- |
| Żadnego zapisu ani zatwierdzenia bez uprawnionej osoby **innej niż wnioskodawca** | zatwierdza wyłącznie kod usługi po decyzji człowieka; model, REST, czat i serwer MCP nie mają żadnej drogi do zatwierdzenia; próba zatwierdzenia własnego zadania: odmowa w API i w bazie |
| Izolacja rozmów | cudzy wątek i zadanie: 404 (REST i MCP); identyfikatory UUID, własność sprawdzana przy każdym odwołaniu |
| Zatwierdzenie przeżywa awarię | proces kończony nagle w trakcie oczekiwania; nowy proces wznawia; powstaje **jedno** zadanie, druga decyzja nic nie robi |
| Ślad audytowy | kto zapytał, jakie narzędzia, kto zatwierdził i co poprawił (tabela `audit_log`) |
| Kontrola kosztu | dzienny limit tokenów na użytkownika (domyślnie jednakowy), limit czasu i długości pytania, limity rdzenia |
| Dane tylko do odczytu | osobne połączenie DuckDB tylko do odczytu; rola bazy stanu nie tworzy obiektów |

## Jakość: parytet z analizą (nie gwarancja ponad nią)

Na 34 pytaniach dev przez REST (dwa przebiegi, prawdziwy model): **31/34 i 30/34** poprawnych (91% i 88%; przedziały 95%: 77-97% i 73-95%), tyle co rdzeń w analizie (31/34, 77-97%).
Zgodność poprawności między przebiegami **97%**. Średnio ok. 7-8 tys. tokenów i 3 s na pytanie (rdzeń: 2,5 s; narzut usługi ok. pół sekundy). Te same słabości: **ujawnianie sprzecznych dokumentów** (limit korekty ceny 300 vs 500 PLN) i podatność na fałszywą treść w dokumencie.
Pytania testowe (16) uruchomiłem przez usługę **raz** i **nie oceniłem** (klucz odpowiedzi poza zasięgiem do rozliczenia).

## Granice (czego usługa nie gwarantuje)

Jakości ponad wynik analizy; wykrywania fałszywej treści w dokumentach; TLS, SSO, wysokiej dostępności i kopii zapasowych; testy obejmują wskazane przypadki ataków, nie wszystkie możliwe; współbieżność sprawdzona na pięciu wątkach; adapter do PostgreSQL dla danych asystenta nie jest zbudowany (test przenośności wykonany tylko w części o roli tylko do odczytu).

## Warunki pilotażu

1. Poziom A, użytkownicy: analitycy i zakupy; kierownicy sklepów po uporządkowaniu dokumentów (sprzeczność D06/D07, nieaktualny D01, D12 z `Revenue`, zdanie z poleceniem w D09).
2. Liczby z widocznym zapytaniem i definicją; procedury z cytatem i dopiskiem „zweryfikuj w dokumencie".
3. Monitorowanie: audyt, cotygodniowy przegląd 20 odpowiedzi przez człowieka, zgłaszanie błędów; uruchamianie `maintenance expire` co godzinę i `retention` co tydzień (`RUNBOOK.md`).
4. Przed danymi rzeczywistymi: decyzja o zgodności (dane do zewnętrznego dostawcy modelu), TLS i SSO.

## Otwarte pytania

Kto jest zatwierdzającym i kto go zastępuje? Jaki termin ważności zatwierdzenia (przyjęto 72 h)? Jakie limity kosztu (przyjęto 200 tys. tokenów dziennie na osobę, jednakowo)? Polityka haseł? Czy i kiedy potrzebny jest adapter do PostgreSQL dla danych asystenta?
