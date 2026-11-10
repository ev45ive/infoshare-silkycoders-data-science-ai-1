"""Testy M1 (ETS) BC-01: syntetyczne oraz zgodność z cache notebooka (pomijane bez danych)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bc01.calendar import week_calendar
from bc01.data import load_catalog, load_model_meta, load_sales
from bc01.features import clean_sales
from bc01.m1 import forecast_m1, season_index
from bc01.panel import build_panel

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "datasets" / "synthetic" / "bc01"
CACHE = REPO / "analizy" / "bc01-prognoza-popytu" / "cache" / "m1_forecasts_v1.npz"
ONLINE_KEY = 6
ORIG_DATES = list(pd.date_range("2026-01-05", "2026-08-17", freq="14D")) + [pd.Timestamp("2026-08-24")]
WX = pd.date_range("2025-01-06", "2026-10-19", freq="W-MON")


def test_season_index_shape_and_last_week_repeated():
    n_w = len(WX)
    rng = np.random.default_rng(0)
    yd = rng.uniform(1, 5, (n_w, 4))
    cat = np.array([0, 0, 1, 1])                 # wszystkie kombinacje kategoria x grupa
    grp = np.array([0, 1, 0, 1])
    ix = season_index(yd, WX[:n_w], cat, grp, n_cat=2)
    assert ix.shape == (54, 2, 2)
    np.testing.assert_array_equal(ix[53], ix[52])
    assert (ix[1:] >= 0.05).all()


def test_forecast_m1_flags_short_history_and_is_finite():
    n = 60
    weeks = pd.date_range("2025-01-06", periods=n + 4, freq="W-MON")
    rng = np.random.default_rng(1)
    yi = rng.uniform(5, 15, (n, 2))
    od = np.full((n + 4, 2), 5.0)
    isow = weeks.isocalendar().week.to_numpy().astype(int)
    cat = np.array([0, 0])
    grp = np.array([0, 0])
    start = np.array([0, 50])
    idxs = np.ones((54, 1, 2))
    P, fb = forecast_m1(55, yi, od, isow, cat, grp, start, idxs)
    assert P.shape == (2, 4)
    assert fb.tolist() == [False, True]
    assert np.isfinite(P).all() and (P >= 0).all()


@pytest.mark.skipif(not (DATA / "fact_sales.parquet").exists() or not CACHE.exists(),
                    reason="brak danych BC-01 lub cache M1 z notebooka")
def test_m1_matches_notebook_cache():
    origin = pd.Timestamp("2026-09-21")
    catalog = load_catalog(DATA)
    meta = load_model_meta(DATA)
    p = build_panel(load_sales(DATA, origin), origin, catalog.models, catalog.store_keys, catalog.basic)
    T = len(p.weeks)
    series = p.series
    is_online = (series.store_key == ONLINE_KEY).to_numpy()
    cal = week_calendar().reindex(WX)
    OD = np.where(is_online[None, :], 7.0, cal.store_open_days.to_numpy(float)[:, None])
    cat_codes = {c: i for i, c in enumerate(sorted(meta.category.unique()))}
    cat = series.model.map(meta.category).map(cat_codes).to_numpy()
    grp = is_online.astype(int)
    START = np.array([p.start[m] for m in series.model])
    isow = WX.isocalendar().week.to_numpy().astype(int)
    yi = clean_sales(p)[2]
    idxs = season_index(p.y / OD[:T], p.weeks, cat, grp, len(cat_codes))

    orig = np.array([int(np.where(WX == d)[0][0]) for d in ORIG_DATES])
    out = [forecast_m1(o, yi, OD, isow, cat, grp, START, idxs) for o in orig]
    P = np.stack([x[0] for x in out])
    FB = np.stack([x[1] for x in out])

    z = np.load(CACHE)
    np.testing.assert_allclose(P, z["P"], rtol=1e-6, atol=1e-6, equal_nan=True)
    np.testing.assert_array_equal(FB, z["FB"])
