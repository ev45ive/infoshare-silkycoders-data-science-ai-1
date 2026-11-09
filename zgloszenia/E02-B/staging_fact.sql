-- Fragment ETL z tego samego wydania REL-2026.10.3
INSERT stg.Sales(SourceLineId,TransactionNo,LineNo,SoldAt,StoreCode,SKU,Quantity,UnitNetPrice,Status,SourceFile,ExtractedAt)
SELECT SourceLineId,TransactionNo,LineNo,TRY_CONVERT(date,SoldAt),StoreCode,SKU,
       TRY_CONVERT(int,Quantity),TRY_CONVERT(decimal(12,2),UnitNetPrice),Status,SourceFile,ExtractedAt
FROM src.SalesRaw;
INSERT dbo.FactSales(DateKey,StoreKey,ProductKey,TransactionNo,LineNo,Quantity,UnitNetPrice,Status)
SELECT d.DateKey,st.StoreKey,p.ProductKey,s.TransactionNo,s.LineNo,s.Quantity,s.UnitNetPrice,s.Status
FROM stg.Sales s JOIN dbo.DimDate d ON d.FullDate=s.SoldAt
JOIN dbo.DimStore st ON st.StoreCode=s.StoreCode JOIN dbo.DimProduct p ON p.SKU=s.SKU;
-- SourceFile/ExtractedAt nie są kopiowane do FactSales.
