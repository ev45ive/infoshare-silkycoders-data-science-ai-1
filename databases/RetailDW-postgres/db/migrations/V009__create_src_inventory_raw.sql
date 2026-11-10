-- Landing zone for the nightly stock feed sent by the warehouse system (WMS).
-- One row per store / SKU / day, holding the closing stock level. Stores send their own files,
-- so a store that does not report simply produces no rows.
CREATE TABLE src.inventory_raw (
    raw_id         bigint         GENERATED ALWAYS AS IDENTITY,
    snapshot_date  varchar(20),
    sku            varchar(40),
    store_code     varchar(20),
    stock_quantity varchar(20),
    source_file    varchar(100),
    extracted_at   timestamptz(3) NOT NULL DEFAULT now(),
    CONSTRAINT pk_inventory_raw PRIMARY KEY (raw_id)
);
