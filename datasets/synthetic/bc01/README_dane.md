# Nordvik: dane do prognozy popytu tygodniowego

Wyciąg z hurtowni danych sieci odzieżowej Nordvik (5 sklepów stacjonarnych i sklep internetowy). Waluta: PLN, VAT 23%.
Ceny `UnitPrice` i `ListPrice` są brutto. Format: Parquet (jeden plik na tabelę).

## Zakres

- Sprzedaż (`fact_sales`): od 2025-01-01 do 2026-09-20 (niedziela, koniec ISO tygodnia 2026-W38).
- Stany magazynowe (`fact_inventory_daily`): wyłącznie od 2026-08-01 do 2026-09-20, tylko aktywne modele, migawka na koniec dnia.
- Kalendarz (`dim_date`): od 2024-12-01 do 2026-12-31.
- Sklepy stacjonarne nie sprzedają w święta państwowe ani w niedziele niehandlowe; sklep internetowy działa codziennie.

## Tabele

- `dim_date`: `DateKey` (yyyymmdd), `Date`, `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth`, `IsoYear`, `IsoWeek`,
  `YearWeek` (np. `2026-W38`, z roku ISO), `DayOfWeek` (1 = poniedziałek), `DayName`, `IsWeekend`,
  `Season` (luty–lipiec `SS<rr>`, sierpień–styczeń `AW<rr>`; styczeń należy do `AW` poprzedniego roku).
- `dim_store`: `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (STORE/ONLINE), `Format`,
  `SalesAreaM2` (metraż bieżący; hurtownia nie przechowuje historii metrażu), `OpenedDate`, `RemodelDate`.
- `dim_product`: `ProductKey`, `SKU` (`StyleCode`-`KodKoloru`-`Rozmiar`), `StyleCode`, `StyleName`, `Department`,
  `Category`, `Color`, `Size` (XS–XL, `ONE` dla akcesoriów), `ListPrice`, `UnitCost` (koszt jednostkowy netto), `IsActive`.
- `merch_plan`: `StyleCode`, `Collection` (`BASIC`, `SS25`, `AW25`, `SS26`, `AW26`), `LaunchDate` (planowana data premiery).
  Plan jest planem: faktyczny początek sprzedaży może się różnić.
- `fact_sales`: jedna pozycja paragonu na wiersz. `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`,
  `TransactionNo` (`T-<StoreCode>-<yyyymmdd>-<numer paragonu>`), `LineNumber`, `Quantity`, `UnitPrice`, `DiscountAmount`,
  `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.
- `fact_inventory_daily`: `InventoryKey`, `DateKey`, `ProductKey`, `StoreKey`, `StockQuantity`, `LoadId`.

## Relacje

- `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = GrossAmount / 1,23` (2 miejsca).
- `UnitPrice` równa się `ListPrice` modelu (cena stała w czasie); obniżki widoczne są wyłącznie w `DiscountAmount`.
- Klucze obce: `DateKey` → `dim_date`, `ProductKey` → `dim_product`, `StoreKey` → `dim_store`.

## Ograniczenia danych (udokumentowane przez firmę)

- Stany magazynowe tylko od sierpnia 2026.
- Brak danych o dostawach, historii cen, klientach i pogodzie.
- `SalesAreaM2` to metraż bieżący.
- `merch_plan` zawiera daty planowane.
