# Handoff: AI w pracy data scientist - czego się nauczyliśmy

Zakres: wyłącznie to, co dotyczy pracy z AI (agenty, skille, prompty, instrukcje, handoff, weryfikacja). Tematy znane z pracy DS (statystyka, SQL, modelowanie, definicje metryk) pominięte.

Źródła: historia commitów (`commits.md`) i pliki repo (`AGENTS.md`, `.github/`, `airflow/HANDOFF.md`). Notatek i zapisów sesji nie użyto.

## 1. Czego się nauczyliśmy - w skrócie

- Agent ma pytać, nie zgadywać. Brakujące informacje zbiera przez `vscode_askQuestions` z propozycjami wyboru.
- Każdy krok procesu kończy się akceptacją człowieka. Bez zgody nie zapisujemy profilu, przepisu, `AGENTS.md` ani nie instalujemy pakietów.
- Założenia są oznaczane statusem: przyjęta, tymczasowa, do potwierdzenia, do zmiany. Agent nie traktuje swoich przybliżeń jako ustalonych.
- Procedura ma działać w nowej sesji. Dlatego zapisujemy ją w skillu, instrukcji lub prompt file, a nie w historii rozmowy.
- Dobry prompt: wąski kontekst, rola, cel nadrzędny, instrukcje, zasady, format wyniku, przykłady.
- Wynik bez dowodu nie jest wynikiem. Wymagamy testu, zapytania, pliku lub logu, a w handoffie - oczekiwanego wyniku weryfikacji.
- Handoff do innej osoby lub sesji: dokument ze statusem faz, rejestrem decyzji (kto zatwierdził), otwartymi pytaniami z założeniem tymczasowym i dziennikiem postępu.
- Bramka: przed rekomendacją agent sprawdza rejestr decyzji. Otwarta decyzja zatrzymuje rekomendację.
- Zakazane ścieżki (np. notatki, historia rozmów, dane źródłowe) są zapisane w `AGENTS.md` i w skillach. Agent ich nie czyta bez przekazania pliku przez użytkownika.

## 2. Koncepty i definicje (w kontekście pracy z AI)

| Pojęcie | Definicja w naszym użyciu |
| --- | --- |
| Agent | Model działający w pętli: planuje, wywołuje narzędzia, ocenia wynik i wykonuje kolejny krok |
| Subagent | Osobny agent z własnym kontekstem, wykonujący wydzieloną część zadania |
| Custom agent (chatmode) | Agent o określonej roli, zestawie narzędzi i instrukcji; w repo: `analityk`, `recenzent-notebookow`, `rozpoznanie-danych`, `walidator-metryk` |
| Narzędzie (tool) | Funkcja wywoływana przez model, np. pytanie do użytkownika, odczyt pliku, zapytanie do bazy, przeglądarka |
| Prompt | Jednorazowe polecenie dla modelu |
| Prompt file | Zapisany prompt z parametrami, do wielokrotnego użycia (`.github/prompts/`) |
| Instrukcja (`AGENTS.md`, `copilot-instructions.md`) | Zasady stale obowiązujące w projekcie, ładowane przy każdej rozmowie |
| Instrukcja warunkowa (`.instructions.md`) | Zasady ładowane tylko dla określonych typów plików (np. SQL, notebooki, bazy) |
| Skill (`SKILL.md`) | Procedura z krokami, decyzjami, bramkami i warunkami zatrzymania; zasoby ładowane na żądanie |
| Handoff | Przekazanie stanu pracy: plik ze statusem, decyzjami i otwartymi pytaniami; także przejście do wybranego agenta z promptem jednym kliknięciem |
| Human-in-the-loop | Model prowadzi i proponuje, człowiek zatwierdza każdy krok |
| Bramka | Miejsce w skillu, w którym agent zatrzymuje się i czeka na decyzję człowieka |
| Rejestr decyzji | Lista decyzji z datą, uzasadnieniem, zatwierdzającym i statusem; wpisy zamyka wyłącznie człowiek |
| Kontekst | Wszystko, co model widzi przy odpowiedzi: rozmowa, pliki, instrukcje, wyniki narzędzi |
| Okno kontekstu | Limit ilości tekstu, który model widzi naraz; duże pliki danych nie wchodzą do kontekstu |
| Sesja | Ciąg pracy w jednej rozmowie; nowa sesja nie zna poprzedniej historii |
| Harness | Lokalna konfiguracja otoczenia pracy agenta: instrukcje, agenci, skille, narzędzia |
| Test w nowej sesji | Uruchomienie procedury bez poprzedniej historii, żeby sprawdzić, czy instrukcja działa sama |
| Commit WIP | Zapis stanu pracy w trakcie zadania, z jawnie wymienionymi ścieżkami w `git add` |
| Halucynacja | Wygenerowana odpowiedź podana pewnym tonem, bez oparcia w źródle lub wyniku |
| Dowód wykonania | Wynik rzeczywiście uruchomionej operacji (test, zapytanie, log), nie deklaracja |

## 3. Wzorce pracy, które się sprawdziły

- **Krok po kroku z akceptacją:** agent wykonuje jeden krok, pokazuje wynik w skrócie, pyta o akceptację i dopiero potem przechodzi dalej (skill `analiza`).
- **Inicjalizacja z pytaniami:** brakującą konfigurację pyta jednorazowo, z propozycjami; zapis do `AGENTS.md` dopiero po zgodzie (skill `partner-import`).
- **Zakres przed liczeniem:** zanim agent policzy, dopytuje o wejścia, metrykę, zakres i format (skill `partner-import`).
- **Test jako dowód:** oczekiwany wynik testu zapisany w handoffie (np. liczba przechodzących testów), a nie samo "działa".
- **Otwarte pytania z założeniem tymczasowym:** każde pytanie ma przypisany właściwy kontakt i wartość robocza, żeby praca szła dalej, ale bez ukrywania niepewności.
- **Zamknięcie pytania w handoffie:** pytanie oznaczone jako zamknięte z uzasadnieniem, nie usuwane.
- **Oddzielenie wersji roboczej od produkcyjnej:** tymczasowe wartości i wersje kodu oznaczone w kodzie i w handoffie (np. wersja kodu z dopiskiem `wip`).
- **Commit po każdej turze:** WIP z jawnymi ścieżkami, bez plików konfiguracyjnych z hasłami.
- **Zasada "proces, nie wynik":** gdy wynik jest zły, poprawiamy instrukcję lub skill, a nie tylko wynik.
- **Dane syntetyczne oznaczone w wyniku:** jeśli plik jest oznaczony jako syntetyczny, wynik nosi tę etykietę.

## 4. Pułapki, na które trzeba uważać

- Model pewnie brzmi także wtedy, gdy się myli. Ton odpowiedzi nie jest miarą jakości.
- Dostępność nie jest prognozą popytu, a ilość nie jest zatwierdzonym zamówieniem. Agent tego nie miesza; człowiek też nie powinien.
- Wartości migawkowe (np. stan magazynowy) nie sumują się po tygodniach; wartości przepływu tak. Agent pyta, którego typu jest kolumna.
- Rozbieżność między wersją kodu a cache lub wynikiem referencyjnym trzeba nazwać i zapisać jako pytanie, nie ukrywać.
- Restart środowiska (kontenera) może przerwać trwające zadania; wymaga zgody.
- Ręczne testy użytkownika równolegle z pracą agenta: agent nie zmienia wspólnego kodu bez uprzedzenia.
- Zakazane ścieżki i duże pliki danych nie wchodzą do kontekstu; wynik liczy skrypt, nie model.
- Sekrety nie trafiają do plików, argumentów poleceń ani czatu.

## 5. Co warto powtórzyć

- Pełny przykład: skill `analiza` od wejścia do podsumowania, z pokazaniem pytań i akceptacji na każdym kroku.
- Ćwiczenie z handoffem: przejęcie pliku `HANDOFF.md` przez drugą osobę bez kontekstu rozmowy.
- Ćwiczenie z bramką: celowo otwarta decyzja w rejestrze i sprawdzenie, czy agent zatrzymuje rekomendację.
- Custom agent vs subagent: ten sam zakres zadania przez oba sposoby, z porównaniem narzędzi i kontekstu.
- Wersjonowanie instrukcji i skilli: przegląd `git diff` przed zatwierdzeniem zmiany.
- Handoff jednym kliknięciem do agenta z promptem: demo i ograniczenia.
- Koszt kontekstu: ile zajmują instrukcje i skille oraz kiedy je ładować warunkowo.
- Ocena skilla: liczba zatrzymań, liczba poprawek, zgodność wyniku z kontrolą.
- Co model wie, a czego nie wie w danym zadaniu (dostęp do danych, data graniczna wiedzy).
