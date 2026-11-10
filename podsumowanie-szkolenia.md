# Podsumowanie pracy: AI w analizie danych Nordvik (infoshare-silkycoders-data-science-ai-1)

Źródła: historia commitów (`commits.md`, 65 commitów, 2026-11-08 do 2026-11-10), pliki repo (`AGENTS.md`, `.github/`, `airflow/HANDOFF.md`, `imports/`, `analizy/`, `datasets/synthetic/*/README_dane.md`).

Pominięte zgodnie z zasadami repo: `notatki/`, `zgloszenia/`, `.specstory/`, `docs/ai-sessions/`. Slajdów nie czytano. Podsumowanie nie zawiera więc treści z notatek z rozmów - jeśli mają wejść do podsumowania, trzeba je wskazać wprost.

## 1. Przebieg pracy (wg commitów)

**2026-11-09: fundamenty pracy z AI**
- Firma Nordvik i przykładowe dokumenty (EX01).
- Dobry prompt: wąski kontekst, rola, cel nadrzędny, instrukcje, zasady, format wyniku, przykłady.
- Post-mortem rozmowy i zapis dobrych praktyk.
- Analiza E02: skąd bierze się liczba; pole "sprzedaż po korektach"; odpowiedź biznesowa dla kierownictwa.
- Format odpowiedzi: tabele, podpunkty, diagramy, mniej prozy, skanowalność; różne diagramy Mermaid.
- Zmiany w danych przed nowym sezonem (P01-O3).
- Human-in-the-loop: AI zna proces, prowadzi za rękę, zadaje pytania, podaje sugestie, rejestruje kontekst.
- Harness lokalny, `copilot-instructions.md`, `AGENTS.md`; prompt i instrukcja dla agentów.
- Integracja z partnerami (P01-04): profile importów, skill `partner-import`.
- Skill "walk the walk": wykonaj kroki, zweryfikuj, testuj, zmień, publikuj; zapis decyzji do pliku i kontrola wyników przed zatwierdzeniem.

**2026-11-10: praca z AI na projekcie BC-01 i narzędzia**
- Baza danych: psql, migracje, instrukcje dla bazy.
- Custom agents (chatmodes) vs subagenty; handoff jednym kliknięciem do wybranego agenta z promptem.
- Skill tworzenia skilli (`/create-skill`) i instrukcji (`/create-instructions`); dobre praktyki zapisane w skillu.
- Prognoza popytu BC-01: notebook, dane syntetyczne, analizy 1-9, cache, porównanie z CSV.
- BC-01 w Airflow: plan, handoff, fazy 0-5, testy (kontrakt "as of", B1, M1, M2, cechy, kalendarz), DAG, backfill jako krok do zatwierdzenia.
- Agent/Model as a Service: usługa analityczna (plan).
- Zgłoszenie dotyczące MLflow.

## 2. Co zostało pokazane i zrobione

**Procesy i skille**
- Skill `analiza`: 6 kroków (wejście, walidacja, hipotezy i eksploracja, analiza, weryfikacja, reprodukowalność) + podsumowanie. Każdy krok ładowany na żądanie, akceptacja użytkownika przed przejściem dalej, zapis do notebooka.
- Skill `partner-import`: inicjalizacja konfiguracji (pytania przez `vscode_askQuestions`, zgoda na zapis do `AGENTS.md`), dopasowanie profilu, walidacja i normalizacja, mapowanie SKU, zapytania biznesowe z przepisami i rejestrem decyzji.

**Agenci**
- `analityk`, `recenzent-notebookow`, `rozpoznanie-danych`, `walidator-metryk` (opisy w `.github/agents/`).

**Instrukcje**
- `copilot-instructions.md`, `AGENTS.md` (rola, zasady, pliki poza zakresem, konfiguracja importów), instrukcje warunkowe dla `sql`, `jupyter`, `database`.

**Projekt BC-01 (prognoza tygodniowa)**
- Migracja `V026` (schemat `forecast`), rola `airflow`, Compose, Dockerfile, `config/bc01.yaml`.
- Potok: dane "as of", kalendarz, panel, flagi braku towaru, cechy, M1 (ETS tłumiony), M2 (LightGBM), B1 (średnia 4 tygodni), zapis do `forecast.*`.
- Testy: kontrakt, zgodność z CSV referencyjnym, zgodność M1 z cache, brak wycieku z przyszłości.
- Wynik: DAG działa, 2 uruchomienia `ok` dla origin 2026-09-21 (120 wierszy, suma 39 638,4 szt.), 2 `failed` dla origin 2026-11-09 (brak danych po 2026-09-20).
- Otwarte: przedziały p10/p90 (obecnie p10 = p90 = prognoza), DAG monitoringu WAPE/bias, backfill, rozbieżność cache M2 dla cechy `disc` (przyczyna nieustalona), zatwierdzenie własnego obrazu Airflow.

**Dane i bazy**
- Zbiory syntetyczne BC01-BC09 z opisami (`README_dane.md`), słownik metryk, dokumenty procedur (D01-D12) dla BC09.
- Migracje V001-V026 i seedy dla RetailDW (PostgreSQL), skrypt `retaildw.sh`.

**Notebooki**
- BC-01 (prognoza), BC-03 (efekt rabatu), BC-04 (sell-through), BC-05 (zwroty), BC-09 (asystent analityczny), analiza churn w `docs/analytics/`.

## 3. Koncepty i problemy AI, które się pojawiły

- Human-in-the-loop: agent pyta przez `vscode_askQuestions`, nie zgaduje, czeka na akceptację po każdym kroku.
- Brak zgody = brak zapisu: zmiany w profilach, przepisach, `AGENTS.md` i instalacje pakietów tylko po zgodzie.
- Handoff (`airflow/HANDOFF.md`): dokument do przejęcia pracy bez kontekstu poprzedniej rozmowy; zawiera status faz, rejestr decyzji (kto zatwierdził), otwarte pytania z założeniami tymczasowymi, dziennik postępu, oczekiwane wyniki weryfikacji.
- Decyzje z oznaczeniem statusu: przyjęta / tymczasowa / do potwierdzenia / do zmiany - AI nie traktuje swoich założeń jako ustalonych.
- Bramki zatrzymania w skillach: przed rekomendacją sprawdzić rejestr decyzji; otwarta decyzja = zatrzymanie.
- Dostępność a popyt: w skillu partner-import zapisane zasady (dostępność nie jest prognozą, ilość nie jest zamówieniem, `AvailableUnits` to stan migawki, nie sumuje się po tygodniach).
- Dane syntetyczne: oznaczenie w wynikach ("dane syntetyczne") i zakaz czytania dużych plików do kontekstu; agent używa skryptów.
- Nie czytać zakazanych ścieżek: reguła w `AGENTS.md` i skillach.
- Testy jako dowód: wynik weryfikacji zapisany jako oczekiwany wynik (np. "25 passed"), nie jako deklaracja.
- Kontrola równoległej pracy: użytkownik testuje DAG ręcznie równolegle z agentem; agent nie zmienia kodu bez uprzedzenia.
- Ryzyko zmian w środowisku: restart kontenera tylko po zgodzie.
- Commit WIP po każdej turze z jawnymi ścieżkami `git add`; `.env` poza repo.
- Rozbieżność wyników (cache M2 z cechą `disc`, do 14%) zapisana jako otwarte pytanie, zamiast ukryta.

## 4. Co warto powtórzyć

- Pełny przykład od zlecenia do wyniku: jeden skill `analiza` przeprowadzony krok po kroku z pokazaniem pytań i akceptacji.
- Porównanie `analiza` (pętla z akceptacją) i `partner-import` (zasady i zatrzymania) - co zmienia struktura skilla.
- Ćwiczenie z handoffem: przejęcie `airflow/HANDOFF.md` przez drugą osobę bez kontekstu rozmowy.
- Ćwiczenie z celowo złą decyzją w rejestrze i pokazanie zatrzymania rekomendacji.
- Wersjonowanie skilli i instrukcji: `git diff` przed zatwierdzeniem zmiany w `copilot-instructions.md` lub `AGENTS.md`.
- Custom agents vs subagenty: pokazanie różnic na jednym zadaniu (kto ma narzędzia, kto ma kontekst).
- Handoff jednym kliknięciem do agenta z promptem (commit a9accfe) - demo i ograniczenia.
- Testy w tym samym repo: kontrakt "as of" i zgodność z CSV jako wzorzec dla każdej analizy AI.
- Kontrola kosztu kontekstu: ile zajmują `AGENTS.md`, instrukcje i skille; kiedy ładować warunkowo.
- Model/agent jako usługa (commit f8a10f4 - plan): co dokładnie zostanie wdrożone i jak to będzie kontrolowane.
- Monitoring prognozy: skrypt DAG monitoringu (WAPE, bias, alarm) jako praktyka utrzymania modelu po wdrożeniu.
- Zakończenie BC-01: decyzje otwarte (przedziały, progi alarmu, zapis wyników, zatwierdzenie obrazu) do rozstrzygnięcia przed uznaniem projektu za gotowy.
- Post-mortem jako stały element: zapis dobrych praktyk po każdej sesji (w repo istnieje jako commit; treść do przeniesienia tylko po wskazaniu pliku).
