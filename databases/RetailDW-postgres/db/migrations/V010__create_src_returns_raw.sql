-- Landing zone for customer returns registered in stores and in the online returns portal.
CREATE TABLE src.returns_raw (
    raw_id         bigint         GENERATED ALWAYS AS IDENTITY,
    return_no      varchar(30),
    transaction_no varchar(30),
    return_date    varchar(20),
    sku            varchar(40),
    store_code     varchar(20),
    quantity       varchar(20),
    return_amount  varchar(20),
    return_reason  varchar(30),
    source_file    varchar(100),
    extracted_at   timestamptz(3) NOT NULL DEFAULT now(),
    CONSTRAINT pk_returns_raw PRIMARY KEY (raw_id)
);
