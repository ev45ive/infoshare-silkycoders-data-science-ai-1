-- Weekly trading numbers by channel, region and category. Weeks follow the ISO-8601 calendar
-- (Monday-Sunday), which is the trading week used in the Monday report.
CREATE VIEW reporting.sales_weekly AS
SELECT  d.iso_year,
        d.iso_week,
        d.year_week,
        MIN(d.full_date)                    AS week_start,
        MAX(d.full_date)                    AS week_end,
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
GROUP BY d.iso_year, d.iso_week, d.year_week,
         st.channel, st.region, p.department, p.category;
