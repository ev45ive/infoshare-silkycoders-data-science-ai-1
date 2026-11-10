-- Product scorecard at SKU level.
-- units_sold_season and sell_through_pct cover the current season only, i.e. the period for which
-- the stock feed has data - sell-through compares what was sold with what is still on the shelf,
-- so both sides have to describe the same intake.
CREATE VIEW reporting.product_performance AS
WITH season_start AS (
    SELECT MIN(date_key) AS date_key FROM dw.fact_inventory_daily
),
stock_now AS (
    SELECT  i.product_key,
            SUM(i.stock_quantity) AS stock_quantity
    FROM    dw.fact_inventory_daily AS i
    WHERE   i.date_key = (SELECT MAX(date_key) FROM dw.fact_inventory_daily)
    GROUP BY i.product_key
),
sold_total AS (
    SELECT  f.product_key,
            SUM(f.quantity)   AS units,
            SUM(f.net_amount) AS net_amount
    FROM    dw.fact_sales AS f
    GROUP BY f.product_key
),
sold_season AS (
    SELECT  f.product_key,
            SUM(f.quantity) AS units
    FROM    dw.fact_sales AS f
    WHERE   f.date_key >= (SELECT date_key FROM season_start)
    GROUP BY f.product_key
),
returned AS (
    SELECT  r.product_key,
            SUM(r.quantity)      AS units,
            SUM(r.return_amount) AS return_amount
    FROM    dw.fact_returns AS r
    GROUP BY r.product_key
)
SELECT  p.sku,
        p.style_code,
        p.style_name,
        p.department,
        p.category,
        p.color,
        p.size,
        p.list_price,
        COALESCE(t.units, 0)            AS units_sold_total,
        COALESCE(t.net_amount, 0)       AS net_revenue_total,
        COALESCE(ss.units, 0)           AS units_sold_season,
        COALESCE(rt.units, 0)           AS units_returned,
        COALESCE(rt.return_amount, 0)   AS return_amount,
        COALESCE(sn.stock_quantity, 0)  AS stock_on_hand,
        CASE WHEN COALESCE(ss.units, 0) + COALESCE(sn.stock_quantity, 0) = 0
             THEN NULL
             ELSE (100.0 * COALESCE(ss.units, 0)
                   / (COALESCE(ss.units, 0) + COALESCE(sn.stock_quantity, 0)))::numeric(5,2)
        END                             AS sell_through_pct
FROM    dw.dim_product AS p
LEFT JOIN sold_total  AS t  ON t.product_key  = p.product_key
LEFT JOIN sold_season AS ss ON ss.product_key = p.product_key
LEFT JOIN returned    AS rt ON rt.product_key = p.product_key
LEFT JOIN stock_now   AS sn ON sn.product_key = p.product_key;
