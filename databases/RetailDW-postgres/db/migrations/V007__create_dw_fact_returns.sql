-- Returns fact. Grain: one row per returned line.
-- return_amount is the refunded amount, VAT included, stored as a positive number.
CREATE TABLE dw.fact_returns (
    return_key     bigint        GENERATED ALWAYS AS IDENTITY,
    date_key       integer       NOT NULL,
    product_key    integer       NOT NULL,
    store_key      integer       NOT NULL,
    return_no      varchar(30)   NOT NULL,
    transaction_no varchar(30)   NOT NULL,
    quantity       integer       NOT NULL,
    return_amount  numeric(12,2) NOT NULL,
    return_reason  varchar(30),
    load_id        integer       NOT NULL,
    CONSTRAINT pk_fact_returns PRIMARY KEY (return_key),
    CONSTRAINT fk_fact_returns_dim_date    FOREIGN KEY (date_key)    REFERENCES dw.dim_date (date_key),
    CONSTRAINT fk_fact_returns_dim_product FOREIGN KEY (product_key) REFERENCES dw.dim_product (product_key),
    CONSTRAINT fk_fact_returns_dim_store   FOREIGN KEY (store_key)   REFERENCES dw.dim_store (store_key)
);

CREATE INDEX ix_fact_returns_date_key
    ON dw.fact_returns (date_key) INCLUDE (product_key, store_key, quantity, return_amount);
