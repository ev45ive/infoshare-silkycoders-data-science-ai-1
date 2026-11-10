-- Margin by style and month, calculated from the sold lines.
-- Used by the merchandising margin review.
CREATE VIEW reporting.margin_analysis AS
SELECT  d.year_month,
        p.style_code,
        p.style_name,
        p.department,
        p.category,
        SUM(f.quantity)                     AS units,
        SUM(f.net_amount)                   AS net_revenue,
        SUM(f.quantity * f.unit_cost)       AS cost_amount,
        SUM(f.net_amount) - SUM(f.quantity * f.unit_cost) AS gross_margin,
        CASE WHEN SUM(f.net_amount) = 0 THEN NULL
             ELSE (100.0 * (SUM(f.net_amount) - SUM(f.quantity * f.unit_cost))
                   / SUM(f.net_amount))::numeric(5,2)
        END                                 AS gross_margin_pct
FROM    dw.fact_sales   AS f
JOIN    dw.dim_date     AS d ON d.date_key    = f.date_key
JOIN    dw.dim_product  AS p ON p.product_key = f.product_key
GROUP BY d.year_month, p.style_code, p.style_name, p.department, p.category;
