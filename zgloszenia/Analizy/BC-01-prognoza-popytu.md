# BC-01 — Prognoza popytu tygodniowego: przebieg analizy krok po kroku

## 1. Czego dotyczy analiza

- Prognoza sprzedanych sztuk na poziomie `StyleCode × lokalizacja` (5 sklepów i online) na 4 tygodnie do przodu.
- Punkt prognozy (origin): poniedziałek 2026-09-21. Ostatni dzień danych: niedziela 2026-09-20. Prognozowane tygodnie: 2026-W39 (21–27 IX), W40, W41, W42 (12–18 X).
- Porównanie dzisiejszej praktyki (średnia z 4 tygodni) z baseline'em sezonowym, modelem szeregów czasowych i globalnym modelem gradientowym.
- Walidacja rolling-origin, błąd WAPE i obciążenie, przedziały prognozy, zimny start nowych kolekcji, brak towaru jako cenzurowanie popytu.

## 2. Przypadek biznesowy i jego przełożenie na analizę

| Element biznesowy | Przełożenie na analizę |
| --- | --- |
| Decyzja: ile sztuk wysłać do lokalizacji w 4 tygodnie | Prognoza sztuk na tydzień 1–4 oraz suma z 4 tygodni na poziomie `StyleCode × lokalizacja` |
| Dzisiejsza praktyka: średnia z 4 tygodni + korekty „na oko" | Baseline B1: średnia tygodniowa z 4 ostatnich pełnych tygodni |
| „Najlepiej sprzedające się modele (top 20)" | 20 modeli o największej sprzedaży w 8 tygodniach przed origin |
| Kryterium wewnętrzne: błąd poniżej 30% | WAPE sumy 4 tygodni na poziomie `StyleCode × lokalizacja`; osobno WAPE per horyzont |
| Brak planowanych akcji rabatowych w W39–W42 | Cechy rabatowe w horyzoncie ustawione na brak promocji (założenie potwierdzone przez Pricing) |
| Wchodzące kolekcje (transze 3, 17, 31 sierpnia 2026) | Zimny start: modele z ≤ 6 tygodniami historii |
| Zdarzające się braki towaru | Zerowa sprzedaż ≠ zerowy popyt: cenzurowanie |
| Brak dostaw, pogody, kalendarza marketingu | Kalendarz świąt budowany jako dane zewnętrzne; wpływ pogody niemożliwy do wyjaśnienia |

## 3. Komplet danych i informacji dla ucznia

**Zlecenie (treść).** Kierownik merchandisingu i alokacji: dosyłki na tygodnie 2026-W39…W42 planowane dziś średnią z 4 tygodni z korektą „na oko"; błędy przy zmianie sezonu i nowych kolekcjach (raz braki kurtek, raz nadmiar); pytanie, czy można prognozować lepiej i o ile; interesuje top 20 modeli; Pricing potwierdził brak akcji w tym okresie; termin: poniedziałek 2026-09-21.

**Kontekst firmy.**
- Nordvik: polska sieć odzieżowa z własną marką; 5 sklepów i online; PLN; VAT 23%.
- Sklepy: Warszawa Arkadia 420 m², Warszawa Mokotów 260 m², Kraków Rynek 180 m² do marca 2026 i 320 m² od 2026-04-01, Poznań 300 m², Gdańsk 240 m².
- Kategorie: Kurtki, Sukienki, Swetry, Jeansy, T-shirty, Koszule, Akcesoria. Model = `StyleCode`; SKU = model × kolor × rozmiar.
- Sezony: SS (luty–lipiec), AW (sierpień–styczeń). Cykl ceny: pełna cena, po ok. 8 tygodniach rabat −20…−30%, potem wyprzedaż −40…−60%.
- Szczyty: Black Friday i grudzień; luty najsłabszy (orientacyjnie).
- Stacjonarne zamknięte w święta i większość niedziel (otwarte: ostatnia niedziela stycznia, kwietnia, czerwca i sierpnia, niedziela przed Wielkanocą, od 2025 trzy niedziele przed Wigilią; Wigilia wolna od 2025). Online działa codziennie.
- Brak w danych: ID klienta, dostaw i przesunięć, historii cennika, ruchu na stronie, pogody, kalendarza marketingu.

**Tabele** (`datasets/synthetic/bc01/`, Parquet):
- `dim_date`: `DateKey`, `Date`, `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth`, `IsoYear`, `IsoWeek`, `YearWeek`, `DayOfWeek`, `DayName`, `IsWeekend`, `Season`.
- `dim_store`: `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel`, `Format`, `SalesAreaM2` (bieżąca), `OpenedDate`, `RemodelDate`.
- `dim_product`: `ProductKey`, `SKU`, `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size`, `ListPrice` (brutto, bieżąca), `UnitCost`, `IsActive`.
- `merch_plan`: `StyleCode`, `Collection` (`SS25`, `AW25`, `SS26`, `AW26`, `BASIC`), `LaunchDate` (planowana).
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.
- `fact_inventory_daily`: `InventoryKey`, `DateKey`, `ProductKey`, `StoreKey`, `StockQuantity`, `LoadId` (migawka na koniec dnia).

**Ograniczenia dokumentowane.**
- Sprzedaż od 2025-01-01 do 2026-09-20; stany tylko od sierpnia 2026 (bieżący sezon); brak kalendarza promocji (rabaty tylko w `DiscountAmount`).
- Stan to migawka: nie sumować dni; różnica migawek nie jest sprzedażą.
- `ListPrice` i `SalesAreaM2` bieżące; `UnitPrice` to cena przed rabatem.
- Relacje: `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = GrossAmount / 1,23`.

**Definicje.** Sztuki = `SUM(Quantity)`; sprzedaż netto = `SUM(NetAmount)`; stopa rabatu = rabat / `SUM(Quantity × UnitPrice)`; tydzień handlowy = ISO (`IsoYear` + `IsoWeek`, nigdy `Year` + `IsoWeek`); WAPE = suma błędów bezwzględnych / suma sprzedaży rzeczywistej (agregowane po całym zbiorze); bias = (suma prognoz − suma rzeczywistych) / suma rzeczywistych.

**Produkty końcowe.** Notebook (Metadata & Purpose, Setup, Load Data, Explore, Transform, Analyze, Results & Conclusions, Appendix), raport biznesowy na 1 stronę, opcjonalnie kod pomocniczy i zapytania SQL z nagłówkiem. Środowisko: Python, Jupyter, MLflow jeśli dostępny.

