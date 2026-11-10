# Nordvik — zbiór danych sprzedażowych (paragony)

Syntetyczny wyciąg z hurtowni sprzedaży sieci odzieżowej Nordvik (5 sklepów stacjonarnych i sklep internetowy).
Waluta: PLN. Ceny (`UnitPrice`, `ListPrice`) są brutto (VAT 23%). `UnitCost` to koszt jednostkowy netto.

## Zakres
- Sprzedaż: 2025-01-01 — 2026-09-20 (włącznie), 413,573 wierszy sprzedaży w 192,492 paragonach.
- Kalendarz (`dim_date`): 2024-12-01 — 2026-12-31.
- Katalog: 36 modeli (`StyleCode`), każdy w 2 kolorach; rozmiary XS–XL, akcesoria `ONE`; 312 SKU.

## Tabele (pliki Parquet)
| Plik | Opis |
| --- | --- |
| `dim_date.parquet` | Kalendarz: `DateKey` (yyyymmdd), `Date`, rok/kwartał/miesiąc, tydzień ISO (`YearWeek`), dzień tygodnia (1 = poniedziałek), `Season` (`SS<rr>` luty–lipiec, `AW<rr>` sierpień–styczeń; styczeń należy do `AW` poprzedniego roku) |
| `dim_store.parquet` | Lokalizacje: `StoreKey`, `StoreCode`, `StoreName`, `City`, `Region`, `Channel` (STORE/ONLINE), `Format`, `SalesAreaM2` (bieżąca powierzchnia), `OpenedDate`, `RemodelDate` |
| `dim_product.parquet` | SKU: `ProductKey`, `SKU` (`StyleCode`-`KodKoloru`-`Rozmiar`), `StyleCode`, `StyleName`, `Department`, `Category`, `Color`, `Size`, `ListPrice`, `UnitCost`, `IsActive` |
| `fact_sales.parquet` | Wiersze sprzedaży (jedna pozycja paragonu = jeden wiersz) |

## `fact_sales`
| Kolumna | Opis |
| --- | --- |
| `SalesKey` | Klucz wiersza |
| `DateKey`, `ProductKey`, `StoreKey` | Klucze do wymiarów |
| `TransactionNo` | Numer paragonu: `T-<StoreCode>-<yyyymmdd>-<numer>`; paragon = unikalny `TransactionNo` |
| `LineNumber` | Numer pozycji w paragonie (od 1) |
| `Quantity` | Liczba sztuk (≥ 1) |
| `UnitPrice` | Cena katalogowa brutto (= `ListPrice`) |
| `DiscountAmount` | Rabat w PLN brutto na całą pozycję |
| `GrossAmount` | `Quantity × UnitPrice − DiscountAmount` |
| `NetAmount` | `GrossAmount / 1,23`, zaokrąglone do 2 miejsc |
| `UnitCost` | Koszt jednostkowy netto |
| `LoadId` | Identyfikator ładowania (stała) |

## Uwagi i ograniczenia
- Brak identyfikatora klienta i programu lojalnościowego: jedyną jednostką zakupu jest paragon (`TransactionNo`).
- Dane obejmują wyłącznie sprzedaż (bez zwrotów, anulowań i stanów magazynowych).
- Sklepy stacjonarne nie mają sprzedaży w dni świąteczne ani w niedziele niehandlowe; sklep internetowy działa codziennie.
- Rabat występował wyłącznie w akcji Black Friday 2025-11-24…30 (−20% na wszystko).
- Kraków Rynek był w 2026 po przebudowie; `SalesAreaM2` to powierzchnia bieżąca.
- Ten sam model może wystąpić w paragonie w więcej niż jednej pozycji (np. inny rozmiar).
