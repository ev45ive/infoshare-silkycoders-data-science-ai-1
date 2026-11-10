# Nordvik - sprzedaz i stany sezonowych modeli odziezy (dane do analizy)

Wyciag z hurtowni danych sieci Nordvik (5 sklepow stacjonarnych i sklep internetowy) oraz jednorazowy eksport stanow magazynowych.
Waluta: PLN. `UnitPrice`, `ListPrice`, `GrossAmount`, `DiscountAmount` sa kwotami brutto (z VAT 23%); `NetAmount` jest netto.
Pliki: Parquet (kompresja zstd), odczyt np. `pandas.read_parquet`.

## Zakres

| Tabela | Wierszy | Zakres |
| --- | --- | --- |
| `dim_date` | 761 | 2024-12-01 ... 2026-12-31 |
| `dim_store` | 6 | 5 sklepow stacjonarnych + sklep internetowy |
| `dim_product` | 816 | 96 modeli, SKU = model x kolor x rozmiar |
| `merch_plan` | 96 | plan wprowadzenia modeli w 4 kolekcjach |
| `fact_sales` | 475,524 | 2025-02-02 ... 2026-09-20 (pozycje paragonow) |
| `fact_inventory_daily` | 649,196 | 2025-02-01 ... 2026-09-20 (migawka stanu na koniec dnia) |

Stan danych: 2026-09-20. Ostatnia kolekcja (`AW26`) jest w trakcie sezonu.

## Slownik danych

- `dim_date`: `DateKey` (int, yyyymmdd), `Date`, `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth` (np. 2026-09), `IsoYear`, `IsoWeek`, `YearWeek` (np. 2026-W38), `DayOfWeek` (1 = poniedzialek), `DayName`, `IsWeekend`, `Season` (SS<rr> lub AW<rr>; styczen nalezy do AW poprzedniego roku).
- `dim_store`: `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (STORE / ONLINE), `Format`, `SalesAreaM2` (powierzchnia biezaca), `OpenedDate`, `RemodelDate`.
- `dim_product`: `ProductKey`, `SKU` (= `StyleCode`-kod koloru-rozmiar), `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size` (XS, S, M, L, XL lub ONE dla akcesoriow), `ListPrice` (brutto), `UnitCost` (koszt jednostkowy netto), `IsActive` (1 = model w biezacej sprzedazy).
- `merch_plan`: `StyleCode`, `Collection` (SS25, AW25, SS26, AW26), `LaunchDate` (planowana data wprowadzenia), `PlannedUnits` (plan z systemu planowania).
- `fact_sales`: `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo` (T-<StoreCode>-<yyyymmdd>-<numer paragonu>), `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.
- `fact_inventory_daily`: `InventoryKey`, `DateKey`, `ProductKey`, `StoreKey`, `StockQuantity`, `LoadId`.

## Relacje arytmetyczne

- `UnitPrice` = `ListPrice` produktu; `GrossAmount` = `Quantity` x `UnitPrice` - `DiscountAmount`; `NetAmount` = `GrossAmount` / 1,23.
- Paragon (`TransactionNo`) ma jedna lub kilka pozycji (`LineNumber` od 1), jest zawsze w jednym sklepie i jednym dniu.
- Sklep internetowy ma wlasny stan magazynowy (`StoreKey` = 6).
- Sklepy stacjonarne nie sprzedaja w swieta i niedziele niehandlowe; sklep internetowy sprzedaje codziennie.
- Sprzedaz modelu w dniu D zmniejsza jego stan SKU x lokalizacja w migawce z dnia D.

## Ograniczenia danych

- Brak tabeli dostaw i przesuniec miedzy lokalizacjami: wszelkie zmiany stanu inne niz sprzedaz widac tylko w samych migawkach.
- Brak historii cen i informacji o akcjach: cena katalogowa jest stala, obnizki widac wylacznie w `DiscountAmount`.
- Stany pochodza z jednorazowego eksportu historycznego o nieznanej jakosci; kompletnosc i poprawnosc migawek nie jest gwarantowana.
- `PlannedUnits` pochodzi z systemu planowania (plan zakupu), a nie z dokumentow dostaw. Faktyczny start sprzedazy modelu moze roznic sie od `LaunchDate`.
- Kolekcja nie jest atrybutem produktu: przypisanie modelu do kolekcji wynika z `merch_plan`.
- `SalesAreaM2` to powierzchnia biezaca; sklep Krakow Rynek byl przebudowywany (`RemodelDate`).
- Brak zwrotow, klientow i danych o ruchu w sklepach.
