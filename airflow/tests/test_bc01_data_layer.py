"""Testy warstwy danych BC-01: kalendarz, panel, flagi braku towaru oraz zgodność z CSV notebooka."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bc01.calendar import store_calendar, trading_sundays
from bc01.data import load_catalog, load_sales
from bc01.panel import build_panel
from bc01.stockouts import detect_stockouts

REPO = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("BC01_DATA_DIR", REPO / "datasets" / "synthetic" / "bc01"))
REF_CSV = REPO / "analizy" / "bc01-prognoza-popytu" / "prognoza-W39-W42-top20.csv"


def test_trading_sundays_2025_known_dates():
    ts = trading_sundays(2025)
    assert pd.Timestamp("2025-01-26") in ts      # ostatnia niedziela stycznia
    assert pd.Timestamp("2025-04-13") in ts      # niedziela przed Wielkanocą (20.04.2025)
    assert pd.Timestamp("2025-12-21") in ts      # niedziela przed Wigilią
    assert len(ts) == 8


def test_store_calendar_closed_on_holiday_and_regular_sunday():
    cal = store_calendar("2025-12-20", "2026-01-05").set_index("date")
    assert not cal.loc["2026-01-01", "store_open"]      # Nowy Rok
    assert not cal.loc["2026-01-04", "store_open"]      # zwykła niedziela
    assert cal.loc["2025-12-21", "store_open"]          # niedziela handlowa


def test_panel_starts_series_and_masks_before_start():
    weeks = pd.date_range("2025-01-06", periods=6, freq="W-MON")
    rows = [
        {"week_start": weeks[2], "model": "A", "store_key": 1, "qty": 5.0},
        {"week_start": weeks[4], "model": "A", "store_key": 1, "qty": 3.0},
    ]
    weekly = pd.DataFrame(rows)
    origin = weeks[-1] + pd.Timedelta(weeks=1)                # 6 tygodni przed origin
    p = build_panel(weekly, origin, models=["A", "B"], store_keys=[1], basic={"B"})
    assert len(p.weeks) == 6
    assert p.start == {"A": 2, "B": 0}
    assert np.isnan(p.y[0, 0]) and np.isnan(p.y[1, 0])        # A przed startem = NaN
    assert p.y[2, 0] == 5.0 and p.y[3, 0] == 0.0               # po starcie brak sprzedaży = 0
    assert p.y[0, 1] == 0.0                                    # BASIC żyje od pierwszego tygodnia


def test_stockout_flag_on_zero_sales_with_high_model_total():
    # Model A ma dwie lokalizacje, udział 50/50 przez 8 tygodni, potem sklep 1 ma zero przy wysokiej sprzedaży modelu.
    Y = np.zeros((11, 2))
    Y[:10] = 10.0
    Y[10] = [0.0, 40.0]
    F, E = detect_stockouts(Y, {"A": np.array([0, 1])}, {"A": 0})
    assert F[10, 0] and not F[10, 1]
    assert E[10, 0] == pytest.approx(40.0)


def test_stockout_not_flagged_when_share_is_consistent():
    Y = np.full((11, 2), 10.0)
    F, _ = detect_stockouts(Y, {"A": np.array([0, 1])}, {"A": 0})
    assert not F.any()


@pytest.mark.skipif(not (DATA / "fact_sales.parquet").exists() or not REF_CSV.exists(),
                    reason="brak danych BC-01 lub CSV referencyjnego")
def test_b1_and_flags_match_notebook_reference_csv():
    origin = pd.Timestamp("2026-09-21")
    cat = load_catalog(DATA)
    sales = load_sales(DATA, origin)
    p = build_panel(sales, origin, cat.models, cat.store_keys, cat.basic)
    F, _ = detect_stockouts(p.y, p.model_cols, p.start)
    T = len(p.weeks)
    got = pd.DataFrame({
        "model": p.series.model,
        "lokalizacja": p.series.store_key.map(cat.store_code),
        "B1_4tyg": 4 * np.nanmean(p.y[T - 4:T], axis=0),
        "podejrzenie_braku_towaru": F[T - 2:T].any(0),
    })
    ref = pd.read_csv(REF_CSV)
    m = ref.merge(got, on=["model", "lokalizacja"], suffixes=("_ref", ""))
    assert len(m) == len(ref) > 0
    # CSV zapisany z round(1) w notebooku -> tolerancja 0,05 szt.
    np.testing.assert_allclose(m["B1_4tyg_ref"], m["B1_4tyg"], rtol=0, atol=0.05)
    assert (m["podejrzenie_braku_towaru_ref"].astype(bool) == m["podejrzenie_braku_towaru"]).all()
