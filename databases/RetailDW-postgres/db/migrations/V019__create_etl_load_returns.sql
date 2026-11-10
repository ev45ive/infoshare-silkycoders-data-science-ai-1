-- Loads customer returns from the landing zone into the warehouse.
--   Step 1: src.returns_raw -> stg.returns
--   Step 2: stg.returns     -> dw.fact_returns
-- Full reload, same pattern (and same CALL rules) as etl.load_sales().
CREATE PROCEDURE etl.load_returns()
LANGUAGE plpgsql
AS $$
DECLARE
    v_load_id integer;
    v_read    integer;
    v_loaded  integer;
    v_error   text;
BEGIN
    INSERT INTO etl.load_log (package_name) VALUES ('etl.load_returns') RETURNING load_id INTO v_load_id;
    COMMIT;

    BEGIN
        SELECT count(*) INTO v_read FROM src.returns_raw;

        TRUNCATE dw.fact_returns, stg.returns RESTART IDENTITY;

        INSERT INTO stg.returns
            (return_no, transaction_no, return_date, sku, store_code,
             quantity, return_amount, return_reason, source_file, load_id)
        SELECT  r.return_no,
                r.transaction_no,
                c.return_date,
                r.sku,
                r.store_code,
                c.quantity,
                c.return_amount,
                r.return_reason,
                r.source_file,
                v_load_id
        FROM    src.returns_raw AS r
        JOIN LATERAL (SELECT etl.try_date(r.return_date)      AS return_date,
                             etl.try_int(r.quantity)          AS quantity,
                             etl.try_numeric(r.return_amount) AS return_amount) AS c ON true
        WHERE   r.return_no      IS NOT NULL
            AND r.transaction_no IS NOT NULL
            AND c.return_date    IS NOT NULL
            AND r.sku            IS NOT NULL
            AND r.store_code     IS NOT NULL
            AND c.quantity       IS NOT NULL
            AND c.return_amount  IS NOT NULL;

        INSERT INTO dw.fact_returns
            (date_key, product_key, store_key, return_no, transaction_no,
             quantity, return_amount, return_reason, load_id)
        SELECT  d.date_key,
                p.product_key,
                st.store_key,
                t.return_no,
                t.transaction_no,
                t.quantity,
                t.return_amount,
                t.return_reason,
                v_load_id
        FROM    stg.returns     AS t
        JOIN    dw.dim_date     AS d  ON d.full_date  = t.return_date
        JOIN    dw.dim_product  AS p  ON p.sku        = t.sku
        JOIN    dw.dim_store    AS st ON st.store_code = t.store_code;

        GET DIAGNOSTICS v_loaded = ROW_COUNT;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
    END;

    IF v_error IS NOT NULL THEN
        UPDATE etl.load_log
        SET    finished_at = now(), status = 'FAILED', error_message = v_error
        WHERE  load_id = v_load_id;
        COMMIT;
        RAISE EXCEPTION 'etl.load_returns failed: %', v_error;
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
