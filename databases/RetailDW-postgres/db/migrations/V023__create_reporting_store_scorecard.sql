-- Monthly store scorecard: the productivity measures the area managers get every month -
-- revenue, average basket, units per transaction and revenue per square metre.
CREATE VIEW reporting.store_scorecard AS
SELECT  st.store_code,
        st.store_name,
        st.city,
        st.region,
        st.channel,
        st.format,
        st.sales_area_m2,
        d.year_month,
        SUM(f.net_amount)                                   AS net_revenue,
        SUM(f.quantity)                                     AS units,
        COUNT(DISTINCT f.transaction_no)                    AS transactions,
        (SUM(f.net_amount) / COUNT(DISTINCT f.transaction_no))::numeric(10,2)
                                                            AS avg_basket_value,
        (1.0 * SUM(f.quantity) / COUNT(DISTINCT f.transaction_no))::numeric(10,2)
                                                            AS units_per_transaction,
        (SUM(f.net_amount) / st.sales_area_m2)::numeric(10,2)
                                                            AS net_revenue_per_m2
FROM    dw.fact_sales AS f
JOIN    dw.dim_store  AS st ON st.store_key = f.store_key
JOIN    dw.dim_date   AS d  ON d.date_key   = f.date_key
WHERE   st.sales_area_m2 > 0
GROUP BY st.store_code, st.store_name, st.city, st.region, st.channel,
         st.format, st.sales_area_m2, d.year_month;
