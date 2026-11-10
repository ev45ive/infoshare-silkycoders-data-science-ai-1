"""Kontrakt modelu zarejestrowanego pod aliasem @kandydat. Ramki w testach są zbudowane ręcznie („test”): nie mówią nic o jakości modelu."""
import os
import sys
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
import bc04_core as core  # noqa: E402
import log_runs  # noqa: E402

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
MODEL = mlflow.pyfunc.load_model("models:/bc04-sell-through-risk@kandydat")
FE = ["pred55", "st_d", "trend", "avail_core", "restock", "ln_price", "k"]
D = core.build_dataset(log_runs.DATA, HERE / "cache").D


def row(**kw):  # test: wartości typowe dla uczenia, nadpisywane per przypadek
    base = {"pred55": 0.6, "st_d": 0.3, "trend": 0.0, "avail_core": 1.0, "restock": 0.0, "ln_price": float(D.ln_price.median()), "k": 4}
    return pd.DataFrame([{**base, **kw}])


def test_parity_with_model_fit_on_same_data():
    ref = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)).fit(D[FE], core.label(D, core.TAU))
    out = MODEL.predict(D[FE].head(60))
    ok = out.status == "ok"
    assert ok.all()
    np.testing.assert_allclose(out.p_risk.to_numpy(), ref.predict_proba(D[FE].head(60))[:, 1], atol=1e-9)


def test_column_order_does_not_matter():
    a, b = row(), row()[FE[::-1]]
    assert MODEL.predict(a).p_risk[0] == pytest.approx(MODEL.predict(b).p_risk[0])


def test_missing_column_raises():
    with pytest.raises(Exception, match="(?i)missing|brak"):
        MODEL.predict(row().drop(columns=["trend"]))


@pytest.mark.parametrize("k", [1, 8, 20])
def test_age_outside_validated_range_is_refused(k):
    out = MODEL.predict(row(k=k))
    assert np.isnan(out.p_risk[0]) and out.status[0].startswith("poza zakresem") and f"k={k}" in out.status[0]


def test_value_outside_unit_interval_raises():
    with pytest.raises(Exception, match="przedziałem"):
        MODEL.predict(row(st_d=1.5))


def test_feature_outside_training_range_is_refused():
    out = MODEL.predict(row(ln_price=12.0))
    assert np.isnan(out.p_risk[0]) and "ln_price" in out.status[0]
