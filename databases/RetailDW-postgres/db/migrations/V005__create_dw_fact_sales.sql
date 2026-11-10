-- Sales fact. Grain: one row per sold line of a transaction (one SKU within one receipt).
-- gross_amount = quantity * unit_price - discount_amount, VAT included.
-- net_amount   = gross_amount / 1.23, VAT excluded.
-- unit_cost is copied from the product dimension at load time so that margin can be
-- recalculated without re-joining the dimension.
CREATE TABLE dw.fact_sales (
    sales_key       bigint        GENERATED ALWAYS AS IDENTITY,
    date_key        integer       NOT NULL,
    product_key     integer       NOT NULL,
    store_key       integer       NOT NULL,
    transaction_no  varchar(30)   NOT NULL,
    line_number     integer       NOT NULL,
    quantity        integer       NOT NULL,
    unit_price      numeric(10,2) NOT NULL,
    discount_amount numeric(10,2) NOT NULL,
    gross_amount    numeric(12,2) NOT NULL,
    net_amount      numeric(12,2) NOT NULL,
    unit_cost       numeric(10,2) NOT NULL,
    load_id         integer       NOT NULL,
    CONSTRAINT pk_fact_sales PRIMARY KEY (sales_key),
    CONSTRAINT fk_fact_sales_dim_date    FOREIGN KEY (date_key)    REFERENCES dw.dim_date (date_key),
    CONSTRAINT fk_fact_sales_dim_product FOREIGN KEY (product_key) REFERENCES dw.dim_product (product_key),
    CONSTRAINT fk_fact_sales_dim_store   FOREIGN KEY (store_key)   REFERENCES dw.dim_store (store_key)
);

CREATE INDEX ix_fact_sales_date_key
    ON dw.fact_sales (date_key) INCLUDE (product_key, store_key, quantity, gross_amount, net_amount);
CREATE INDEX ix_fact_sales_product_key ON dw.fact_sales (product_key);
