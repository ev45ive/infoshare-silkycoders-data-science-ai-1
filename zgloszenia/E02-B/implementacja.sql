-- Aktualny wyciąg wdrożeniowy scenariusza: REL-2026.10.3, opublikowany 2026-10-13 17:20 Europe/Warsaw.
-- SourceFile zachowane w raw i staging; brak w faktach dbo.
CREATE VIEW reporting.vw_SalesAfterAdjustments AS
WITH sales AS (
 SELECT s.StoreKey, d.IsoYearWeek,
        SUM(s.Quantity * s.UnitNetPrice) AS BaseNetSales
 FROM dbo.FactSales s JOIN dbo.DimDate d ON d.DateKey=s.DateKey
 WHERE s.Status='COMPLETED' GROUP BY s.StoreKey,d.IsoYearWeek
), adj AS (
 SELECT a.StoreKey, d.IsoYearWeek, SUM(a.AdjustmentAmount) AS Adjustments
 FROM dbo.FactAdjustment a JOIN dbo.DimDate d ON d.DateKey=a.DateKey
 WHERE a.ApprovalStatus='POSTED' GROUP BY a.StoreKey,d.IsoYearWeek
)
SELECT s.StoreKey,s.IsoYearWeek,
       s.BaseNetSales + COALESCE(a.Adjustments,0) AS SalesAfterAdjustments
FROM sales s LEFT JOIN adj a ON a.StoreKey=s.StoreKey AND a.IsoYearWeek=s.IsoYearWeek;
-- Nie ma joinu FactReturns; wynik nie jest po zwrotach.
-- FactSales grain = transaction line; agregacja przed joinem z korektami chroni ziarno.
