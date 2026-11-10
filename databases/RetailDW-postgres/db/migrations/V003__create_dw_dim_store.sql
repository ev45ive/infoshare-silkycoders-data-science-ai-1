-- Store dimension. Covers physical stores and the online shop, which is modelled as a store
-- so that every sale has a selling location.
-- sales_area_m2 is the current selling floor area (NULL for the online shop). remodel_date is the
-- date of the last floor-area change; the stored area is always the current one, not the one in
-- force on a past trading day.
CREATE TABLE dw.dim_store (
    store_key     integer      GENERATED ALWAYS AS IDENTITY,
    store_code    varchar(20)  NOT NULL,
    store_name    varchar(100) NOT NULL,
    city          varchar(50)  NOT NULL,
    region        varchar(50)  NOT NULL,
    channel       varchar(10)  NOT NULL,
    format        varchar(20)  NOT NULL,
    sales_area_m2 integer,
    opened_date   date         NOT NULL,
    remodel_date  date,
    CONSTRAINT pk_dim_store PRIMARY KEY (store_key),
    CONSTRAINT ck_dim_store_channel CHECK (channel IN ('STORE', 'ONLINE'))
);

CREATE UNIQUE INDEX ux_dim_store_store_code ON dw.dim_store (store_code);
