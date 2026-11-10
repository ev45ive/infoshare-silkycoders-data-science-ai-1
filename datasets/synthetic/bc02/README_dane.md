# Nordvik: sprzedaż, plik źródłowy i dziennik ładowań (zbiór `bc02`)

Dane syntetyczne sieci odzieżowej Nordvik (5 sklepów stacjonarnych + sklep internetowy), PLN, VAT 23%.
`UnitPrice` i `ListPrice` są kwotami brutto (z VAT); `NetAmount` to wartość netto.
Zakres sprzedaży: **2025-01-01 – 2026-09-20**. Dziennik ładowań: **2025-01-02 – 2026-09-21**. Format plików: Parquet.

## Tabele

| Plik | Opis |
| --- | --- |
| `dim_date.parquet` | Kalendarz od 2024-12-01 do 2026-12-31: `DateKey` (yyyymmdd), `Date`, `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth`, `IsoYear`, `IsoWeek`, `YearWeek`, `DayOfWeek` (1 = poniedziałek), `DayName`, `IsWeekend`, `Season` (`SS<rr>` luty–lipiec, `AW<rr>` sierpień–styczeń; styczeń należy do sezonu AW poprzedniego roku) |
| `dim_store.parquet` | Lokalizacje: `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (STORE/ONLINE), `Format`, `SalesAreaM2` (bieżąca powierzchnia sprzedażowa), `OpenedDate`, `RemodelDate` |
| `dim_product.parquet` | Katalog SKU (14 modeli w 2 kolorach; rozmiary XS–XL lub `ONE` dla akcesoriów): `ProductKey`, `SKU` (`StyleCode`-`KodKoloru`-`Rozmiar`), `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size`, `ListPrice` (brutto), `UnitCost` (koszt jednostkowy netto), `IsActive` |
| `src_sales_raw.parquet` | Zawartość plików wyciągów ze sprzedaży, zapisana tak, jak przychodzą (wszystkie pola tekstowe), w kolejności przybycia plików |
| `fact_sales.parquet` | Wynik procedury ładowania sprzedaży (stan po ostatnim udanym uruchomieniu) |
| `load_log.parquet` | Dziennik uruchomień procedury ładowania |

### `src_sales_raw`
`RawId` (rosnący numer wiersza w kolejności przybycia), `SourceFile` (`POS_<yyyymmdd>.csv` – wszystkie sklepy stacjonarne,
`WEB_<yyyymmdd>.csv` – sklep internetowy; plik za dzień D jest wyciągany w dniu D+1 w nocy), `ExtractedAt`,
`TransactionNo` (`T-<StoreCode>-<yyyymmdd>-<numer>`, numeracja od 1 w obrębie sklepu i dnia), `LineNumber`, `SalesDate`
(`yyyy-mm-dd`), `SKU`, `StoreCode`, `Quantity`, `UnitPrice`, `DiscountAmount` — wszystkie jako tekst.
Dla dni i sklepów, w których nie było sprzedaży (np. sklepy stacjonarne w niedziele niehandlowe i święta), plik nie zawiera wierszy.

### `fact_sales`
`SalesKey`, `TransactionNo`, `LineNumber`, `DateKey`, `StoreKey`, `ProductKey`, `Quantity`, `UnitPrice`, `DiscountAmount`,
`GrossAmount` = `Quantity` × `UnitPrice` − `DiscountAmount`, `NetAmount` = `GrossAmount` / 1,23, `UnitCost` (z `dim_product`),
`LoadId` (identyfikator ostatniego udanego uruchomienia, jednakowy dla wszystkich wierszy).

### `load_log`
Jeden wiersz dziennie (procedura `etl.LoadSales`, uruchamiana około 03:00 i przetwarzająca pliki z poprzedniego dnia):
`LoadId`, `PackageName`, `StartedAt`, `FinishedAt`, `Status` (`SUCCESS` / `FAILED`), `RowsRead` (liczba wierszy w `src_sales_raw`
**narastająco**, które były dostępne w momencie uruchomienia), `RowsLoaded` (liczba wierszy w `fact_sales` narastająco),
`RowsRejected` (= `RowsRead` − `RowsLoaded`), `ErrorMessage` (dla uruchomień zakończonych niepowodzeniem).
Przy uruchomieniu zakończonym niepowodzeniem pola `RowsRead`, `RowsLoaded` i `RowsRejected` są puste, a w `fact_sales` zostaje stan z poprzedniego udanego uruchomienia.

## Proces ładowania (pełne przeładowanie)

Każde uruchomienie przeładowuje `fact_sales` w całości z całej zawartości `src_sales_raw` dostępnej w momencie startu:

1. **Krok 1 – konwersja typów.** Wiersz jest odrzucany, jeśli pole `TransactionNo`, `LineNumber`, `SalesDate`, `SKU`, `StoreCode`,
   `Quantity` lub `UnitPrice` jest puste albo nie daje się skonwertować do właściwego typu (liczby w zapisie z kropką dziesiętną).
   Niekonwertowalne `DiscountAmount` jest zastępowane wartością 0.
2. **Krok 2 – dopasowanie wymiarów.** Wiersz jest odrzucany, jeśli `SalesDate` nie ma dopasowania w `dim_date`, `SKU` w `dim_product`
   (dopasowanie dokładne) albo `StoreCode` w `dim_store`.
3. Odrzucone wiersze nie są nigdzie zapisywane; jedynym śladem jest różnica `RowsRead` − `RowsLoaded` w `load_log`.
4. Procedura nie usuwa powtórzeń: wszystkie wiersze, które przejdą kroki 1–2, trafiają do `fact_sales`.

## Ograniczenia

- Dane są syntetyczne; nie odzwierciedlają rzeczywistej firmy.
- Brak czasu transakcji w ciągu dnia i brak identyfikatorów klientów.
- Powierzchnia sprzedażowa w `dim_store` jest bieżąca (po zakończeniu prac w sklepie, który ma wpisaną `RemodelDate`).
- Sprzedaż sklepów stacjonarnych występuje wyłącznie w dniach handlowych zgodnie z polskim kalendarzem (niedziele niehandlowe i święta bez sprzedaży).
