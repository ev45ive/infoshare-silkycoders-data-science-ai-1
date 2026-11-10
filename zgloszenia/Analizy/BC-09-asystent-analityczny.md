# BC-09 — Asystent analityczny (agent z narzędziami): przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Prototyp asystenta, który odpowiada w języku naturalnym na pytania z danych (SQL tylko do odczytu), z procedur (dokumenty z cytowaniem) i z prognozy, a zadania zakłada wyłącznie jako szkic do zatwierdzenia przez człowieka.
- Porównanie czterech wariantów na tym samym złotym zbiorze pytań: pipeline regułowy bez modelu językowego, RAG bez narzędzi, agent z narzędziami, orkiestrator z sub-agentami.
- Kluczowe zagadnienia: definicje metryk w widokach vs słownik, kontrole techniczne zamiast promptu, sprzeczne i nieaktualne dokumenty, instrukcje ukryte w dokumentach i zadaniach, odmowy poza zakresem, prognoza dla modelu bez historii, dyscyplina dev/test, powtarzalność, koszt, walidacja sędziego AI względem człowieka.
- Dane: 14 modeli plus 1 nowy, 2025-01-01 do 2026-09-20; stany od 2026-08-01; 12 dokumentów procedur; 40 pytań (dev 24, test 16).

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| Kierownicy, analitycy i zakupy zadają te same pytania w centrali | Złoty zbiór pytań w 4 kategoriach: liczbowe, procedurowe, wieloetapowe, poza zakresem |
| Obawa: liczby wg złej definicji (brutto zamiast netto) | Weryfikacja widoków względem słownika metryk; słownik w kontekście i w testach; metryka poprawności liczb |
| Obawa: wymyślone procedury | Ugruntowanie (cytowanie dokumentu, wersja, data); odmowa „brak procedury" |
| Obawa: asystent zrobi to, czego nie powinien | Rola bazy tylko do odczytu; `propose_task` tylko jako szkic; zatwierdzenie poza zasięgiem modelu; testy bezpieczeństwa (cel: 0 zapisów bez zatwierdzenia) |
| „Czy bezpieczne i dobre na tyle, żeby uruchomić pilotaż, i na jakim poziomie samodzielności?" | Rekomendacja poziomu autonomii z progami ustalonymi przed wynikami i warunkami pilotażu |
| Twarde ograniczenie: tylko odczyt, zapis po zatwierdzeniu | Architektura: narzędzia z limitami (wiersze, czas, SELECT), audyt zapisów |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Dyrektor operacyjny: kierownicy sklepów, analitycy i zakupy zadają tym samym osobom w centrali te same pytania („ile sprzedaliśmy w Gdańsku w zeszłym tygodniu", „jak przyjąć zwrot bez paragonu", „którym sklepom wysłać dosyłkę kurtek"); pilotaż asystenta odpowiadającego z danych i procedur i zakładającego zadania dla człowieka; obawy: zła definicja metryki, wymyślone procedury, nieuprawnione działania; pytanie o bezpieczeństwo, jakość i poziom samodzielności. Ograniczenia: tylko odczyt danych; zapis tylko po zatwierdzeniu przez człowieka; wdrożenie jako usługa poza zakresem (prototyp: funkcja `answer(question)` i CLI).

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; 5 sklepów i online; PLN; VAT 23%. „Sprzedaż" bez doprecyzowania = sprzedaż netto przed zwrotami.
- Warstwy hurtowni: `dbo` (wymiary i fakty), `reporting` (widoki). Widoki powstawały pod różne pytania; nazwy nie zawsze odpowiadają temu, co liczą; ta sama metryka bywa opisana inaczej w dokumentacji i w widoku.
- Brak w danych: ID klienta, dostaw, historii cennika, ruchu, pogody.

**Zasoby** (`datasets/synthetic/bc09/`):
- Schemat `dbo` (identyfikatory zachowują wielkość liter, w PostgreSQL w cudzysłowach): `DimDate`, `DimStore`, `DimProduct`, `FactSales`, `FactReturns`, `FactInventoryDaily`.
- Schemat `reporting`: `vw_SalesDaily` (`Date`, `StoreCode`, `Channel`, `Units`, `Transactions`, `Revenue`, `DiscountAmount`, `CostAmount`), `vw_SalesWeekly` (`IsoYear`, `IsoWeek`, `YearWeek`, `WeekStart`, `WeekEnd`, `Channel`, `Region`, `Department`, `Category`, `Units`, `Transactions`, `GrossAmount`, `DiscountAmount`, `NetAmount`, `CostAmount`), `vw_StockAvailability` (`Date`, `StoreCode`, `SkuInFeed`, `SkuAvailable`, `SkuUnavailable`, `AvailabilityPct`), `vw_StoreScorecard` (`YearMonth`, `StoreCode`, `NetSales`, `CostOfGoods`, `ReturnsNet`, `GrossMargin`, `SalesAreaM2`, `NetSalesPerM2`).
- `slownik_metryk.md`: definicje firmy (sprzedaż brutto/netto, marża brutto = netto − COGS − zwroty netto z tego samego okresu, wskaźnik zwrotów, przychód na m², dostępność na SKU obecnych w feedzie, sell-through, tydzień ISO).
- `docs_procedury/` (12 dokumentów z nagłówkiem: tytuł, wersja, data obowiązywania, właściciel).
- `gold_set.jsonl`: `id`, `question`, `category`, `split`; dla `dev` także `reference_answer`.

**Środowisko.**
- PostgreSQL z pgvector (zmienne `PG*`) lub DuckDB tylko do odczytu + wyszukiwanie wektorowe w pamięci; rola asystenta wyłącznie `SELECT` na `dbo` i `reporting`.
- Model językowy: `OPENAI_API_KEY` lub `ANTHROPIC_API_KEY` (nazwa modelu z `*_MODEL` lub zapisana wybrana); twardy limit kosztu (tokeny na przebieg); tylko prawdziwe wywołania.
- Osadzenia: usługa dostawcy lub lokalny model; alternatywa leksykalna (BM25) z opisem konsekwencji.

**Metryki oceny.** Poprawność liczb (tolerancja), wybór narzędzia i zbędne wywołania, ugruntowanie (cytat potwierdzający), poprawność odmów i niepotrzebne odmowy, ujawnienie konfliktów, bezpieczeństwo (zapisy bez zatwierdzenia = 0; polecenia z treści dokumentów i zadań), koszt/opóźnienie/kroki, powtarzalność (dwa przebiegi).

**Produkty końcowe.** Notebook, `src/asystent/` (narzędzia, pętla agenta, prompty), `src/ocena/` (oceniacz, runner), `wyniki/` (surowe odpowiedzi, wywołania narzędzi, metryki, plik ślepej oceny 20 odpowiedzi), raport 1 strona (poziom autonomii, wyniki z przedziałami, ryzyka i kontrole, warunki pilotażu).

