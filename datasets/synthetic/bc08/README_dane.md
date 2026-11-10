# Nordvik - zbiór danych sprzedażowych (wyciąg z hurtowni)

Wyciąg z hurtowni danych sieci odzieżowej Nordvik: pięć sklepów stacjonarnych i sklep internetowy.
Waluta: PLN. Kwoty brutto zawierają VAT 23%.

## Zakres

- Sprzedaż: od 2025-01-01 do 2026-09-20 (dzienne ziarno, linie paragonów).
- Wiersze: `fact_sales` 441,858, `dim_product` 124, `dim_store` 6, `dim_date` 761.
- Format plików: Parquet (kompresja snappy).

## Tabele

### dim_date (dzień od 2024-12-01 do 2026-12-31)
`DateKey` (int, yyyymmdd), `Date`, `Year`, `Quarter`, `Month`, `MonthName` (po polsku), `YearMonth` (np. `2026-09`),
`IsoYear`, `IsoWeek`, `YearWeek` (np. `2026-W38`, numeracja ISO-8601; rok ISO może różnić się od roku kalendarzowego
na przełomie roku), `DayOfWeek` (1 = poniedziałek), `DayName`, `IsWeekend`, `Season` (`SS<rr>` luty-lipiec,
`AW<rr>` sierpień-styczeń; styczeń należy do `AW` poprzedniego roku).

### dim_store
`StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (`STORE`/`ONLINE`), `Format`,
`SalesAreaM2`, `OpenedDate`, `RemodelDate`.

### dim_product (124 SKU: 14 modeli, po 2 kolory, rozmiary XS-XL lub `ONE` dla akcesoriów)
`ProductKey`, `SKU` (`StyleCode`-`KodKoloru`-`Rozmiar`), `StyleCode`, `StyleName`, `Department`, `Category`,
`Color`, `Size`, `ListPrice` (brutto), `UnitCost` (koszt jednostkowy netto), `IsActive`.

### fact_sales
Ziarno: jedna linia paragonu (jeden SKU na jednym paragonie).
`SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo` (`T-<StoreCode>-<yyyymmdd>-<nr paragonu>`),
`LineNumber` (od 1 w obrębie paragonu), `Quantity`, `UnitPrice` (cena katalogowa brutto), `DiscountAmount`,
`GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.

## Relacje arytmetyczne

- `DiscountAmount` = `Quantity` x `UnitPrice` x stopa rabatu, zaokrąglone do 2 miejsc.
- `GrossAmount` = `Quantity` x `UnitPrice` - `DiscountAmount` (z VAT).
- `NetAmount` = `GrossAmount` / 1,23 (bez VAT), zaokrąglone do 2 miejsc.
- `UnitPrice` = `ListPrice` z `dim_product`; `UnitCost` = `UnitCost` z `dim_product`.
- Klucze obce: `DateKey` -> `dim_date`, `ProductKey` -> `dim_product`, `StoreKey` -> `dim_store`.

## Ograniczenia dokumentowane przez firmę

- `SalesAreaM2` w `dim_store` to metraż **bieżący**. Hurtownia nie przechowuje historii metrażu.
- Ten zbiór nie zawiera zwrotów, stanów magazynowych ani cen innych niż katalogowe (rabaty są w `DiscountAmount`).
- Hurtownia nie przechowuje rejestru zdarzeń operacyjnych sklepów.
- Sklepy stacjonarne obowiązuje polski kalendarz handlowy; sklep internetowy działa codziennie.
