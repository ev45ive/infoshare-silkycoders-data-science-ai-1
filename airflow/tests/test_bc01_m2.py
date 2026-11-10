"""Testy M2 (LightGBM) BC-01: syntetyczne oraz zgodność z cache notebooka (pomijane bez danych)."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("lightgbm")

from bc01.calendar import week_calendar  # noqa: E402
from bc01.data import load_catalog, load_model_meta, load_sales, load_weekly_discount  # noqa: E402
from bc01.features import aggregates, build_context, clean_sales  # noqa: E402
from bc01.m2 import M2_FEATURES, M2_PARAMS, build_rows, fit_predict  # noqa: E402
from bc01.panel import build_panel  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "datasets" / "synthetic" / "bc01"
CACHE = REPO / "analizy" / "bc01-prognoza-popytu" / "cache" / "m2_runs_v1.pkl"
ONLINE_KEY = 6
KRK_KEY = 3
ORIG_DATES = list(pd.date_range("2026-01-05", "2026-08-17", freq="14D")) + [pd.Timestamp("2026-08-24")]
WX = pd.date_range("2025-01-06", "2026-10-19", freq="W-MON")


SYN_FEATS = ["h", "cat", "feat_x"]
SYN_PARAMS = dict(M2_PARAMS, n_estimators=20)


def _synthetic_rows() -> pd.DataFrame:
    """Dwie serie (c = 0, 1), origin t = 10; wiersze t = 4..11, y znane tylko dla tw <= 9."""
    rng = np.random.default_rng(3)
    rows = []
    for t in range(4, 12):
        for c in (0, 1):
            for h in (1, 2, 3, 4):
                tw = t + h - 1
                y = float(rng.integers(0, 20)) if tw <= 9 else np.nan
                rows.append(dict(t=t, h=h, tw=tw, c=c, cat=c, y=y, flag_tw=False,
                                 feat_x=float(rng.normal())))
    return pd.DataFrame(rows)


def test_fit_predict_shape_and_fills_origin_rows():
    rows = _synthetic_rows()
    out = fit_predict(rows, origin_t=10, n_series=2, feats=SYN_FEATS, params=SYN_PARAMS)
    assert out.shape == (2, 4)
    assert np.isfinite(out).all()


def test_fit_predict_ignores_future_targets():
    rows = _synthetic_rows()
    base = fit_predict(rows, origin_t=10, n_series=2, feats=SYN_FEATS, params=SYN_PARAMS)
    tampered = rows.copy()
    future = tampered.tw >= 10                  # cele z przyszłości nie mogą wejść do treningu
    tampered.loc[future, "y"] = 1e6
    again = fit_predict(tampered, origin_t=10, n_series=2, feats=SYN_FEATS, params=SYN_PARAMS)
    np.testing.assert_allclose(base, again, equal_nan=True)


def test_fit_predict_ignores_flagged_training_targets():
    rows = _synthetic_rows()
    rows.loc[(rows.tw == 6), "flag_tw"] = True  # tydzień z brakiem towaru
    base = fit_predict(rows, origin_t=10, n_series=2, feats=SYN_FEATS, params=SYN_PARAMS)
    tampered = rows.copy()
    tampered.loc[tampered.tw == 6, "y"] = 1e6
    again = fit_predict(tampered, origin_t=10, n_series=2, feats=SYN_FEATS, params=SYN_PARAMS)
    np.testing.assert_allclose(base, again, equal_nan=True)


@pytest.mark.skipif(not (DATA / "fact_sales.parquet").exists() or not CACHE.exists(),
                    reason="brak danych BC-01 lub cache M2 z notebooka")
def test_m2_matches_notebook_cache():
    origin = pd.Timestamp("2026-09-21")
    catalog = load_catalog(DATA)
    meta = load_model_meta(DATA)
    p = build_panel(load_sales(DATA, origin), origin, catalog.models, catalog.store_keys, catalog.basic)
    T = len(p.weeks)
    cal = week_calendar().reindex(WX)
    disc = load_weekly_discount(DATA, origin)
    ctx = build_context(p, cal, meta, disc, ONLINE_KEY, KRK_KEY)
    F, E, YI = clean_sales(p)
    MT, CT = aggregates(ctx, YI)
    rows = build_rows(ctx, p.y, F, YI, MT, CT, T)
    orig = [int(np.where(WX == d)[0][0]) for d in ORIG_DATES]
    S = len(p.series)

    cache = pickle.loads(CACHE.read_bytes())
    keys = [k for k in cache if list(k[0]) == list(M2_FEATURES) and dict(k[1]) == M2_PARAMS]
    assert len(keys) == 1, "w cache brak klucza z zamrożoną konfiguracją M2"
    ref = cache[keys[0]]

    mine = np.stack([fit_predict(rows, o, S) for o in orig])
    ref_arr = np.stack([ref[i] for i in range(len(orig))])
    np.testing.assert_allclose(mine, ref_arr, rtol=1e-6, atol=1e-6, equal_nan=True)
