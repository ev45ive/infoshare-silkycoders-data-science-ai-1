/*
    FILE OUT OF SCOPE FOR DATA ANALYSTS

    Generates SYNTHETIC TEST DATA for local development only (infrastructure code).
    Data analysts must not read, reference or analyze this file: treat the landing zone tables
    (src.*) as real data from the source systems.

    ---

    PostgreSQL port of the T-SQL generator. Builds the landing zone (src.*) for the trading
    history covered by this environment. Runs once, on an empty src.sales_raw; on a populated
    database it leaves the data alone. Reproducible: the same run always produces the same data.

    Porting notes:
      - CHECKSUM(...) is replaced by an md5-based hash, so the rows differ from the SQL Server
        output while the distributions, seasonality and planted data quirks are the same.
      - Needs psql (\set, \gset, \if); retaildw.sh seed runs it in a single transaction.
      - Intentional CROSS JOIN over date x store x product: the demand model is evaluated for every
        combination before it is thinned out by the receipts draw.
*/
\set sales_from '2025-01-01'
\set sales_to   '2026-09-20'
\set stock_from '2026-06-01'

SELECT EXISTS (SELECT 1 FROM src.sales_raw) AS populated \gset

\if :populated
    \echo '  [src] already populated, skipping'
\else
    \echo '  preparing [src] data'

    -- Deterministic pseudo-random number in [0, 1) derived from a text key.
    CREATE FUNCTION pg_temp.hash01(p text) RETURNS numeric
    LANGUAGE sql IMMUTABLE
    AS $$ SELECT (('x' || substr(md5(p), 1, 7))::bit(28)::integer % 10000) / 10000.0 $$;

    -- Per-product and per-store weights used by the demand model.
    CREATE TEMP TABLE gen_prod AS
    SELECT  p.sku,
            p.style_code,
            p.category,
            p.size,
            p.list_price,
            CASE p.category
                WHEN 'Kurtki'   THEN 0.55
                WHEN 'Sukienki' THEN 0.85
                WHEN 'Swetry'   THEN 0.75
                WHEN 'Jeansy'   THEN 0.95
                WHEN 'T-shirty' THEN 1.35
                WHEN 'Koszule'  THEN 0.60
                ELSE                 0.70
            END AS base,
            CASE p.size
                WHEN 'XS' THEN 0.08
                WHEN 'S'  THEN 0.22
                WHEN 'M'  THEN 0.30
                WHEN 'L'  THEN 0.28
                WHEN 'XL' THEN 0.12
                ELSE           1.00
            END AS size_share,
            CASE WHEN row_number() OVER (PARTITION BY p.style_code, p.size
                                         ORDER BY p.color COLLATE "C") = 1
                 THEN 0.58 ELSE 0.42
            END AS color_share,
            -- Share of the season's intake still expected on the shelf at the end of the month, by size.
            CASE p.size
                WHEN 'XS' THEN 0.50
                WHEN 'S'  THEN 0.78
                WHEN 'M'  THEN 0.90
                WHEN 'L'  THEN 0.88
                WHEN 'XL' THEN 0.55
                ELSE           0.75
            END AS target_sell_through
    FROM    dw.dim_product AS p;

    CREATE TEMP TABLE gen_store AS
    SELECT  s.store_code,
            s.channel,
            CASE s.store_code
                WHEN 'S-WAW-01' THEN 1.60
                WHEN 'S-WAW-02' THEN 1.00
                WHEN 'S-KRK-01' THEN 0.80
                WHEN 'S-POZ-01' THEN 1.15
                WHEN 'S-GDA-01' THEN 0.90
                ELSE                 1.45
            END AS store_factor
    FROM    dw.dim_store AS s;

    -- One row per store / SKU / day on which at least one receipt contained the SKU.
    -- A line exists on a day when the deterministic draw falls under that day's demand.
    CREATE TEMP TABLE gen_lines AS
    SELECT  d.full_date AS dt,
            d.date_key,
            st.store_code,
            st.channel,
            p.sku,
            p.style_code,
            p.category,
            p.size,
            p.list_price AS unit_price,
            rc.receipts,
            CASE WHEN p.category = 'Sukienki'
                      AND d.full_date BETWEEN '2026-03-02' AND '2026-03-22' THEN 0.30
                 WHEN d.full_date BETWEEN '2025-11-24' AND '2025-11-30'     THEN 0.20
                 ELSE 0.00
            END AS discount_pct
    FROM    dw.dim_date AS d
    CROSS JOIN gen_store AS st
    CROSS JOIN gen_prod  AS p
    CROSS JOIN LATERAL (SELECT pg_temp.hash01(st.store_code || '|' || p.sku || '|' || d.date_key) AS rnd,
                               extract(doy FROM d.full_date)::integer                            AS doy) AS r
    -- Seasonality is a smooth yearly curve per category: peak is the day of year the category
    -- sells best, amp how pronounced the season is.
    CROSS JOIN LATERAL (SELECT CASE p.category
                                   WHEN 'Kurtki'   THEN 345 WHEN 'Swetry'   THEN 340
                                   WHEN 'Sukienki' THEN 185 WHEN 'T-shirty' THEN 195
                                   WHEN 'Koszule'  THEN 300 WHEN 'Jeansy'   THEN 285
                                   ELSE 345 END AS peak,
                               CASE p.category
                                   WHEN 'Kurtki'   THEN 0.85 WHEN 'Swetry'   THEN 0.72
                                   WHEN 'Sukienki' THEN 0.50 WHEN 'T-shirty' THEN 0.55
                                   WHEN 'Koszule'  THEN 0.20 WHEN 'Jeansy'   THEN 0.18
                                   ELSE 0.30 END AS amp) AS sea
    CROSS JOIN LATERAL (SELECT
                p.base * p.size_share * p.color_share * st.store_factor
                -- Day-of-week pattern (1 = Monday): stores peak on Saturday, the online shop on Sunday and Monday.
                * CASE WHEN st.channel = 'ONLINE'
                       THEN (ARRAY[1.10, 1.05, 1.00, 1.00, 0.95, 0.90, 1.15])[d.day_of_week]
                       ELSE (ARRAY[0.75, 0.78, 0.85, 0.95, 1.20, 1.60, 0.95])[d.day_of_week]
                  END
                * (1 + sea.amp * cos(2 * pi() * (r.doy - sea.peak) / 365.0))
                -- Clamp: float8 exp() raises an underflow error far from the peak, T-SQL returns 0.
                * (1 + 0.85 * exp(-least(power(((r.doy - 349) / 11.0)::float8, 2), 700)))
                * CASE WHEN d.full_date BETWEEN '2025-11-24' AND '2025-11-30' THEN 1.90 ELSE 1.00 END
                * (1 + 0.06 * (d.full_date - :'sales_from'::date) / 628.0)
                * CASE WHEN st.store_code = 'S-KRK-01' AND d.full_date >= '2026-04-01' THEN 1.26 ELSE 1.00 END
                * CASE WHEN p.category = 'Sukienki'
                            AND d.full_date BETWEEN '2026-03-02' AND '2026-03-22' THEN 1.55 ELSE 1.00 END
                AS demand) AS m
    -- Turn expected demand into a whole number of receipts. The fractional part decides
    -- probabilistically, so slow sellers appear only on some days while fast sellers keep a
    -- stable daily rate.
    CROSS JOIN LATERAL (SELECT floor(m.demand * 3.6)::integer
                               + CASE WHEN m.demand * 3.6 - floor(m.demand * 3.6) > r.rnd THEN 1 ELSE 0 END
                               AS receipts) AS rc
    WHERE   d.full_date BETWEEN :'sales_from'::date AND :'sales_to'::date
        AND rc.receipts >= 1
        -- Planted stock-out: two jacket styles sold out in M/L in four stores from mid-September.
        AND NOT (p.style_code IN ('W-JKT-001', 'W-JKT-002')
                 AND p.size IN ('M', 'L')
                 AND st.store_code IN ('S-WAW-01', 'S-WAW-02', 'S-POZ-01', 'S-GDA-01')
                 AND d.full_date >= '2026-09-14');

    -- Expand into individual receipt lines (at most 10 per SKU/day) and group them into
    -- receipts of roughly 2.3 lines each.
    CREATE TEMP TABLE gen_baskets AS
    SELECT  b.*,
            'T-' || b.store_code || '-' || to_char(b.dt, 'YYYYMMDD') || '-' || right('0000' || b.basket, 4)
                AS transaction_no
    FROM (
        SELECT  l.dt,
                l.store_code,
                l.channel,
                l.sku,
                l.style_code,
                l.size,
                l.unit_price,
                l.discount_pct,
                1 + CASE WHEN (n.i * 37 + length(l.sku) * 11) % 100 < 18 THEN 1 ELSE 0 END AS quantity,
                (((row_number() OVER w) - 1)::integer * 10) / 23 + 1                       AS basket,
                row_number() OVER w                                                        AS seq
        FROM    gen_lines AS l
        CROSS JOIN LATERAL generate_series(1, least(l.receipts, 10)) AS n (i)
        WINDOW w AS (PARTITION BY l.dt, l.store_code ORDER BY n.i, l.sku COLLATE "C")
    ) AS b;

    INSERT INTO src.sales_raw
        (transaction_no, line_number, sales_date, sku, store_code,
         quantity, unit_price, discount_amount, source_file)
    SELECT  b.transaction_no,
            (row_number() OVER (PARTITION BY b.dt, b.store_code, b.basket ORDER BY b.seq))::text,
            to_char(b.dt, 'YYYY-MM-DD'),
            b.sku,
            b.store_code,
            b.quantity::text,
            b.unit_price::text,
            round(b.quantity * b.unit_price * b.discount_pct, 2)::numeric(10,2)::text,
            CASE WHEN b.channel = 'ONLINE' THEN 'WEB_' ELSE 'POS_' END || to_char(b.dt, 'YYYYMMDD') || '.csv'
    FROM    gen_baskets AS b
    ORDER BY b.dt, b.store_code COLLATE "C", b.basket, b.seq;

    -- Second copy of one day's point-of-sale export.
    INSERT INTO src.sales_raw
        (transaction_no, line_number, sales_date, sku, store_code,
         quantity, unit_price, discount_amount, source_file)
    SELECT  transaction_no, line_number, sales_date, sku, store_code,
            quantity, unit_price, discount_amount,
            'POS_20260817_RETRY.csv'
    FROM    src.sales_raw
    WHERE   sales_date  = '2026-08-17'
        AND source_file = 'POS_20260817.csv'
    ORDER BY raw_id;

    -- Stock feed. Each store takes one delivery for the season and sells it down; the closing
    -- stock of a day is what the feed reports.
    CREATE TEMP TABLE gen_season_units AS
    SELECT  store_code, sku, SUM(quantity) AS units
    FROM    gen_baskets
    WHERE   dt >= :'stock_from'::date
    GROUP BY store_code, sku;

    CREATE TEMP TABLE gen_daily_units AS
    SELECT  dt, store_code, sku, SUM(quantity) AS units
    FROM    gen_baskets
    GROUP BY dt, store_code, sku;

    CREATE INDEX ix_gen_daily_units ON gen_daily_units (store_code, sku, dt);

    CREATE TEMP TABLE gen_allocation AS
    SELECT  su.store_code,
            su.sku,
            GREATEST(ceil(su.units / p.target_sell_through), 3) AS allocation
    FROM    gen_season_units AS su
    JOIN    gen_prod         AS p ON p.sku = su.sku;

    CREATE INDEX ix_gen_allocation ON gen_allocation (store_code, sku);

    INSERT INTO src.inventory_raw
        (snapshot_date, sku, store_code, stock_quantity, source_file)
    SELECT  to_char(g.dt, 'YYYY-MM-DD'),
            g.sku,
            g.store_code,
            GREATEST(g.allocation - g.sold_to_date, 0)::integer::text,
            'WMS_' || to_char(g.dt, 'YYYYMMDD') || '.csv'
    FROM (
        SELECT  d.full_date AS dt,
                st.store_code,
                p.sku,
                CASE WHEN p.style_code IN ('W-JKT-001', 'W-JKT-002')
                          AND p.size IN ('M', 'L')
                          AND st.store_code IN ('S-WAW-01', 'S-WAW-02', 'S-POZ-01', 'S-GDA-01')
                     THEN COALESCE(su.units, 0)
                     ELSE COALESCE(a.allocation, 3)
                END AS allocation,
                SUM(COALESCE(du.units, 0)) OVER (PARTITION BY st.store_code, p.sku
                                                 ORDER BY d.full_date
                                                 ROWS UNBOUNDED PRECEDING) AS sold_to_date
        FROM    dw.dim_date AS d
        CROSS JOIN gen_store AS st
        CROSS JOIN gen_prod  AS p
        LEFT JOIN gen_allocation   AS a  ON a.store_code  = st.store_code AND a.sku  = p.sku
        LEFT JOIN gen_season_units AS su ON su.store_code = st.store_code AND su.sku = p.sku
        LEFT JOIN gen_daily_units  AS du ON du.store_code = st.store_code AND du.sku = p.sku
                                        AND du.dt         = d.full_date
        WHERE   d.full_date BETWEEN :'stock_from'::date AND :'sales_to'::date
            -- Planted gap: this store sent no stock file for three days.
            AND NOT (st.store_code = 'S-POZ-01'
                     AND d.full_date BETWEEN '2026-06-10' AND '2026-06-12')
    ) AS g
    ORDER BY g.dt, g.store_code COLLATE "C", g.sku COLLATE "C";

    -- Returns.
    INSERT INTO src.returns_raw
        (return_no, transaction_no, return_date, sku, store_code,
         quantity, return_amount, return_reason, source_file)
    SELECT  'R-' || to_char(s.return_date, 'YYYYMMDD') || '-'
                 || right('000000' || row_number() OVER (ORDER BY s.return_date,
                                                                  s.transaction_no COLLATE "C",
                                                                  s.sku COLLATE "C"), 6),
            s.transaction_no,
            to_char(s.return_date, 'YYYY-MM-DD'),
            s.sku,
            s.store_code,
            '1',
            s.unit_price::text,
            s.return_reason,
            'RET_' || to_char(s.return_date, 'YYYYMM') || '.csv'
    FROM (
        SELECT  b.transaction_no,
                b.sku,
                b.store_code,
                b.unit_price,
                b.dt + (3 + trunc(rr.rnd * 18)::integer) AS return_date,
                CASE
                    -- One-size items are never sent back for a bad fit.
                    WHEN b.size = 'ONE' THEN
                        CASE WHEN rr.rnd2 < 0.62 THEN 'CHANGED_MIND'
                             WHEN rr.rnd2 < 0.88 THEN 'DAMAGED'
                             ELSE 'OTHER' END
                    WHEN b.channel = 'ONLINE' AND b.style_code = 'W-JNS-003' THEN
                        CASE WHEN rr.rnd2 < 0.70 THEN 'WRONG_SIZE'
                             WHEN rr.rnd2 < 0.88 THEN 'CHANGED_MIND'
                             WHEN rr.rnd2 < 0.95 THEN 'DAMAGED'
                             ELSE 'OTHER' END
                    WHEN b.channel = 'ONLINE' THEN
                        CASE WHEN rr.rnd2 < 0.45 THEN 'WRONG_SIZE'
                             WHEN rr.rnd2 < 0.80 THEN 'CHANGED_MIND'
                             WHEN rr.rnd2 < 0.92 THEN 'DAMAGED'
                             ELSE 'OTHER' END
                    ELSE
                        CASE WHEN rr.rnd2 < 0.45 THEN 'CHANGED_MIND'
                             WHEN rr.rnd2 < 0.70 THEN 'WRONG_SIZE'
                             WHEN rr.rnd2 < 0.90 THEN 'DAMAGED'
                             ELSE 'OTHER' END
                END AS return_reason
        FROM    gen_baskets AS b
        CROSS JOIN LATERAL (SELECT pg_temp.hash01('ret' || b.transaction_no || b.sku) AS rnd,
                                   pg_temp.hash01(b.sku || 'ret' || b.transaction_no) AS rnd2) AS rr
        WHERE   rr.rnd < CASE
                    WHEN b.channel = 'ONLINE' AND b.style_code = 'W-JNS-003' THEN 0.34
                    WHEN b.channel = 'ONLINE'                                THEN 0.18
                    ELSE                                                          0.04
                END
    ) AS s
    WHERE   s.return_date <= :'sales_to'::date
    ORDER BY s.return_date, s.transaction_no COLLATE "C", s.sku COLLATE "C";

    DROP TABLE gen_prod, gen_store, gen_lines, gen_baskets,
               gen_season_units, gen_daily_units, gen_allocation;

    SELECT 'src.sales_raw' AS table_name, count(*) AS row_count FROM src.sales_raw
    UNION ALL
    SELECT 'src.inventory_raw', count(*) FROM src.inventory_raw
    UNION ALL
    SELECT 'src.returns_raw', count(*) FROM src.returns_raw;
\endif
