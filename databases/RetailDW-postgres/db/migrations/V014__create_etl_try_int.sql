-- Replacement for T-SQL TRY_CAST(... AS INT): NULL instead of an error. Regex-guarded
-- (no exception block), so it stays fast on hundreds of thousands of rows.
CREATE FUNCTION etl.try_int(p text) RETURNS integer
LANGUAGE sql IMMUTABLE PARALLEL SAFE
AS $$
    SELECT CASE WHEN btrim(p) ~ '^[+-]?[0-9]{1,9}$' THEN btrim(p)::integer END
$$;
