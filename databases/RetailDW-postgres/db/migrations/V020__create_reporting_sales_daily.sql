-- Daily sales, one row per trading day / store / product category.
-- The base view for day-level questions; roll it up on year_month or year_week for longer periods.
CREATE VIEW reporting.sales_daily AS
SELECT  d.full_date                         AS sales_date,
        d.year_month,
        d.year_week,
        st.store_code,
        st.store_name,
        st.channel,
        st.region,
        p.department,
        p.category,
        SUM(f.quantity)                     AS units,
        COUNT(DISTINCT f.transaction_no)    AS transactions,
        SUM(f.gross_amount)                 AS gross_amount,
        SUM(f.discount_amount)              AS discount_amount,
        SUM(f.net_amount)                   AS net_amount,
        SUM(f.quantity * f.unit_cost)       AS cost_amount
FROM    dw.fact_sales   AS f
JOIN    dw.dim_date     AS d  ON d.date_key    = f.date_key
JOIN    dw.dim_store    AS st ON st.store_key  = f.store_key
JOIN    dw.dim_product  AS p  ON p.product_key = f.product_key
GROUP BY d.full_date, d.year_month, d.year_week,
         st.store_code, st.store_name, st.channel, st.region,
         p.department, p.category;
