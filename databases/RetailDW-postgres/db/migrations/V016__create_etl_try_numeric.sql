-- Replacement for T-SQL TRY_CAST(... AS DECIMAL(10, 2)): NULL for non-numeric text or values that
-- would not fit (more than 8 integer digits). Rounding to 2 decimals happens on assignment
-- to the target numeric(10,2) column.
CREATE FUNCTION etl.try_numeric(p text) RETURNS numeric
LANGUAGE sql IMMUTABLE PARALLEL SAFE
AS $$
    SELECT CASE WHEN btrim(p) ~ '^[+-]?[0-9]{1,8}(\.[0-9]+)?$' THEN btrim(p)::numeric END
$$;
