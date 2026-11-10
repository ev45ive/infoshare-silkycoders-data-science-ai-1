# Ćwiczenie BC-09: asystent analityczny jako usługa (LangGraph, FastAPI, Streamlit, MCP)

## 1. Do czego służy to rozszerzenie względem samej analizy

- Analiza (notebook i prototyp) odpowiada na pytania: czy asystent z narzędziami (zapytania SQL tylko do odczytu, wyszukiwanie w procedurach, prognoza, szkic zadania) jest wystarczająco dobry i bezpieczny, jakie ma ryzyka i kontrole, jaki poziom samodzielności jest dopuszczalny. Prototyp obsługuje **jedną osobę przy terminalu**.
- Rozszerzenie zamienia zamrożony prototyp w **usługę dla wielu użytkowników**:
  - logowanie i role (wnioskodawca, zatwierdzający),
  - trwałe rozmowy i zatwierdzanie zadań w czasie (także po restarcie),
  - interfejs REST z dokumentacją, aplikacja czatu, serwer MCP dla zewnętrznych klientów,
  - ślad audytowy i kontrola kosztu.
- **Nie poprawia jakości odpowiedzi.** Pokazuje, że usługa zachowuje się jak zamrożony prototyp i że nowe ryzyka są kontrolowane technicznie.
- Nowe pytania, na które analiza nie odpowiada:
  - jak wznowić rozmowę wstrzymaną na zatwierdzenie po godzinie lub po restarcie usługi i wykonać dokładnie jedno działanie,
  - jak uniemożliwić czyjąś rozmowę lub zatwierdzenie własnego zadania,
  - jak sprawić, żeby żaden interfejs (REST, czat, MCP) nie dał modelowi drogi do zatwierdzenia,
  - czy usługa utrzymuje jakość prototypu,
  - jak zapewnić powtarzalność i nie zepsuć zbioru testowego.
- Narzędzia: LangGraph (graf z trwałym stanem i wstrzymaniem), FastAPI z Pydantic (REST i Swagger), Streamlit (czat), oficjalny SDK serwera MCP, PostgreSQL.

## 2. Potrzeba biznesowa i jej przełożenie

- **Zlecenie (dyrektor operacyjny):** kierownicy sklepów, analitycy i dział zakupów zadają tym samym osobom w centrali te same pytania. Pilotażowy asystent ma odpowiadać na podstawie danych i procedur i w razie potrzeby zakładać zadanie dla człowieka. Obawy: zła definicja metryki, wymyślone procedury, działanie, którego asystent nie powinien wykonać.
- **Twarde ograniczenia:** dostęp do danych tylko do odczytu; zadanie zakłada się dopiero po zatwierdzeniu przez człowieka; asystent może przygotować szkic, ale go nie zatwierdza.

| Potrzeba biznesowa | Wymaganie techniczne |
| --- | --- |
| Pilotaż dla wielu osób | Logowanie, role, izolacja rozmów (autoryzacja na poziomie obiektu) |
| Zatwierdza uprawniony człowiek, inny niż wnioskodawca | Rola „zatwierdzający", reguła czterech oczu, zatwierdzanie wyłącznie przez kod usługi |
| Zatwierdzenie po czasie | Trwały stan (punkty kontrolne w bazie), wstrzymanie i wznowienie po restarcie, idempotentne działania |
| Dostęp z różnych narzędzi | REST, czat i serwer MCP nad tym samym rdzeniem i tymi samymi zabezpieczeniami |
| Zaufanie do wyników | Regresja na zbiorze deweloperskim względem zamrożonego prototypu |
| Odpowiedzialność | Dziennik audytu: kto zapytał, co zrobiły narzędzia, kto zatwierdził |
| Kontrola kosztu i nadużyć | Limity kroków, wejścia i kosztu dziennego na użytkownika |

## 3. Co musi mieć uczeń (komplet)

**Wyniki analizy BC-09** (`analizy/bc09-asystent-analityczny/`):
- notebook: model zagrożeń i kontrole, audyt widoków względem słownika metryk, audyt dokumentów procedur, złoty zbiór i oceniacz, hipotezy, warianty W1–W4 z wynikami na zbiorze deweloperskim, testy bezpieczeństwa, dziennik pracy;
- `src/asystent/` (narzędzia, pętla agenta, prompty), `src/ocena/` (oceniacz, runner), `wyniki/` (surowe odpowiedzi, wywołania narzędzi, metryki kosztu, plik ślepej oceny);
- `raport-biznesowy.md`: rekomendowany poziom autonomii, wyniki z przedziałami, ryzyka i kontrole, warunki pilotażu.
- stan: czy był dostęp do modelu językowego, czy zbiór testowy oceniono, jaki wariant jest zamrożony.

**Zasoby asystenta** (`datasets/synthetic/bc09/`):
- tabele i widoki w Parquet: schemat `dbo` (`DimDate`, `DimStore`, `DimProduct`, `FactSales`, `FactReturns`, `FactInventoryDaily`) i `reporting` (`vw_SalesDaily`, `vw_SalesWeekly`, `vw_StockAvailability`, `vw_StoreScorecard`), nazwy z zachowaną wielkością liter;
- `slownik_metryk.md` (obowiązujące definicje), `docs_procedury/` (wersje, daty, sprzeczności, treści z poleceniami dla modelu), `gold_set.jsonl` (pytania `dev` z odpowiedziami wzorcowymi, `test` bez nich).
- narzędzia zamrożone: `run_sql`, `search_docs`, `forecast`, `propose_task`; limity kroków, tokenów, wierszy i czasu z prototypu.

**Środowisko (repozytorium):**
- `databases/RetailDW-postgres/`: kontener `retaildw-postgres-1`, port 5433, role `retaildw`, `retaildw_ro`; hurtownia w snake_case (schematy `dw`, `reporting`) z własnym seedem.
- Baza danych asystenta: `retaildw_bc09` (dane przypadku z zachowaniem nazw), jeśli istnieje; baza stanu usługi: osobna (np. `retaildw_bc09_state`).
- Python 3.11 lub nowszy (wymóg SDK MCP), model językowy ze zmiennych środowiskowych (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`).

**Dokumentacja:**
- LangGraph, wstrzymanie i wznowienie: https://docs.langchain.com/oss/python/langgraph/interrupts
- LangGraph, trwałość (punkty kontrolne, `thread_id`): https://docs.langchain.com/oss/python/langgraph/persistence
- SDK MCP (Python): https://github.com/modelcontextprotocol/python-sdk i https://py.sdk.modelcontextprotocol.io/
- Konfiguracja serwerów MCP w VS Code: https://code.visualstudio.com/docs/copilot/customization/mcp-servers

**Wiedza wstępna:** Python, REST i OAuth2/tokeny na poziomie podstaw, SQL, agent z narzędziami i podstawy LLM, podstawy bezpieczeństwa aplikacji (autoryzacja, wstrzykiwanie poleceń).

## 4. Kroki

### Krok 1. Odczyt wejść i zamrożenie rdzenia

- **Co przekazać / wskazać:**
  - notebook, raport, `src`, `wyniki` poprzedniej analizy;
  - liczby referencyjne: metryki na zbiorze deweloperskim zamrożonego wariantu (z przedziałami), koszt i opóźnienie na pytanie, wyniki testów bezpieczeństwa.
- **Pytania naprowadzające:**
  - Który wariant jest zamrożony i z jakimi narzędziami, promptami i limitami?
  - Jaki poziom autonomii rekomenduje raport i jakie warunki pilotażu?
  - Czy model językowy był dostępny? Czy zbiór testowy oceniono?
  - Co zostaje bez zmian, a co dokładamy?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - jeśli wcześniej brakowało dostępu do modelu, wyniki wariantów 2–4 są „niewykonane": usługa może działać na wariancie 1 (reguły), co wystarcza do pokazania całej infrastruktury;
  - rdzeniu nie wolno stroić po stronie wdrożenia (prompty, narzędzia, limity).
- **Rezultat:**
  - opis zamrożonego rdzenia;
  - liczby referencyjne;
  - tabela „bez zmian (rdzeń)" i „dokładamy (usługa)".

### Krok 2. Brama środowiska

- **Co przekazać / wskazać:**
  - SDK MCP wymaga Pythona 3.11+;
  - dwie bazy: danych asystenta (tylko do odczytu) i stanu usługi (zapis własną rolą);
  - kontener `retaildw-postgres-1`: `./retaildw.sh status`.
- **Pytania naprowadzające:**
  - Jaka jest wersja Pythona i które biblioteki (LangGraph i pakiet punktów kontrolnych, FastAPI, Pydantic, Streamlit, SDK MCP, sterownik PostgreSQL) przypinamy?
  - Czy rola tylko do odczytu naprawdę nie zapisze, a rola usługi zapisuje tylko w schemacie stanu?
  - Czy mały graf z wstrzymaniem przeżywa restart procesu? Czy mały serwer MCP odpowiada?
  - Co robimy bez modelu językowego, bez PostgreSQL, z problemem biblioteki?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - interfejsy frameworków agentowych i MCP szybko się zmieniają, poradniki bywają niezgodne z zainstalowaną wersją (np. starsza klasa serwera w SDK);
  - plik punktów kontrolnych zamiast bazy jest rozwiązaniem niedocelowym i musi być tak oznaczony;
  - utworzenie bazy stanu to zmiana środowiska: jawne polecenie, skrypt usunięcia.
- **Rezultat:**
  - środowisko z przypiętymi wersjami;
  - testy podstaw: role, graf z wstrzymaniem, serwer MCP, API;
  - albo opis blokad i użytego planu awaryjnego.

### Krok 3. Notatka projektowa i decyzja architektoniczna

- **Co przekazać / wskazać:**
  - zasady: UI i MCP nie mają bezpośredniego dostępu do bazy ani do modelu, wołają API;
  - właściwości punktów kontrolnych i wstrzymania w LangGraph (stan zapisany, wznowienie tym samym `thread_id`, węzeł po wznowieniu startuje od początku).
- **Pytania naprowadzające:**
  - Czego musiałaby dopisać własna pętla, żeby wstrzymać wykonanie na dowolnie długo i wznowić po restarcie przez innego użytkownika, trwale utrzymać wątek i strumieniować zdarzenia? Czy to uzasadnia framework i jaki jest jego koszt?
  - Jakie role i uprawnienia? Co oznacza autoryzacja na poziomie obiektu dla wątku, zadania i zatwierdzenia?
  - Jak wygląda model danych stanu i automat stanów zadania (szkic, oczekuje, zatwierdzone, odrzucone)?
  - Kto faktycznie zatwierdza i jak model jest od tego odcięty?
  - Jakie nowe zagrożenia pojawiają się przy usłudze wielodostępnej? Jaka kontrola i jaki test dla każdego?
  - Czego nie budujemy?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - identyfikator rozmowy łatwy do zgadnięcia bez sprawdzania własności to dziura (używać UUID i sprawdzać własność przy każdym odwołaniu);
  - efekty uboczne przed wstrzymaniem w tym samym węźle wykonają się ponownie po wznowieniu (osobny, idempotentny węzeł);
  - treść zadania wyświetlana osobie zatwierdzającej to wektor ataku;
  - serwer MCP nie może zawierać narzędzia zatwierdzającego.
- **Rezultat:**
  - notatka i `ADR.md`: warstwy, uzasadnienie frameworku z kosztem, macierz uprawnień, model danych, przepływ zatwierdzania, lista punktów REST i narzędzi MCP, uwierzytelnianie, rozszerzony model zagrożeń, lista „czego nie robimy".

### Krok 4. Wyodrębnienie rdzenia i parytet

- **Co przekazać / wskazać:**
  - liczby referencyjne z kroku 1 i oceniacz z poprzedniej analizy;
  - rdzeń ma być funkcją z wstrzykniętymi zależnościami i bez stanu globalnego.
- **Pytania naprowadzające:**
  - Czy rdzeń wywołany jako funkcja daje te same metryki i ten sam ślad narzędzi na zbiorze deweloperskim?
  - Skąd biorą się ewentualne różnice i czy mieszczą się w niedeterminizmie modelu?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - stan globalny prototypu (połączenia, zmienne) nie przeżyje wielu użytkowników naraz;
  - porównanie tekstu odpowiedzi modelu jest niewiarygodne, porównuje się metryki z przedziałami.
- **Rezultat:**
  - rdzeń bez stanu globalnego;
  - zestawienie rdzeń vs liczby referencyjne.

### Krok 5. Graf z trwałym stanem i zatwierdzaniem

- **Co przekazać / wskazać:**
  - wstrzymanie (`interrupt`), wznowienie (`Command(resume=...)`), punkty kontrolne w bazie stanu;
  - zasady: osobny węzeł tworzący szkic i osobny węzeł wstrzymania; nie opakowywać wstrzymania w `try/except`; wartości serializowalne.
- **Pytania naprowadzające:**
  - Co się stanie, gdy zatrzymamy proces w trakcie oczekiwania na zatwierdzenie i uruchomimy go ponownie?
  - Jak sprawić, żeby po wznowieniu powstało dokładnie jedno zadanie?
  - Co może zmienić zatwierdzający (poprawa pól szkicu) i jak to zapisać w audycie?
  - Czy model ma jakąkolwiek drogę do zatwierdzenia? Jak to udowodnić?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - zdublowane szkice po wznowieniu to objaw efektów ubocznych przed wstrzymaniem;
  - zatwierdzenie wykonuje kod usługi po decyzji uprawnionego człowieka, nie narzędzie dostępne dla modelu;
  - przy pięciu równoległych użytkownikach stan jednej rozmowy nie może przeniknąć do drugiej.
- **Rezultat:**
  - graf z węzłami: pytanie (pętla narzędzi z limitem), szkic zadania, wstrzymanie, wykonanie decyzji, odpowiedź;
  - testy: wstrzymanie → zatrzymanie procesu → wznowienie bez duplikatów, odrzucenie, zatwierdzenie z poprawką, błędny `thread_id`, treść nakłaniająca model do zatwierdzenia;
  - parytet metryk na zbiorze deweloperskim: graf vs rdzeń.

### Krok 6. API (FastAPI, Pydantic, Swagger)

- **Co przekazać / wskazać:**
  - schematy Pydantic jako kontrakt (długości, typy, brak pól dodatkowych);
  - interaktywna dokumentacja generowana z kodu, z opisem schematu uwierzytelniania.
- **Pytania naprowadzające:**
  - Jakie punkty końcowe i kto ma do nich dostęp? Jak działa uwierzytelnianie i termin ważności tokenu?
  - Czy wnioskodawca może odczytać cudzy wątek, zatwierdzić własne zadanie, wysłać zbyt długie pytanie, zużyć nieograniczony koszt?
  - Co widzi klient po błędzie serwera? Co trafia do logów, a co nie?
  - Czy strumieniowanie zdarzeń poprawia odczuwalne opóźnienie na tyle, żeby je zostawić?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - sprawdzenie uprawnień tylko w interfejsie lub w prompcie jest niewystarczające, kontrola jest w API i w bazie;
  - zapytania do bazy danych asystenta idą osobnym połączeniem, rolą tylko do odczytu;
  - szczegóły wewnętrzne i sekrety nie mogą wyciekać w komunikatach błędów;
  - asynchroniczna aplikacja z synchronicznym wywołaniem grafu blokuje pętlę zdarzeń.
- **Rezultat:**
  - działające API z dokumentacją interaktywną;
  - role, własność obiektów, limity (wejście, czas, koszt dzienny), identyfikator żądania w logach bez sekretów.

### Krok 7. Interfejs czatu (Streamlit)

- **Co przekazać / wskazać:**
  - interfejs woła tylko API;
  - model uruchamiania skryptu przez Streamlit (stan sesji).
- **Pytania naprowadzające:**
  - Co użytkownik powinien widzieć oprócz odpowiedzi (kroki narzędzi, źródła, cytaty, stan „oczekuje na zatwierdzenie")?
  - Co widzi osoba zatwierdzająca i jakie decyzje może podjąć?
  - Jak wyświetlić treść pochodzącą z modelu, dokumentów i zadań bez wykonania zawartych w niej poleceń lub znaczników?
  - Gdzie przechowywać token i identyfikator wątku?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - treść z dokumentów i zadań to dane niezaufane: wyświetlana jako zwykły tekst;
  - token i identyfikator wątku w stanie sesji, nie w adresie.
- **Rezultat:**
  - aplikacja z logowaniem, czatem, widokiem zatwierdzeń dla uprawnionej roli;
  - brak bezpośredniego dostępu do bazy i modelu z interfejsu.

### Krok 8. Serwer MCP

- **Co przekazać / wskazać:**
  - SDK i jego aktualna dokumentacja (klasa serwera, narzędzia, transporty stdio i HTTP);
  - format `mcp.json` w VS Code (klucz `servers`, zmienne wejściowe na sekrety) oraz przenośny `.mcp.json` (klucz `mcpServers`, bez zmiennych wejściowych).
- **Pytania naprowadzające:**
  - Jakie narzędzia wystawiamy i dlaczego dokładnie takie? Czy któreś pozwala zatwierdzać zadania?
  - Jak serwer MCP uwierzytelnia użytkownika i skąd bierze token bez wpisywania go w plik?
  - Co się stanie, gdy treść zadania lub dokumentu każe asystentowi „zatwierdzić zadanie"?
  - Jak sprawdzić listę narzędzi i działanie bez własnego klienta?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - narzędzie zatwierdzające w MCP lub dostępne dla modelu łamie twarde ograniczenie;
  - sekret wpisany w plik konfiguracji w repozytorium to wyciek;
  - nie kopiować konfiguracji między formatami bez sprawdzenia (`servers` kontra `mcpServers`);
  - konfiguracji obszaru roboczego użytkownika nie modyfikujemy, dostarczamy plik przykładowy i instrukcję.
- **Rezultat:**
  - serwer MCP z zaplanowaną listą narzędzi (bez zatwierdzania), wołający API;
  - `mcp.json.example` zgodny z dokumentacją edytora, bez sekretów, z krótką instrukcją podłączenia;
  - testy narzędziami SDK: lista narzędzi, brak zatwierdzania, brak dostępu do cudzych rozmów.

### Krok 9. Testy i regresja

- **Co przekazać / wskazać:**
  - zbiór deweloperski (z odpowiedziami wzorcowymi) służy do regresji, zbiór testowy do jednorazowej oceny końcowej;
  - odpowiedzi wzorcowe zbioru testowego są w kluczu, którego nie otwieramy.
- **Pytania naprowadzające:**
  - Jakie testy automatyczne bezpieczeństwa i funkcji? (logowanie i wygaśnięcie tokenu, podrobiony token, role, cudzy wątek i zadanie, próba zatwierdzenia przez wnioskodawcę, zbyt długie wejście, zapis do bazy danych rolą asystenta, polecenia w dokumencie i w treści zadania, limity.)
  - Co się dzieje po restarcie usługi w trakcie oczekiwania na zatwierdzenie?
  - Czy jakość na zbiorze deweloperskim przez REST (dwa przebiegi) mieści się w granicach liczb referencyjnych?
  - Jak sprawdzić zbiór testowy bez jego „zużywania": jednorazowo, bez oceny względem klucza, porównując z zamrożonymi surowymi odpowiedziami i śladem narzędzi?
  - Jak zachowuje się usługa przy kilku użytkownikach równocześnie?
  - Jaki jest koszt i opóźnienie przez usługę względem rdzenia?
  - Czy narzędzie SQL można skierować na hurtownię (rola tylko do odczytu, opis schematu w snake_case) bez zmiany kodu? Czemu nie oceniamy tego złotym zbiorem?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - wielokrotne uruchamianie zbioru testowego obniża jego wartość jako niezależnej oceny;
  - różnice o 1–2 pytania przy kilkunastu pytaniach testowych to szum;
  - hurtownia ma inne dane niż przypadek, więc uruchomienie na niej to test przenośności, nie jakości;
  - opis schematu i słownik metryk to konfiguracja, nie kod narzędzia.
- **Rezultat:**
  - raport z testów: bezpieczeństwo i funkcje (przeszło/nie), trwałość po restarcie, współbieżność, regresja jakości z przedziałami, koszt i opóźnienie;
  - wynik przenośności narzędzia SQL na hurtownię (odmowa zapisu, sens zapytań, bez oceny jakości).

### Krok 10. Utrzymanie i operacje

- **Co przekazać / wskazać:**
  - rosnące punkty kontrolne, nieobsłużone zatwierdzenia, rotacja tokenów;
  - granice środowiska szkoleniowego.
- **Pytania naprowadzające:**
  - Jak odtworzyć „kto zatwierdził co" z audytu?
  - Jak wygaszać nieobsłużone zatwierdzenia i czyścić punkty kontrolne?
  - Co robi operator przy próbie wstrzyknięcia poleceń, przekroczeniu kosztu, awarii modelu językowego?
  - Czego brakuje do produkcji (TLS, logowanie jednokrotne, skalowanie, kopie zapasowe)?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - punkty kontrolne rosną bez ograniczeń;
  - zatwierdzenie bez terminu ważności może zostać użyte po miesiącach, w zmienionym kontekście.
- **Rezultat:**
  - runbook pilotażu: użytkownicy, utknięte zatwierdzenia, wstrzyknięcia poleceń, limity kosztu, awarie;
  - lista różnic względem produkcji.

### Krok 11. Raport wdrożenia

- **Co przekazać / wskazać:**
  - wyniki kroków 4–9.
- **Pytania naprowadzające:**
  - Czy pilotaż może ruszyć, dla kogo i na jakich warunkach?
  - Co usługa gwarantuje (brak zapisów bez zatwierdzenia przez uprawnioną, inną osobę; ślad audytowy; izolacja rozmów), a czego nie gwarantuje (jakość odpowiedzi to wynik poprzedniej analizy)?
  - Jakie ryzyka pozostają otwarte?
- **Problem / ograniczenie do wskazania, jeśli umknie:**
  - raport nie obiecuje jakości ponad wynik analizy ani bezpieczeństwa ponad przetestowane kontrole.
- **Rezultat:**
  - raport (maks. 1 strona): decyzja i warunki pilotażu, gwarancje usługi i ich dowody, granice, otwarte ryzyka i pytania (kto jest zatwierdzającym, czas ważności zatwierdzenia, limity kosztu).

## 5. Rezultat końcowy całości

- Usługa uruchamiana lokalnie: REST z dokumentacją interaktywną, czat z widokiem zatwierdzeń, serwer MCP bez zatwierdzania, trwały stan w bazie.
- Dowody: parytet rdzenia, grafu i REST na zbiorze deweloperskim, zero zapisów bez zatwierdzenia, izolacja rozmów dwóch użytkowników, wznowienie po restarcie bez duplikatów, brak wykonywania poleceń z treści dokumentów i zadań.
- Rdzeń asystenta bez zmian względem prototypu, zbiór testowy nieużyty do strojenia.
- `ADR.md`, runbook pilotażu i raport z warunkami uruchomienia i uczciwym opisem granic.
