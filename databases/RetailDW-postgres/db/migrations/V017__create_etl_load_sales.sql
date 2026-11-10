-- Loads sales from the landing zone into the warehouse.
--   Step 1: src.sales_raw -> stg.sales      (type conversion, validation)
--   Step 2: stg.sales     -> dw.fact_sales  (dimension lookup, measures)
-- Full reload: both targets are truncated first, so the procedure can be re-run at any time and
-- always reflects the current content of the landing zone.
--
-- Call it outside an explicit transaction (plain `CALL etl.load_sales();`). The audit row is
-- committed before the work starts, so a failed load still leaves a FAILED entry in etl.load_log.
CREATE PROCEDURE etl.load_sales()
LANGUAGE plpgsql
AS $$
DECLARE
    v_load_id integer;
    v_read    integer;
    v_loaded  integer;
    v_error   text;
BEGIN
    INSERT INTO etl.load_log (package_name) VALUES ('etl.load_sales') RETURNING load_id INTO v_load_id;
    COMMIT;

    BEGIN
        SELECT count(*) INTO v_read FROM src.sales_raw;

        TRUNCATE dw.fact_sales, stg.sales RESTART IDENTITY;

        -- Step 1: convert text to typed columns. A row that cannot be converted is dropped here
        -- and shows up in rows_rejected.
        INSERT INTO stg.sales
            (transaction_no, line_number, sales_date, sku, store_code,
             quantity, unit_price, discount_amount, source_file, load_id)
        SELECT  r.transaction_no,
                c.line_number,
                c.sales_date,
                r.sku,
                r.store_code,
                c.quantity,
                c.unit_price,
                COALESCE(c.discount_amount, 0),
                r.source_file,
                v_load_id
        FROM    src.sales_raw AS r
        JOIN LATERAL (SELECT etl.try_int(r.line_number)        AS line_number,
                             etl.try_date(r.sales_date)        AS sales_date,
                             etl.try_int(r.quantity)           AS quantity,
                             etl.try_numeric(r.unit_price)     AS unit_price,
                             etl.try_numeric(r.discount_amount) AS discount_amount) AS c ON true
        WHERE   r.transaction_no IS NOT NULL
            AND c.line_number    IS NOT NULL
            AND c.sales_date     IS NOT NULL
            AND r.sku            IS NOT NULL
            AND r.store_code     IS NOT NULL
            AND c.quantity       IS NOT NULL
            AND c.unit_price     IS NOT NULL;

        -- Step 2: resolve dimension keys and derive the measures.
        INSERT INTO dw.fact_sales
            (date_key, product_key, store_key, transaction_no, line_number,
             quantity, unit_price, discount_amount, gross_amount, net_amount,
             unit_cost, load_id)
        SELECT  d.date_key,
                p.product_key,
                st.store_key,
                s.transaction_no,
                s.line_number,
                s.quantity,
                s.unit_price,
                s.discount_amount,
                (s.quantity * s.unit_price - s.discount_amount)::numeric(12,2),
                ((s.quantity * s.unit_price - s.discount_amount) / 1.23)::numeric(12,2),
                p.unit_cost,
                v_load_id
        FROM    stg.sales       AS s
        JOIN    dw.dim_date     AS d  ON d.full_date  = s.sales_date
        JOIN    dw.dim_product  AS p  ON p.sku        = s.sku
        JOIN    dw.dim_store    AS st ON st.store_code = s.store_code;

        GET DIAGNOSTICS v_loaded = ROW_COUNT;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
    END;

    -- COMMIT is not allowed inside a block with an EXCEPTION clause, hence the flag.
    IF v_error IS NOT NULL THEN
        UPDATE etl.load_log
        SET    finished_at = now(), status = 'FAILED', error_message = v_error
        WHERE  load_id = v_load_id;
        COMMIT;
        RAISE EXCEPTION 'etl.load_sales failed: %', v_error;
    END IF;

    UPDATE etl.load_log
    SET    finished_at   = now(),
           status        = 'SUCCEEDED',
           rows_read     = v_read,
           rows_loaded   = v_loaded,
           rows_rejected = v_read - v_loaded
    WHERE  load_id = v_load_id;
END
$$;
