# Katalog obiektów  
Wersja katalogu `CAT-2026.10`, eksport 2026-10-14 08:00 Europe/Warsaw.

| Obiekt | Ziarno | Klucz / uwaga |
|---|---|---|
| src.SalesRaw | plik × wiersz | SourceFile, ExtractedAt; surowy tekst |
| src.AdjustmentRaw | plik × wiersz korekty | AdjustmentId, SourceFile, ExtractedAt |
| stg.Sales | zaakceptowana pozycja | SourceLineId; konwersja z surowego |
| stg.Adjustment | zaakceptowana korekta | AdjustmentId; kwoty signed |
| dbo.DimDate | dzień | DateKey |
| dbo.DimStore | sklep | StoreKey |
| dbo.DimProduct | SKU | ProductKey |
| dbo.DimAdjustmentType | adjustment type | AdjustmentTypeKey |
| dbo.FactSales | pozycja transakcji | TransactionNo + LineNo; netto przed zwrotami |
| dbo.FactAdjustment | korekta pozycji | AdjustmentId; AdjustmentAmount signed |
| dbo.FactReturns | przyjęta pozycja zwrotu | ReturnLineId; kwota dodatnia |
| dbo.LoadLog | przebieg ładowania | RunId; status i liczniki |
| reporting.vw_SalesAfterAdjustments | sklep × ISO tydzień | raportowa miara, definicję potwierdza SQL |
| reporting.vw_WeeklySalesLegacy | sklep × tydzień kalendarzowy | historyczny obiekt, emerytowany |
| reporting.vw_SalesAdjusted | nieznane | stary alias z dokumentacji; brak w eksporcie bieżącego schematu |

