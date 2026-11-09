CREATE TABLE src_SalesRaw (SaleDate TEXT, StoreCode TEXT, TransactionNo TEXT, LineNumber INTEGER, Quantity INTEGER, GrossAmount REAL, DiscountAmount REAL, Status TEXT);
CREATE TABLE dbo_FactSales (SaleDate TEXT, StoreCode TEXT, TransactionNo TEXT, LineNumber INTEGER, Quantity INTEGER, GrossAmount REAL, DiscountAmount REAL, Status TEXT);
