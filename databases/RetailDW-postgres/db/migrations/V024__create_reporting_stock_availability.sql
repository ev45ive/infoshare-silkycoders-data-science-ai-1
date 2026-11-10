-- Stock availability: for a given day, store and category, the share of SKUs that had stock left
-- at the close of trading.
-- Built from the stock feed, so a day only appears for a store that actually reported that day.
--
-- WARNING: this view calculates UNWEIGHTED availability (average per category).
-- If you aggregate it for a whole period, large categories have the same weight as small ones.
-- For example:
--   - Jackets (24% of catalog): 97.5% availability
--   - Dresses (3% of catalog): 100% availability
-- Result from this view: (97.5 + 100) / 2 = 98.75% (unweighted)
--
-- If you need WEIGHTED availability (actual inventory %), query dw.fact_inventory_daily directly:
--   SELECT (100.0 * SUM(CASE WHEN stock_quantity > 0 THEN 1 ELSE 0 END) / COUNT(*))::numeric(5,2)
--   FROM dw.fact_inventory_daily
-- That will give ~99.2% (weighted by catalog size).
-- Always specify which method you used when reporting availability.
CREATE VIEW reporting.stock_availability AS
SELECT  d.full_date     AS snapshot_date,
        d.year_month,
        d.year_week,
        st.store_code,
        st.store_name,
        p.department,
        p.category,
        COUNT(*)                                                    AS sku_count,
        SUM(CASE WHEN i.stock_quantity > 0 THEN 1 ELSE 0 END)       AS sku_in_stock,
        (100.0 * SUM(CASE WHEN i.stock_quantity > 0 THEN 1 ELSE 0 END) / COUNT(*))::numeric(5,2)
                                                                    AS availability_pct,
        SUM(i.stock_quantity)                                       AS stock_quantity
FROM    dw.fact_inventory_daily AS i
JOIN    dw.dim_date             AS d  ON d.date_key    = i.date_key
JOIN    dw.dim_store            AS st ON st.store_key  = i.store_key
JOIN    dw.dim_product          AS p  ON p.product_key = i.product_key
GROUP BY d.full_date, d.year_month, d.year_week,
         st.store_code, st.store_name, p.department, p.category;
