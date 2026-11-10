# BC-09: hurtownia danych i dokumenty procedur Nordvik

Zasoby do budowy asystenta analitycznego firmy Nordvik (sieć odzieżowa: 5 sklepów stacjonarnych i sklep internetowy, PLN, VAT 23%).

## Zawartość katalogu

| Element | Opis |
| --- | --- |
| `dbo.*.parquet` | Tabele hurtowni (wymiary i fakty) |
| `reporting.*.parquet` | Widoki raportowe zapisane jako tabele |
| `slownik_metryk.md` | Słownik metryk Nordvik |
| `docs_procedury/` | Dokumenty procedur (D01–D12), po polsku |
| `gold_set.jsonl` | Zbiór pytań (40): `id`, `question`, `category`, `split`; dla `dev` także `reference_answer` |

## Zakres danych

- Sprzedaż (`FactSales`) i zwroty (`FactReturns`): od 2025-01-01 do 2026-09-20.
- Stany magazynowe (`FactInventoryDaily`): od 2026-08-01 do 2026-09-20 (migawka na koniec dnia, bieżący sezon).
- `DimDate`: dni od 2024-12-01 do 2026-12-31.
- Katalog: 134 SKU (15 modeli w 2 kolorach, rozmiary XS–XL, akcesoria `ONE`).
- Sklepy stacjonarne nie sprzedają w święta i w niedziele niehandlowe; sklep internetowy działa codziennie.
- Przyjęcie zwrotu może nastąpić w innej lokalizacji niż zakup.

## Tabele `dbo`

- `DimDate`: `DateKey` (yyyymmdd), `Date`, `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth`, `IsoYear`, `IsoWeek`, `YearWeek`, `DayOfWeek` (1 = poniedziałek), `DayName`, `IsWeekend`, `Season` (SS/AW).
- `DimStore`: `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (STORE/ONLINE), `Format`, `SalesAreaM2` (powierzchnia bieżąca), `OpenedDate`, `RemodelDate`.
- `DimProduct`: `ProductKey`, `SKU`, `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size`, `ListPrice` (brutto), `UnitCost` (netto), `IsActive`.
- `FactSales`: linia transakcji. `TransactionNo`, `LineNumber`, `Quantity`, `UnitPrice` (brutto, równa `ListPrice`), `DiscountAmount`, `GrossAmount` = `Quantity × UnitPrice − DiscountAmount`, `NetAmount` = `GrossAmount / 1,23`, `UnitCost`, `LoadId`.
- `FactReturns`: `DateKey` i `StoreKey` to data i miejsce przyjęcia zwrotu, `ReturnNo`, `TransactionNo` (transakcja sprzedaży), `Quantity`, `ReturnAmount` (z VAT), `ReturnReason`, `LoadId`.
- `FactInventoryDaily`: `StockQuantity` na koniec dnia dla SKU objętych zapasem w danej lokalizacji.

## Widoki `reporting`

| Widok | Kolumny |
| --- | --- |
| `vw_SalesWeekly` | tydzień ISO (`IsoYear`, `IsoWeek`, `YearWeek`, `WeekStart`, `WeekEnd`), `Channel`, `Region`, `Department`, `Category`; `Units`, `Transactions`, `GrossAmount`, `DiscountAmount`, `NetAmount`, `CostAmount` |
| `vw_SalesDaily` | `Date`, `StoreCode`, `Channel`; `Units`, `Transactions`, `Revenue` (przychód dnia), `DiscountAmount`, `CostAmount` |
| `vw_StockAvailability` | `Date`, `StoreCode`, `SkuInFeed`, `SkuAvailable`, `SkuUnavailable`, `AvailabilityPct` (dostępność w %) |
| `vw_StoreScorecard` | `YearMonth`, `StoreCode` (tylko sklepy stacjonarne), `NetSales`, `CostOfGoods`, `ReturnsNet`, `GrossMargin`, `SalesAreaM2`, `NetSalesPerM2` |

## Dokumenty procedur

| ID | Tytuł | Wersja | Obowiązuje od | Właściciel |
| --- | --- | --- | --- | --- |
| D01 | Zwrot bez paragonu | 2.1 | 2025-03-01 | Obsługa zwrotów |
| D02 | Zwrot bez paragonu | 3.0 | 2026-02-01 | Obsługa zwrotów |
| D03 | Zwroty zakupów online | 1.4 | 2025-06-01 | E-commerce |
| D04 | Reklamacja towaru uszkodzonego | 2.0 | 2025-04-01 | Obsługa klienta |
| D05 | Wymiana rozmiaru | 1.2 | 2025-02-01 | Sprzedaż |
| D06 | Korekta ceny na kasie | 1.1 | 2025-11-01 | Controlling |
| D07 | Rabaty i upusty: zasady zatwierdzania | 2.0 | 2026-01-15 | Pricing |
| D08 | Przesunięcia międzysklepowe | 1.0 | 2025-05-01 | Logistyka |
| D09 | Zamknięcie dnia w sklepie | 1.3 | 2025-09-01 | Sprzedaż |
| D10 | Karty podarunkowe | 1.0 | 2025-07-01 | Sprzedaż |
| D11 | Inwentaryzacja | 1.1 | 2025-08-01 | Logistyka |
| D12 | Raportowanie sprzedaży dla kierowników sklepów | 1.0 | 2025-04-15 | Controlling |

Brak dokumentów dotyczących innych tematów niż wymienione powyżej.

## Zbiór pytań

40 pytań w czterech kategoriach po 10: `liczbowe`, `procedurowe`, `wieloetapowe`, `poza_zakresem`. Podział: `dev` (24, z odpowiedzią wzorcową) i `test` (16, bez odpowiedzi).
