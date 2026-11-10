-- Seeds dw.dim_date: every day from 2024-12-01 to 2026-12-31. No-op when the table already has rows.
-- Month and day names are intentionally ASCII (no Polish diacritics), as in the source model.
INSERT INTO dw.dim_date
    (date_key, full_date, calendar_year, calendar_quarter, calendar_month, month_name, year_month,
     iso_year, iso_week, year_week, day_of_week, day_name, is_weekend, season)
SELECT  to_char(cal.d, 'YYYYMMDD')::integer,
        cal.d,
        cal.y,
        extract(quarter FROM cal.d)::integer,
        cal.m,
        (ARRAY['Styczen', 'Luty', 'Marzec', 'Kwiecien', 'Maj', 'Czerwiec',
               'Lipiec', 'Sierpien', 'Wrzesien', 'Pazdziernik', 'Listopad', 'Grudzien'])[cal.m],
        to_char(cal.d, 'YYYY-MM'),
        extract(isoyear FROM cal.d)::integer,
        extract(week FROM cal.d)::integer,
        to_char(cal.d, 'IYYY') || '-W' || to_char(cal.d, 'IW'),
        cal.dow,
        (ARRAY['Poniedzialek', 'Wtorek', 'Sroda', 'Czwartek', 'Piatek', 'Sobota', 'Niedziela'])[cal.dow],
        cal.dow >= 6,
        -- Retail seasons: spring/summer runs February-July, autumn/winter August-January.
        CASE WHEN cal.m BETWEEN 2 AND 7 THEN 'SS' || lpad((cal.y % 100)::text, 2, '0')
             WHEN cal.m = 1             THEN 'AW' || lpad(((cal.y - 1) % 100)::text, 2, '0')
             ELSE                            'AW' || lpad((cal.y % 100)::text, 2, '0')
        END
FROM (
    SELECT  g.d,
            extract(year FROM g.d)::integer   AS y,
            extract(month FROM g.d)::integer  AS m,
            extract(isodow FROM g.d)::integer AS dow
    FROM    (SELECT date '2024-12-01' + n AS d
             FROM   generate_series(0, date '2026-12-31' - date '2024-12-01') AS n) AS g
) AS cal
WHERE NOT EXISTS (SELECT 1 FROM dw.dim_date);
