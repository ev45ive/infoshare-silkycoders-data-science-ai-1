"""Zapis wyniku prognozy BC-01 do schematu forecast w RetailDW (rola airflow: SELECT, INSERT, UPDATE)."""

from __future__ import annotations

import os

import pandas as pd

SERIES_COLUMNS = ["style_code", "location_code", "category", "forecast_units_total", "p10_units_total",
                  "p90_units_total", "baseline_b1_units_total", "flag_new_model", "flag_possible_stockout",
                  "flag_low_confidence"]
WEEKLY_COLUMNS = ["style_code", "location_code", "iso_year", "iso_week", "forecast_units"]


def connect():
    """Połączenie z RetailDW; hasło tylko ze zmiennej środowiskowej (BC01_DB_PASSWORD), nigdy z argumentów."""
    import psycopg2

    return psycopg2.connect(host=os.environ.get("BC01_DB_HOST", "postgres"), port=5432,
                            dbname=os.environ.get("BC01_DB_NAME", "retaildw"),
                            user=os.environ.get("BC01_DB_USER", "airflow"),
                            password=os.environ["BC01_DB_PASSWORD"])


def start_run(conn, origin: pd.Timestamp, horizon_from: str, horizon_to: str, config_version: str,
              code_version: str, promo_assumption: str) -> int:
    with conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO forecast.run (origin_date, as_of_date, horizon_from, horizon_to, config_version,
                                         code_version, promo_assumption, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'running') RETURNING run_id""",
            (origin.date(), (origin - pd.Timedelta(days=1)).date(), horizon_from, horizon_to,
             str(config_version), code_version, promo_assumption))
        return cur.fetchone()[0]


def finish_run(conn, run_id: int, series: pd.DataFrame, weekly: pd.DataFrame) -> None:
    """Wyniki i status 'ok' w jednej transakcji."""
    from psycopg2.extras import execute_values

    def rows(df: pd.DataFrame, cols: list[str]):
        return [(run_id, *(v.item() if hasattr(v, "item") else v for v in r)) for r in df[cols].itertuples(index=False)]

    with conn, conn.cursor() as cur:
        execute_values(cur, f"INSERT INTO forecast.series_forecast (run_id, {', '.join(SERIES_COLUMNS)}, model) VALUES %s",
                       [r + ("M2",) for r in rows(series, SERIES_COLUMNS)])
        execute_values(cur, f"INSERT INTO forecast.weekly_units (run_id, {', '.join(WEEKLY_COLUMNS)}) VALUES %s",
                       rows(weekly, WEEKLY_COLUMNS))
        cur.execute("UPDATE forecast.run SET status = 'ok', finished_at = now() WHERE run_id = %s", (run_id,))


def fail_run(conn, run_id: int) -> None:
    with conn, conn.cursor() as cur:
        cur.execute("UPDATE forecast.run SET status = 'failed', finished_at = now() WHERE run_id = %s", (run_id,))
