"""Prognoza BC-01 dla jednego originu: M2 + B1 + flagi, top N modeli (port sekcji 5-7 notebooka, bez przedziałów)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from bc01.calendar import week_calendar
from bc01.data import load_catalog, load_model_meta, load_sales, load_weekly_discount
from bc01.features import aggregates, build_context, clean_sales
from bc01.m2 import M2_FEATURES, build_rows, fit_predict
from bc01.panel import FIRST_WEEK, build_panel

# Przedziały p10/p90 nie są jeszcze zaimplementowane: wynik ma p10 = p90 = prognoza (patrz HANDOFF).
CODE_VERSION = "m2-wip-no-intervals"
ONLINE_CODE = "S-ONL-01"
KRK_CODE = "S-KRK-01"
NEW_MODEL_MAX_AGE_WEEKS = 6
LOW_CONFIDENCE_MIN_UNITS = 20


def horizon_labels(origin: pd.Timestamp) -> tuple[str, str]:
    first, last = origin, origin + pd.Timedelta(weeks=3)
    f, l = first.isocalendar(), last.isocalendar()
    return f"{f.year}-W{f.week:02d}", f"{l.year}-W{l.week:02d}"


def compute_forecast(data_dir: Path, origin: pd.Timestamp, top_n: int = 20,
                     lookback_weeks: int = 8) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Zwraca (series, weekly): tabele zgodne z forecast.series_forecast i forecast.weekly_units (bez run_id)."""
    origin = pd.Timestamp(origin).normalize()
    catalog = load_catalog(data_dir)
    meta = load_model_meta(data_dir)
    sales = load_sales(data_dir, origin)

    last_week = origin - pd.Timedelta(weeks=1)
    if sales.empty or sales["week_start"].max() != last_week:
        have = None if sales.empty else sales["week_start"].max().date()
        raise ValueError(f"dane nie sięgają tygodnia przed origin {origin.date()} (ostatni tydzień w danych: {have})")

    p = build_panel(sales, origin, catalog.models, catalog.store_keys, catalog.basic)
    T, S = len(p.weeks), len(p.series)
    code_to_key = {c: k for k, c in catalog.store_code.items()}
    weeks_x = pd.date_range(FIRST_WEEK, periods=T + 5, freq="W-MON")   # + 5 przyszłych tygodni, jak WX w notebooku
    ctx = build_context(p, week_calendar().reindex(weeks_x), meta, load_weekly_discount(data_dir, origin),
                        code_to_key[ONLINE_CODE], code_to_key[KRK_CODE])
    F, _, YI = clean_sales(p)
    MT, CT = aggregates(ctx, YI)
    rows = build_rows(ctx, p.y, F, YI, MT, CT, T)
    pred = fit_predict(rows, T, S, feats=M2_FEATURES)

    ser = p.series.copy()
    models = ser["model"].to_numpy()
    s8 = pd.Series(np.nansum(p.y[T - lookback_weeks:T], axis=0)).groupby(models).sum()
    top = list(s8.nlargest(top_n).index)
    keep = np.isin(models, top)
    if np.isnan(pred[keep]).any():
        raise ValueError("brak prognozy M2 dla części serii z top N")

    start_series = np.array([p.start[m] for m in models])
    total = np.round(pred.sum(1), 2)
    series = pd.DataFrame({
        "style_code": models,
        "location_code": ser["store_key"].map(catalog.store_code).to_numpy(),
        "category": meta.loc[models, "category"].to_numpy(),
        "forecast_units_total": total,
        "p10_units_total": total,
        "p90_units_total": total,
        "baseline_b1_units_total": np.round(4 * np.nanmean(p.y[T - 4:T], axis=0), 2),
        "flag_new_model": (T - start_series) <= NEW_MODEL_MAX_AGE_WEEKS,
        "flag_possible_stockout": F[T - 2:T].any(0),
        "flag_low_confidence": total < LOW_CONFIDENCE_MIN_UNITS,
    })[keep].sort_values(["style_code", "location_code"]).reset_index(drop=True)

    iso = origin + pd.to_timedelta(np.arange(4) * 7, unit="D")
    iso_cal = pd.DatetimeIndex(iso).isocalendar()
    weekly = pd.DataFrame([
        {"style_code": models[c], "location_code": series_loc, "iso_year": int(iso_cal.year.iloc[h]),
         "iso_week": int(iso_cal.week.iloc[h]), "forecast_units": round(float(pred[c, h]), 2)}
        for c, series_loc in zip(np.flatnonzero(keep), ser["store_key"].map(catalog.store_code).to_numpy()[keep])
        for h in range(4)
    ]).sort_values(["style_code", "location_code", "iso_year", "iso_week"]).reset_index(drop=True)
    return series, weekly
