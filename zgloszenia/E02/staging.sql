-- stg.Sales: przyjmuje Status POSTED i pomija pozostałe statusy.
INSERT INTO dbo_FactSales
SELECT SaleDate, StoreCode, TransactionNo, LineNumber, Quantity,
       GrossAmount, DiscountAmount, Status
FROM src_SalesRaw WHERE Status = 'POSTED';
