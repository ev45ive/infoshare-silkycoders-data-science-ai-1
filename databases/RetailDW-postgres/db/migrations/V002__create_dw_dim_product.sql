-- Product dimension at SKU grain.
-- A SKU is one size/colour variant of a style, e.g. style W-JKT-001 sold as W-JKT-001-CZA-M.
-- Reporting by "model" groups on style_code; reporting by "product" usually means the SKU.
-- list_price is the current catalogue price including VAT; unit_cost is the landed cost of one unit.
CREATE TABLE dw.dim_product (
    product_key integer       GENERATED ALWAYS AS IDENTITY,
    sku         varchar(40)   NOT NULL,
    style_code  varchar(20)   NOT NULL,
    style_name  varchar(100)  NOT NULL,
    department  varchar(20)   NOT NULL,
    category    varchar(30)   NOT NULL,
    color       varchar(20)   NOT NULL,
    size        varchar(5)    NOT NULL,
    list_price  numeric(10,2) NOT NULL,
    unit_cost   numeric(10,2) NOT NULL,
    is_active   boolean       NOT NULL DEFAULT true,
    CONSTRAINT pk_dim_product PRIMARY KEY (product_key)
);

CREATE UNIQUE INDEX ux_dim_product_sku ON dw.dim_product (sku);
CREATE INDEX ix_dim_product_style_code ON dw.dim_product (style_code) INCLUDE (category, department, size);
