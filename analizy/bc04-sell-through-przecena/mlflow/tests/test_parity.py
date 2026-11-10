"""Parytet rejestru MLflow z notebookiem (liczby referencyjne z kopii wykonanego notebooka) oraz brak sekretów.

Wymaga działającego serwera (MLFLOW_TRACKING_URI) i wcześniejszych: run_reference.py, log_runs.py.
"""
import json
import os
import sys
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import pytest
from mlflow import MlflowClient

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import bc04_core as core  # noqa: E402
import log_runs  # noqa: E402

REF = HERE / "reference"
URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(URI)
last = json.loads((REF / "last_suite.json").read_text())
client = MlflowClient()
EXP = client.get_experiment_by_name(last["experiment"]).experiment_id
RUNS = {r.data.params["method"]: r for r in client.search_runs([EXP], filter_string=f"tags.suite_id = '{last['suite_id']}'")}
OREF = pd.read_parquet(REF / "ref_O_final.parquet")
TAB6 = pd.read_csv(REF / "ref_tab6.csv").set_index("metoda")


def test_client_equals_server_version():
    r = __import__("requests").get(URI + "/version", timeout=10)
    assert r.text.strip() == mlflow.__version__ == "3.5.0"


def test_one_run_per_method_and_policy():
    assert set(core.METH) <= set(RUNS)
    assert len(RUNS) == len(core.METH) + 4


@pytest.mark.parametrize("m", list(core.METH))
def test_pooled_metrics_equal_notebook_table(m):
    got, ref = RUNS[m].data.metrics, TAB6.loc[m]
    pairs = {"brier": "Brier", "brier_ci90_lo": "Brier 90% od", "brier_ci90_hi": "Brier 90% do", "log_loss": "log loss", "auc": "AUC",
             "ece_5": "ECE (5 przedziałów)", "cost_per_row_tuned": "koszt/wiersz (próg z walidacji)", "cost_tuned_ci90_lo": "koszt od",
             "cost_tuned_ci90_hi": "koszt do", "cost_per_row_theory": "koszt (próg teoretyczny)"}
    for k, col in pairs.items():
        assert got[k] == pytest.approx(ref[col], rel=1e-9, abs=1e-9), (m, k)


@pytest.mark.parametrize("m", list(core.METH))
def test_per_collection_metrics_equal_notebook_oof(m):
    exp = log_runs.fold_metrics(OREF, m, core.TAU)
    got = RUNS[m].data.metrics
    for k, v in exp.items():
        assert got[k] == pytest.approx(v, rel=1e-9, abs=1e-9), (m, k)


def test_no_secrets_in_params_and_tags():
    bad = ("password", "passwd", "secret", "token", "postgresql://", "api_key")
    for r in RUNS.values():
        for k, v in {**r.data.params, **r.data.tags}.items():
            assert not any(b in f"{k}={v}".lower() for b in bad), (r.info.run_name, k)
            assert k not in os.environ
