# Nordvik: sprzedaż i zwroty (wyciąg z hurtowni)

Wyciąg z hurtowni danych sieci odzieżowej Nordvik (5 sklepów stacjonarnych i sklep internetowy). Waluta: PLN. Kwoty brutto zawierają VAT 23%.
Stan wyciągu: 2026-09-20. Format: Parquet (kompresja zstd), po jednym pliku na tabelę.

## Zakres

- Sprzedaż (`fact_sales`): 2025-01-01 … 2026-09-20.
- Zwroty (`fact_returns`): historia pełna od 2025-01-01; obejmuje zwroty przyjęte do 2026-09-20 włącznie. Zwroty przyjęte później nie są jeszcze w hurtowni.
- Wymiar dat (`dim_date`): 2024-12-01 … 2026-12-31.

## Tabele i kolumny

### dim_date
`DateKey` (int, yyyymmdd), `Date`, `Year`, `Quarter`, `Month`, `MonthName` (po polsku), `YearMonth` (`2026-09`), `IsoYear`, `IsoWeek`, `YearWeek` (`2026-W38`), `DayOfWeek` (1 = poniedziałek), `DayName`, `IsWeekend`, `Season` (`SS<rr>` luty–lipiec, `AW<rr>` sierpień–styczeń; styczeń należy do `AW` poprzedniego roku).

### dim_store
`StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (`STORE` / `ONLINE`), `Format`, `SalesAreaM2` (bieżąca powierzchnia sprzedaży; dla sklepu internetowego brak), `OpenedDate`, `RemodelDate`.

### dim_product
`ProductKey`, `SKU` (`StyleCode`-`KodKoloru`-`Rozmiar`), `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size` (XS, S, M, L, XL; akcesoria `ONE`), `ListPrice` (brutto), `UnitCost` (koszt jednostkowy netto), `IsActive`. W katalogu jest 36 modeli, każdy w 2 kolorach.

### fact_sales (jedna pozycja paragonu = jeden wiersz)
`SalesKey`, `DateKey`, `ProductKey`, `StoreKey`, `TransactionNo` (`T-<StoreCode>-<yyyymmdd>-<numer>`), `LineNumber`, `Quantity`, `UnitPrice` (brutto), `DiscountAmount`, `GrossAmount`, `NetAmount`, `UnitCost`, `LoadId`.

Relacje arytmetyczne:
- `GrossAmount = Quantity × UnitPrice − DiscountAmount`
- `NetAmount = GrossAmount / 1,23`
- `UnitPrice` równa się `ListPrice` produktu; ewentualny rabat jest wyłącznie w `DiscountAmount`.
- Para (`TransactionNo`, `LineNumber`) jest unikalna.

### fact_returns (zwrot przyjęty w portalu zwrotów)
`ReturnKey`, `DateKey` (data przyjęcia zwrotu), `ProductKey`, `StoreKey` (miejsce przyjęcia zwrotu), `ReturnNo`, `TransactionNo` (paragon pierwotnej sprzedaży), `Quantity` (zwrócone sztuki), `ReturnAmount` (zwrócona kwota brutto, proporcjonalna do zapłaconej za zwrócone sztuki), `ReturnReason`, `LoadId`.

## Ograniczenia i uwagi

- Zwrot nie ma numeru linii paragonu ani identyfikatora klienta. Zwrot łączy się ze sprzedażą po (`TransactionNo`, `ProductKey`). Jeśli ten sam SKU występuje na paragonie w więcej niż jednej pozycji, połączenie nie wskazuje pozycji jednoznacznie.
- `DateKey` i `StoreKey` zwrotu oznaczają datę i miejsce przyjęcia zwrotu, które mogą różnić się od daty i miejsca zakupu. Zwroty w sklepach stacjonarnych są przyjmowane w dni otwarcia sklepu.
- Jeden wiersz zwrotu może dotyczyć części sztuk z pozycji; paragon może mieć kilka wierszy zwrotu tego samego produktu.
- `ReturnReason` jest wypełniane przez obsługę przy przyjęciu i bywa puste. Wartości: `WRONG_SIZE`, `CHANGED_MIND`, `DAMAGED`, `OTHER`.
- `LoadId` jest stałe w całym wyciągu.
- Sklepy stacjonarne nie sprzedają w święta i niedziele niehandlowe; sklep internetowy działa codziennie. Powierzchnia `SalesAreaM2` to wartość bieżąca; sklep S-KRK-01 miał przed przebudową (`RemodelDate` 2026-04-01) mniejszą powierzchnię.
- Dane są syntetyczne.
