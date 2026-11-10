"""Tygodniowa prognoza popytu BC-01 (M2) dla top N modeli: zapis do RetailDW, schemat forecast.

Uruchomienie ręczne z parametrem origin_date (poniedziałek); puste = ostatni poniedziałek do dziś.
Wynik nie ma jeszcze przedziałów p10/p90 (p10 = p90 = prognoza), patrz airflow/HANDOFF.md.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.sdk import dag, get_current_context, task

CONFIG_PATH = os.environ.get("BC01_CONFIG", "/opt/airflow/config/bc01.yaml")
DATA_DIR = os.environ.get("BC01_DATA_DIR", "/opt/airflow/data/bc01")


def _config() -> dict:
    import yaml

    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _origin():
    import pandas as pd

    raw = (get_current_context()["params"].get("origin_date") or "").strip()
    day = pd.Timestamp(raw) if raw else pd.Timestamp(pendulum.now("Europe/Warsaw").date())
    origin = day.normalize() - pd.Timedelta(days=day.day_of_week)
    if raw and origin != day.normalize():
        raise ValueError(f"origin_date musi być poniedziałkiem, dostano {raw}")
    return origin


@dag(
    dag_id="bc01_prognoza_tygodniowa",
    schedule="0 6 * * 1",
    start_date=pendulum.datetime(2026, 1, 5, tz="Europe/Warsaw"),
    catchup=False,
    max_active_runs=1,
    params={"origin_date": ""},
    default_args={"retries": 0, "execution_timeout": timedelta(minutes=30)},
    tags=["bc01", "prognoza"],
)
def bc01_prognoza_tygodniowa():
    @task
    def start_run() -> dict:
        from bc01 import pipeline, store

        cfg, origin = _config(), _origin()
        h_from, h_to = pipeline.horizon_labels(origin)
        conn = store.connect()
        try:
            run_id = store.start_run(conn, origin, h_from, h_to, cfg["config_version"], pipeline.CODE_VERSION,
                                     cfg["promo_assumption"])
        finally:
            conn.close()
        return {"run_id": run_id, "origin": str(origin.date())}

    @task
    def compute(run: dict) -> dict:
        import pandas as pd

        from bc01 import pipeline

        cfg = _config()
        series, weekly = pipeline.compute_forecast(
            Path(DATA_DIR), pd.Timestamp(run["origin"]),
            top_n=cfg["top_n_models"], lookback_weeks=cfg["top_n_lookback_weeks"])
        return {"series": series.to_dict("records"), "weekly": weekly.to_dict("records")}

    @task
    def publish(run: dict, result: dict) -> int:
        import pandas as pd

        from bc01 import store

        conn = store.connect()
        try:
            store.finish_run(conn, run["run_id"], pd.DataFrame(result["series"]), pd.DataFrame(result["weekly"]))
        finally:
            conn.close()
        return len(result["series"])

    @task(trigger_rule="one_failed")
    def mark_failed(run: dict) -> None:
        from airflow.sdk.exceptions import AirflowFailException

        from bc01 import store

        conn = store.connect()
        try:
            store.fail_run(conn, run["run_id"])
        finally:
            conn.close()
        raise AirflowFailException(f"forecast.run {run['run_id']} oznaczony jako failed")  # przebieg DAG ma być failed

    run = start_run()
    result = compute(run)
    published = publish(run, result)
    [result, published] >> mark_failed(run)


bc01_prognoza_tygodniowa()
