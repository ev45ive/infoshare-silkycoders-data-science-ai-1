-- Landing zone for the daily POS / e-commerce sales extract.
-- Every column arrives as text exactly as the source system wrote it. Nothing is validated
-- here - conversion and validation happen in etl.load_sales().
CREATE TABLE src.sales_raw (
    raw_id          bigint         GENERATED ALWAYS AS IDENTITY,
    transaction_no  varchar(30),
    line_number     varchar(10),
    sales_date      varchar(20),
    sku             varchar(40),
    store_code      varchar(20),
    quantity        varchar(20),
    unit_price      varchar(20),
    discount_amount varchar(20),
    source_file     varchar(100),
    extracted_at    timestamptz(3) NOT NULL DEFAULT now(),
    CONSTRAINT pk_sales_raw PRIMARY KEY (raw_id)
);

CREATE INDEX ix_sales_raw_source_file ON src.sales_raw (source_file);
