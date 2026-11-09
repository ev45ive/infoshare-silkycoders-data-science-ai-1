CREATE VIEW reporting_WeeklySales AS
SELECT StoreCode, SUM(GrossAmount - DiscountAmount) / 1.23 AS NetSales
FROM dbo_FactSales WHERE Status='POSTED' GROUP BY StoreCode;
