# Dane Nordvik: sprzedaż i zwroty (wyciąg z hurtowni)

Syntetyczny wyciąg z hurtowni danych sieci odzieżowej Nordvik (5 sklepów stacjonarnych i sklep internetowy).
Waluta: PLN, VAT 23%. Format: Parquet.

## Zakres
- Sprzedaż: 2025-01-01 … 2026-09-20 (`fact_sales`). Zwroty: przyjęte do 2026-09-20 (`fact_returns`).
- `dim_date`: 2024-12-01 … 2026-12-31.
- Katalog: 36 modeli, każdy w 2 kolorach; odzież w rozmiarach XS-XL, akcesoria `ONE` (312 SKU).

## Tabele i kolumny
**dim_date**: `DateKey` (int, yyyymmdd), `Date`, `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth` (`2026-09`), `IsoYear`, `IsoWeek`,
`YearWeek` (`2026-W38`), `DayOfWeek` (1 = poniedziałek), `DayName`, `IsWeekend`, `Season` (`SS<rr>` luty-lipiec, `AW<rr>` sierpień-styczeń; styczeń należy do `AW` poprzedniego roku).

**dim_store**: `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (`STORE`/`ONLINE`), `Format`, `SalesAreaM2` (bieżąca; brak dla sklepu internetowego), `OpenedDate`, `RemodelDate`.

**dim_product**: `ProductKey`, `SKU` (`StyleCode`-`KodKoloru`-`Rozmiar`), `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size`, `ListPrice` (brutto, bieżący), `UnitCost` (netto), `IsActive`.

**fact_sales** (jedna pozycja paragonu): `SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice` (brutto),
`DiscountAmount` (brutto, ≥ 0), `GrossAmount`, `NetAmount`, `UnitCost` (netto, za sztukę), `LoadId`.

**fact_returns** (zwrot po jednostkach z pozycji sprzedaży): `ReturnKey`, `DateKey` (data przyjęcia), `ProductKey`, `StoreKey` (sklep przyjęcia), `ReturnNo`, `TransactionNo` (paragon pierwotnej sprzedaży),
`Quantity`, `ReturnAmount`, `ReturnReason` (bywa puste), `LoadId`.

## Relacje arytmetyczne
- `GrossAmount = Quantity × UnitPrice − DiscountAmount`; `NetAmount = round(GrossAmount / 1,23; 2)`.
- `ReturnAmount` = zapłacone brutto za zwrócone sztuki = `GrossAmount × zwrócone / Quantity`.
- Suma zwróconych sztuk na (`TransactionNo`, `ProductKey`) nie przekracza sprzedanych; zwrot ma datę późniejszą niż sprzedaż.
- Sklepy stacjonarne nie sprzedają ani nie przyjmują zwrotów w święta i niedziele niehandlowe; sklep internetowy działa codziennie.

## Ograniczenia dokumentowane przez firmę
- Brak historii cennika i brak spisanego kalendarza akcji: `ListPrice` jest wartością bieżącą, a rabat widać wyłącznie w `DiscountAmount` na pozycjach.
- Metraż w `dim_store` jest bieżący (Kraków Rynek miał mniejszą powierzchnię przed przebudową; remont zakończony 2026-04-01).
- Zwroty niosą datę i sklep przyjęcia, które mogą różnić się od sprzedaży (zakup online można zwrócić w sklepie).
- Brak danych o zapasach i ruchu w sklepach.
