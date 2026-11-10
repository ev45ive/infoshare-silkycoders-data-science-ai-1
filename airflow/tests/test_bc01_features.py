"""Testy warstwy cech BC-01: czyszczenie braku towaru i brak wycieku danych z przyszłości (syntetyczne dane)."""

import numpy as np
import pandas as pd
import pytest

from bc01.calendar import week_calendar
from bc01.features import GROUPS, aggregates, build_context, clean_sales, feature_rows
from bc01.panel import FIRST_WEEK, build_panel

ONLINE, KRK = 6, 3
STORES = [1, 2, 3, ONLINE]
MODELS = ["A", "B", "C"]
BASIC = {"B"}
META = pd.DataFrame(
    {"category": ["K1", "K1", "K2"], "collection": ["SS25", "BASIC", "AW25"],
     "launch": ["2025-01-06", "2025-01-06", "2025-03-03"]},
    index=pd.Index(MODELS, name="model"),
)
N_WEEKS = 30
T_ORIGIN = 20


def make_weekly(seed=1, stockout=True):
    rng = np.random.default_rng(seed)
    weeks = pd.date_range(FIRST_WEEK, periods=N_WEEKS, freq="W-MON")
    rows = []
    for m in MODELS:
        for s in STORES:
            qty = rng.poisson(20, N_WEEKS).astype(float)
            if m == "C":
                qty[:10] = 0.0                                  # późny start serii
            if stockout and m == "A" and s == 1:
                qty[T_ORIGIN:T_ORIGIN + 4] = 0.0                  # zero w tygodniach 20–23 mimo popytu innych sklepów
            for w, q in zip(weeks, qty):
                rows.append({"week_start": w, "model": m, "store_key": s, "qty": q})
    return pd.DataFrame(rows)


def build_all(weekly):
    weeks = pd.date_range(FIRST_WEEK, periods=N_WEEKS, freq="W-MON")
    origin = weeks[-1] + pd.Timedelta(weeks=1)
    panel = build_panel(weekly, origin, MODELS, STORES, BASIC)
    WX = pd.date_range(FIRST_WEEK, periods=len(panel.weeks) + 4, freq="W-MON")
    cal = week_calendar().reindex(WX)
    disc = pd.DataFrame(0.0, index=panel.weeks, columns=MODELS)
    ctx = build_context(panel, cal, META, disc, online_key=ONLINE, krk_key=KRK)
    F, E, YI = clean_sales(panel)
    MT, CT = aggregates(ctx, YI)
    return panel, ctx, F, E, YI, MT, CT


def test_clean_sales_replaces_only_flagged_weeks():
    panel, ctx, F, E, YI, MT, CT = build_all(make_weekly())
    col = panel.series.index[(panel.series.model == "A") & (panel.series.store_key == 1)][0]
    assert F[T_ORIGIN:T_ORIGIN + 4, col].all()
    np.testing.assert_allclose(YI[F], E[F])
    keep = ~F & ~np.isnan(panel.y)
    np.testing.assert_array_equal(YI[keep], panel.y[keep])


def test_aggregates_sum_series_and_respect_start():
    panel, ctx, F, E, YI, MT, CT = build_all(make_weekly(stockout=False))
    ix_c = panel.model_cols["C"]
    assert np.isnan(MT[:panel.start["C"], ix_c]).all()
    t = 15
    np.testing.assert_allclose(MT[t, panel.model_cols["A"]], np.nansum(YI[t, panel.model_cols["A"]]))


def test_feature_rows_have_expected_shape_and_groups():
    panel, ctx, F, E, YI, MT, CT = build_all(make_weekly())
    rows = feature_rows(ctx, T_ORIGIN, panel.y, F, YI, MT, CT)
    cols = {c for g in GROUPS.values() for c in g}
    assert cols.issubset(rows.columns)
    assert sorted(rows.h.unique()) == [1, 2, 3, 4]
    assert len(rows) == 4 * int((ctx.START <= T_ORIGIN - 1).sum())


def test_features_do_not_use_weeks_at_or_after_origin():
    weekly = make_weekly()
    panel1, ctx1, F1, _, YI1, MT1, CT1 = build_all(weekly)
    r1 = feature_rows(ctx1, T_ORIGIN, panel1.y, F1, YI1, MT1, CT1)

    changed = weekly.copy()
    future = changed.week_start >= pd.Timestamp(FIRST_WEEK) + pd.Timedelta(weeks=T_ORIGIN)
    rng = np.random.default_rng(99)
    changed.loc[future, "qty"] = rng.poisson(200, future.sum()).astype(float)
    panel2, ctx2, F2, _, YI2, MT2, CT2 = build_all(changed)
    r2 = feature_rows(ctx2, T_ORIGIN, panel2.y, F2, YI2, MT2, CT2)

    feature_cols = [c for c in r1.columns if c not in ("y", "flag_tw")]
    pd.testing.assert_frame_equal(r1[feature_cols], r2[feature_cols])
