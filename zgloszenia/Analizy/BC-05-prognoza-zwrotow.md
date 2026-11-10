# BC-05 — Zwroty: modele, rozmiary i zakupy o podwyższonym ryzyku: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Analiza i prognoza zwrotów na poziomie pozycji sprzedaży, modelu × rozmiaru × kanału oraz agregatu kwartalnego.
- Trzy różne decyzje biznesowe: poprawa oferty (tabele rozmiarów, opisy, dostawca), działania w momencie zakupu, planowanie kosztu zwrotów.
- Kluczowe zagadnienia: wskaźnik kohortowy zamiast słownikowego, cenzurowanie okna zwrotu, kanał sprzedaży jako zmienna zakłócająca, przeciek, ocena w obrębie kanału, kurczenie wskaźników małych komórek.
- Okres: 2025-01-01 do 2026-09-20; 36 modeli; pełna historia zwrotów (założenie).

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| „Które modele i rozmiary wracają częściej, niż byśmy się spodziewali?" | Wskaźnik zwrotów model × rozmiar × kanał z kurczeniem i przedziałami; nadwyżka ponad oczekiwanie z kanału, kategorii i rozmiaru |
| „Co, już w momencie zakupu, zwiększa ryzyko zwrotu?" | Model ryzyka na poziomie pozycji sprzedaży z cechami znanymi w chwili sprzedaży |
| „Ile będą nas kosztować zwroty w następnym kwartale?" | Oczekiwany koszt zwrotów (z przedziałem) = wskaźnik kohortowy × założone wolumeny × średnia wartość zwrotu |
| „Które zwroty sprawdzać w pierwszej kolejności?" (ok. 100 tygodniowo) | Wymaga innego celu niż ryzyko zwrotu: zwroty już dotarły; adekwatne byłoby np. ryzyko uszkodzenia wśród zwróconych (`DAMAGED`) |
| Online ok. 18%, sklepy ok. 4% | Kanał jako główny predyktor; ocena zawsze w obrębie kanału |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Kierownik obsługi zwrotów z e-commerce: online wraca ok. 18% sztuk, sklepy ok. 4%; pytania: które modele i rozmiary wracają częściej niż wynika z kanału, co w momencie zakupu zwiększa ryzyko zwrotu, ile zwroty będą kosztować w następnym kwartale; ok. 100 zwróconych pozycji tygodniowo można dokładnie sprawdzić: czy da się wskazać kolejność.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa; 5 sklepów i online; PLN; VAT 23%. Kategorie: Kurtki, Sukienki, Swetry, Jeansy, T-shirty, Koszule, Akcesoria.
- Powody zwrotu: `WRONG_SIZE`, `CHANGED_MIND`, `DAMAGED`, `OTHER`. Rozmiary skrajne (XS, XL) to typowe ryzyko nadmiaru.
- Brak w danych: ID klienta, informacji o zamówieniu poza pozycjami paragonu, dostaw, historii cennika, ruchu, pogody.

**Tabele** (`datasets/synthetic/bc05/`):
- `dim_date`, `dim_store`, `dim_product` (jak standardowo).
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.
- `fact_returns`: `ReturnKey`, `DateKey` (przyjęcie zwrotu), `ProductKey`, `StoreKey` (miejsce przyjęcia), `ReturnNo`, `TransactionNo`, `Quantity`, `ReturnAmount` (z VAT), `ReturnReason` (może być puste), `LoadId`.

**Ograniczenia dokumentowane.**
- Odstępstwo od standardowej hurtowni: pełna historia zwrotów od 2025-01-01 (standardowo tylko bieżący sezon); do zweryfikowania w audycie.
- Zwroty łączą się ze sprzedażą po `TransactionNo` i `ProductKey`; samo `TransactionNo` mnoży wiersze; data i sklep zwrotu to przyjęcie, nie sprzedaż.
- `UnitPrice` to cena przed rabatem; `ListPrice` i `UnitCost` bieżące.
- Relacje: `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = GrossAmount / 1,23`.

**Definicje.** Sztuki sprzedane i zwrócone; wskaźnik zwrotów (słownik: sztuki zwrócone / sprzedane w tym samym okresie i przekroju); wartość zwrotów netto = `SUM(ReturnAmount)/1,23`; sprzedaż netto; stopa rabatu; liczba transakcji; tydzień ISO. Do analizy ryzyka zakupu wskaźnik kohortowy (zwroty przypisane do daty i kanału sprzedaży przez `TransactionNo` + `ProductKey`): odstępstwo od słownika, pokazać różnicę.

**Produkty końcowe.** Notebook, raport 1 strona (tabela modeli × rozmiar × kanał z nadwyżką, czynniki ryzyka, koszt kwartalny, odpowiedź o kolejności kontroli), kod pomocniczy.

