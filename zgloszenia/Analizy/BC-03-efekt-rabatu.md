# BC-03 — Efekt rabatu: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Ocena, czy rabaty Nordvik się opłacają: efekt rabatu na sprzedaż (elastyczność cenowa), przesunięcie popytu po akcji, wpływ na marżę po zwrotach.
- Dane obserwacyjne bez losowania: rabaty nakładają się na sezon, Black Friday i wydarzenia zewnętrzne; modele do wyprzedaży są wybierane na podstawie słabej sprzedaży.
- Metody: naiwne porównanie, regresja Poissona z efektami stałymi (PPML), różnica różnic i event study, model gradientowy jako kontrast (predykcja, nie efekt).
- Okres danych: 2025-01-01 do 2026-09-20; 36 modeli; zwroty dostępne za cały okres.

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| „Czy dodatkowa sprzedaż pokrywa utraconą marżę?" | Próg opłacalności wzrostu sprzedaży (break-even uplift) vs oszacowany wzrost netto; marża po zwrotach |
| „Czy kategorie reagują tak samo? (jeansy mocniej niż kurtki)" | Elastyczność per kategoria i kanał, test różnic (interakcje) |
| „Czy to tylko przesunięcie zakupów?" | Okno po akcji (przesunięcie popytu): efekt „akcja + 14 dni" vs sam okres akcji |
| Brak kalendarza akcji z 20 miesięcy | Odtworzenie epizodów rabatowych z `DiscountAmount` |
| Decyzja: kalendarz akcji AW26 (kategorie, głębokość, czy w ogóle) | Rekomendacja w zakresie obserwowanych rabatów + propozycja eksperymentu |
| Nikt nie losował, kto dostaje rabat | Kontrfakt, grupy kontrolne, selekcja do wyprzedaży, placebo |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Dyrektor ds. cen i promocji: Black Friday −20%, w ciągu roku akcje na wybrane kategorie, wyprzedaże końca sezonu; sprzedaż rośnie w tygodniach z rabatem, ale nie wiadomo ile daje rabat, a ile okres; brak spisanego kalendarza akcji z 20 miesięcy; pytania: czy dodatkowa sprzedaż pokrywa utraconą marżę, czy kategorie reagują tak samo, czy to przesunięcie zakupów; decyzja: kalendarz akcji AW26 (listopad 2026 – styczeń 2027), termin 2 tygodnie.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; 5 sklepów i online; PLN; VAT 23%. Kategorie: Kurtki, Sukienki, Swetry, Jeansy, T-shirty, Koszule, Akcesoria.
- Cykl ceny: pełna cena, po ok. 8 tygodniach rabat −20…−30%, potem wyprzedaż −40…−60%. Black Friday i grudzień to szczyt.
- Zwroty (orientacyjnie): ok. 4% sztuk w sklepach, ok. 18% online; kanały osobno.
- Brak w danych: ID klienta, dostaw, historii cennika, ruchu, pogody, konkurencji, kalendarza marketingu.

**Tabele** (`datasets/synthetic/bc03/`):
- `dim_date`, `dim_store`, `dim_product` (jak standardowo; `ListPrice` brutto bieżąca, `UnitCost`).
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.
- `fact_returns`: `ReturnKey`, `DateKey` (przyjęcie), `ProductKey`, `StoreKey` (miejsce przyjęcia), `ReturnNo`, `TransactionNo`, `Quantity`, `ReturnAmount` (z VAT), `ReturnReason` (`DAMAGED`, `WRONG_SIZE`, `CHANGED_MIND`, `OTHER`, puste), `LoadId`.

**Ograniczenia dokumentowane.**
- Zwroty dostępne za cały okres (odstępstwo od standardowej hurtowni, gdzie jest tylko bieżący sezon).
- Zwroty łączą się ze sprzedażą po `TransactionNo` i `ProductKey`; data i sklep zwrotu = przyjęcie.
- `UnitPrice` to cena przed rabatem; brak historii cennika.
- Relacje: `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = GrossAmount / 1,23`.

**Definicje.** Sztuki; sprzedaż brutto i netto; stopa rabatu = `SUM(DiscountAmount)/SUM(Quantity × UnitPrice)`; COGS; wartość zwrotów netto = `SUM(ReturnAmount)/1,23`; marża brutto (słownik) = netto − COGS − zwroty netto przyjęte w tym samym okresie; wskaźnik zwrotów; tydzień ISO. Do oceny akcji marża kohortowa (zwroty przypisane do daty sprzedaży przez `TransactionNo` + `ProductKey`) jest jawnym odstępstwem od słownika; pokazać oba wyniki.

**Produkty końcowe.** Notebook, raport 1 strona (tabela per kategoria: elastyczność, próg opłacalności, wzrost netto po przesunięciu, wpływ na marżę, werdykt), propozycja eksperymentu.
