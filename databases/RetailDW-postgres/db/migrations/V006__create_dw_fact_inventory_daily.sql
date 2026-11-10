-- Stock fact. Grain: one row per day / SKU / store, holding the stock level at the close of that
-- trading day.
-- This is a snapshot, not a movement log - two consecutive rows describe two states, and the
-- difference between them is not a transaction.
-- Stock is only collected for the current season; there are no rows for dates before the start
-- of the feed.
CREATE TABLE dw.fact_inventory_daily (
    inventory_key  bigint  GENERATED ALWAYS AS IDENTITY,
    date_key       integer NOT NULL,
    product_key    integer NOT NULL,
    store_key      integer NOT NULL,
    stock_quantity integer NOT NULL,
    load_id        integer NOT NULL,
    CONSTRAINT pk_fact_inventory_daily PRIMARY KEY (inventory_key),
    CONSTRAINT fk_fact_inventory_daily_dim_date    FOREIGN KEY (date_key)    REFERENCES dw.dim_date (date_key),
    CONSTRAINT fk_fact_inventory_daily_dim_product FOREIGN KEY (product_key) REFERENCES dw.dim_product (product_key),
    CONSTRAINT fk_fact_inventory_daily_dim_store   FOREIGN KEY (store_key)   REFERENCES dw.dim_store (store_key)
);

CREATE INDEX ix_fact_inventory_daily_date_key
    ON dw.fact_inventory_daily (date_key) INCLUDE (product_key, store_key, stock_quantity);
