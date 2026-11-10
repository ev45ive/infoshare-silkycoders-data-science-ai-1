-- Loads stock levels from the landing zone into the warehouse.
--   Step 1: src.inventory_raw -> stg.inventory
--   Step 2: stg.inventory     -> dw.fact_inventory_daily
-- Full reload, same pattern (and same CALL rules) as etl.load_sales().
CREATE PROCEDURE etl.load_inventory()
LANGUAGE plpgsql
AS $$
DECLARE
    v_load_id integer;
    v_read    integer;
    v_loaded  integer;
    v_error   text;
BEGIN
    INSERT INTO etl.load_log (package_name) VALUES ('etl.load_inventory') RETURNING load_id INTO v_load_id;
    COMMIT;

    BEGIN
        SELECT count(*) INTO v_read FROM src.inventory_raw;

        TRUNCATE dw.fact_inventory_daily, stg.inventory RESTART IDENTITY;

        INSERT INTO stg.inventory
            (snapshot_date, sku, store_code, stock_quantity, source_file, load_id)
        SELECT  c.snapshot_date,
                r.sku,
                r.store_code,
                c.stock_quantity,
                r.source_file,
                v_load_id
        FROM    src.inventory_raw AS r
        JOIN LATERAL (SELECT etl.try_date(r.snapshot_date)  AS snapshot_date,
                             etl.try_int(r.stock_quantity)  AS stock_quantity) AS c ON true
        WHERE   c.snapshot_date  IS NOT NULL
            AND r.sku            IS NOT NULL
            AND r.store_code     IS NOT NULL
            AND c.stock_quantity IS NOT NULL;

        INSERT INTO dw.fact_inventory_daily
            (date_key, product_key, store_key, stock_quantity, load_id)
        SELECT  d.date_key,
                p.product_key,
                st.store_key,
                i.stock_quantity,
                v_load_id
        FROM    stg.inventory   AS i
        JOIN    dw.dim_date     AS d  ON d.full_date  = i.snapshot_date
        JOIN    dw.dim_product  AS p  ON p.sku        = i.sku
        JOIN    dw.dim_store    AS st ON st.store_code = i.store_code;

        GET DIAGNOSTICS v_loaded = ROW_COUNT;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_error = MESSAGE_TEXT;
    END;

    IF v_error IS NOT NULL THEN
        UPDATE etl.load_log
        SET    finished_at = now(), status = 'FAILED', error_message = v_error
        WHERE  load_id = v_load_id;
        COMMIT;
        RAISE EXCEPTION 'etl.load_inventory failed: %', v_error;
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
