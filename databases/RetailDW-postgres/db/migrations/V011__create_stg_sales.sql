-- Typed, validated sales rows. Populated by etl.load_sales() from src.sales_raw;
-- rows that fail conversion never reach this table.
CREATE TABLE stg.sales (
    staging_row_id  bigint        GENERATED ALWAYS AS IDENTITY,
    transaction_no  varchar(30)   NOT NULL,
    line_number     integer       NOT NULL,
    sales_date      date          NOT NULL,
    sku             varchar(40)   NOT NULL,
    store_code      varchar(20)   NOT NULL,
    quantity        integer       NOT NULL,
    unit_price      numeric(10,2) NOT NULL,
    discount_amount numeric(10,2) NOT NULL,
    source_file     varchar(100),
    load_id         integer       NOT NULL,
    CONSTRAINT pk_stg_sales PRIMARY KEY (staging_row_id)
);

CREATE INDEX ix_stg_sales_sales_date ON stg.sales (sales_date);
