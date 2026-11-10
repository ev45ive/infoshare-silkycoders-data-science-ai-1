-- Calendar dimension, one row per day.
-- year_week uses ISO-8601 week numbering (the trading calendar of the weekly reports),
-- so iso_year can differ from calendar_year around 1 January.
CREATE TABLE dw.dim_date (
    date_key         integer     NOT NULL, -- yyyymmdd
    full_date        date        NOT NULL,
    calendar_year    smallint    NOT NULL,
    calendar_quarter smallint    NOT NULL,
    calendar_month   smallint    NOT NULL,
    month_name       varchar(20) NOT NULL,
    year_month       varchar(7)  NOT NULL, -- '2026-09'
    iso_year         smallint    NOT NULL,
    iso_week         smallint    NOT NULL,
    year_week        varchar(8)  NOT NULL, -- '2026-W38'
    day_of_week      smallint    NOT NULL, -- 1 = Monday
    day_name         varchar(20) NOT NULL,
    is_weekend       boolean     NOT NULL,
    season           varchar(10) NOT NULL, -- retail season the day belongs to
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
);

CREATE UNIQUE INDEX ux_dim_date_full_date ON dw.dim_date (full_date);
CREATE INDEX ix_dim_date_year_week ON dw.dim_date (year_week);
