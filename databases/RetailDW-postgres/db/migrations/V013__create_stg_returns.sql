-- Typed, validated returns. Populated by etl.load_returns() from src.returns_raw.
CREATE TABLE stg.returns (
    staging_row_id bigint        GENERATED ALWAYS AS IDENTITY,
    return_no      varchar(30)   NOT NULL,
    transaction_no varchar(30)   NOT NULL,
    return_date    date          NOT NULL,
    sku            varchar(40)   NOT NULL,
    store_code     varchar(20)   NOT NULL,
    quantity       integer       NOT NULL,
    return_amount  numeric(10,2) NOT NULL,
    return_reason  varchar(30),
    source_file    varchar(100),
    load_id        integer       NOT NULL,
    CONSTRAINT pk_stg_returns PRIMARY KEY (staging_row_id)
);
