-- Grain: one row per order line. Dates are local business dates.
WITH line_sales AS (
  SELECT s.TransactionNo, s.LineNo, CAST(s.SoldAt AS date) AS SaleDate,
         s.StoreCode, s.SKU, s.Quantity, s.UnitNetPrice,
         s.Quantity * s.UnitNetPrice AS NetSalesBeforeReturns
  FROM dbo.SalesLine AS s
  WHERE s.SoldAt >= '2026-09-07' AND s.SoldAt < '2026-09-14'
    AND s.Status = 'COMPLETED'
), weekly AS (
  SELECT DATEPART(isowk, SaleDate) AS IsoWeek, StoreCode,
         SUM(NetSalesBeforeReturns) AS WeeklyNetSalesBeforeReturns,
         COUNT(DISTINCT TransactionNo) AS TransactionCount,
         COUNT(*) AS LineCount
  FROM line_sales
  GROUP BY DATEPART(isowk, SaleDate), StoreCode
)
SELECT IsoWeek, StoreCode, WeeklyNetSalesBeforeReturns, TransactionCount, LineCount
FROM weekly ORDER BY StoreCode;
