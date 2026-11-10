-- Forecast results for BC-01 (weekly demand, model M2), written by the Airflow DAG.
-- series_forecast holds the 4-week totals per style x location, weekly_units the weekly split.
CREATE SCHEMA IF NOT EXISTS forecast AUTHORIZATION retaildw;

CREATE TABLE forecast.run (
    run_id          bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at      timestamptz NOT NULL DEFAULT now(),
    finished_at     timestamptz,
    origin_date     date        NOT NULL,
    as_of_date      date        NOT NULL,
    horizon_from    text        NOT NULL,
    horizon_to      text        NOT NULL,
    config_version  text        NOT NULL,
    code_version    text        NOT NULL,
    promo_assumption text       NOT NULL,
    status          text        NOT NULL CHECK (status IN ('running', 'ok', 'failed')),
    CHECK (as_of_date < origin_date)
);

CREATE TABLE forecast.series_forecast (
    run_id                  bigint       NOT NULL REFERENCES forecast.run (run_id),
    style_code              text         NOT NULL,
    location_code           text         NOT NULL,
    category                text         NOT NULL,
    model                   text         NOT NULL,
    forecast_units_total    numeric(10,2) NOT NULL,
    p10_units_total         numeric(10,2) NOT NULL,
    p90_units_total         numeric(10,2) NOT NULL,
    baseline_b1_units_total numeric(10,2) NOT NULL,
    flag_new_model          boolean      NOT NULL,
    flag_possible_stockout  boolean      NOT NULL,
    flag_low_confidence     boolean      NOT NULL,
    PRIMARY KEY (run_id, style_code, location_code),
    CHECK (p10_units_total <= forecast_units_total AND forecast_units_total <= p90_units_total)
);

CREATE TABLE forecast.weekly_units (
    run_id          bigint        NOT NULL REFERENCES forecast.run (run_id),
    style_code      text          NOT NULL,
    location_code   text          NOT NULL,
    iso_year        smallint      NOT NULL,
    iso_week        smallint      NOT NULL CHECK (iso_week BETWEEN 1 AND 53),
    forecast_units  numeric(10,2) NOT NULL,
    PRIMARY KEY (run_id, style_code, location_code, iso_year, iso_week)
);

GRANT USAGE ON SCHEMA forecast TO retaildw_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA forecast TO retaildw_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE retaildw IN SCHEMA forecast
    GRANT SELECT ON TABLES TO retaildw_ro;
