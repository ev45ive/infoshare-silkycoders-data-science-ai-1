-- Replacement for T-SQL TRY_CAST(... AS DATE). Accepts only ISO yyyy-mm-dd and returns NULL for
-- anything else, including impossible days such as 2026-02-30.
CREATE FUNCTION etl.try_date(p text) RETURNS date
LANGUAGE sql IMMUTABLE PARALLEL SAFE
AS $$
    SELECT CASE
             WHEN m.g IS NULL THEN NULL
             WHEN m.g[3]::integer > extract(day FROM make_date(m.g[1]::integer, m.g[2]::integer, 1)
                                                      + interval '1 month' - interval '1 day')::integer
                  THEN NULL
             ELSE make_date(m.g[1]::integer, m.g[2]::integer, m.g[3]::integer)
           END
    FROM (SELECT regexp_match(btrim(p),
                  '^([1-9][0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$') AS g) AS m
$$;
