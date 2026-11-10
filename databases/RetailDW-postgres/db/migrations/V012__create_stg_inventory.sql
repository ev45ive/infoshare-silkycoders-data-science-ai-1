-- Typed, validated stock levels. Populated by etl.load_inventory() from src.inventory_raw.
CREATE TABLE stg.inventory (
    staging_row_id bigint      GENERATED ALWAYS AS IDENTITY,
    snapshot_date  date        NOT NULL,
    sku            varchar(40) NOT NULL,
    store_code     varchar(20) NOT NULL,
    stock_quantity integer     NOT NULL,
    source_file    varchar(100),
    load_id        integer     NOT NULL,
    CONSTRAINT pk_stg_inventory PRIMARY KEY (staging_row_id)
);

CREATE INDEX ix_stg_inventory_snapshot_date ON stg.inventory (snapshot_date);
