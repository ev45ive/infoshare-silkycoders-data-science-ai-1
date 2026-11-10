# BC-08 — Wpływ przebudowy sklepu Kraków Rynek: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Ocena, czy przebudowa i powiększenie sklepu Kraków Rynek (180 → 320 m², otwarcie 2026-04-01) zwiększyły sprzedaż netto ponad zwykłą zmienność.
- Metody quasi-eksperymentalne dla jednego sklepu poddanego zmianie: przed/po, różnica różnic z event study, kontrola syntetyczna, bayesowski model strukturalny szeregu (w stylu CausalImpact).
- Kluczowe zagadnienia: estymand i kontrfakt, okno przejściowe, jakość sklepów kontrolnych, placebo w czasie i w przestrzeni, moc i minimalny wykrywalny efekt, efekt nowości vs ustalony, przychód na m² w dwóch ujęciach.
- Okres: 2025-01-01 do 2026-09-20 (ok. 24 tygodnie po otwarciu); 14 modeli; zwrotów brak.

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| „Czy przebudowa dała efekt większy niż zwykła zmienność?" | Efekt w % i PLN tygodniowo z przedziałem; porównanie z rozkładem placebo |
| „Cała firma też rośnie, w innych sklepach działo się różnie" | Grupa kontrolna i test jej jakości w okresie przed |
| „Czy planować podobne przebudowy w Poznaniu i Gdańsku?" | Rachunek warunkowy: jaki przyrost marży rocznie uzasadnia inwestycję o danym koszcie i czynszu; co z Krakowa przenosi się, a co nie |
| Powierzchnia 180 → 320 m² | Przychód na m² w ujęciu słownikowym i z faktyczną powierzchnią |
| Przebieg prac w marcu nieznany | Okno przejściowe wyłączone z estymacji, wrażliwość na jego długość |
| Posiedzenie zarządu za 2 tygodnie | Wniosek z jawnym zakresem niepewności i listą brakujących danych |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Dyrektor sprzedaży i rozwoju sieci: Kraków Rynek przebudowany i powiększony ze 180 do 320 m², otwarcie po przebudowie 2026-04-01; pytanie, czy to dało efekt i czy większy niż zwykła zmienność; zarząd rozważa podobne przebudowy Poznania i Gdańska; sprzedaż w Krakowie wzrosła, firma też rośnie, w innych sklepach przez 20 miesięcy działo się różnie (brak rejestru zdarzeń: remonty, konkurencja); posiedzenie zarządu za 2 tygodnie.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; 5 sklepów i online; PLN; VAT 23%.
- Sklepy: Warszawa Arkadia (`S-WAW-01`, 420 m²), Warszawa Mokotów (`S-WAW-02`, 260 m²), Kraków Rynek (`S-KRK-01`, 180 m² do marca 2026, 320 m² od 2026-04-01), Poznań (`S-POZ-01`, 300 m²), Gdańsk (`S-GDA-01`, 240 m²), online (`S-ONL-01`).
- Szczyty: Black Friday i grudzień; luty najsłabszy. Akcje obejmują całą sieć.
- Brak w danych: historii metrażu, danych o konkurencji, rejestru zdarzeń w sklepach, ruchu, pogody, kalendarza marketingu.

**Tabele** (`datasets/synthetic/bc08/`):
- `dim_date`, `dim_product` (14 modeli), `dim_store` (z `SalesAreaM2` bieżącym i `RemodelDate`).
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.

**Ograniczenia dokumentowane.**
- Brak zwrotów w zbiorze: marża liczona jako netto − COGS to marża przed zwrotami (odstępstwo od słownika, jawnie).
- `SalesAreaM2` to bieżąca powierzchnia; historia metrażu poza hurtownią (z dokumentacji firmy: 180 m² do marca 2026, 320 m² od 2026-04-01).
- Relacje: `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = GrossAmount / 1,23`.

**Definicje.** Sprzedaż netto; sztuki; COGS; liczba transakcji; przychód na m² (słownik: sprzedaż netto / bieżąca powierzchnia, obie strony dzielone przez dzisiejszą powierzchnię; tylko sklepy stacjonarne); tydzień ISO. Dzielenie obu okresów przez tę samą stałą nie zmienia względnej zmiany sprzedaży: wariant z faktyczną powierzchnią w danym okresie (180/320 m², informacja spoza hurtowni) pokazać dodatkowo.

**Produkty końcowe.** Notebook, raport 1 strona (efekt z przedziałem, profil w czasie, przychód na m² w dwóch ujęciach, wniosek warunkowy dla Poznania i Gdańska, brakujące dane), kod pomocniczy.

