"""Test pipeline.py: wynik dla origin 2026-09-21 zgodny z CSV notebooka (M2, B1, flagi), ograniczenia schematu forecast."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("lightgbm")

from bc01.pipeline import compute_forecast, horizon_labels  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "datasets" / "synthetic" / "bc01"
CSV = REPO / "analizy" / "bc01-prognoza-popytu" / "prognoza-W39-W42-top20.csv"
ORIGIN = pd.Timestamp("2026-09-21")


def test_horizon_labels():
    assert horizon_labels(ORIGIN) == ("2026-W39", "2026-W42")
    assert horizon_labels(pd.Timestamp("2026-12-28")) == ("2026-W53", "2027-W03")


@pytest.mark.skipif(not (DATA / "fact_sales.parquet").exists() or not CSV.exists(), reason="brak danych lub CSV")
def test_forecast_matches_notebook_csv_and_schema_constraints():
    series, weekly = compute_forecast(DATA, ORIGIN)
    assert len(series) == 120 and len(weekly) == 480
    assert (series.p10_units_total <= series.forecast_units_total).all()
    assert (series.forecast_units_total <= series.p90_units_total).all()
    assert weekly.groupby(["style_code", "location_code"]).forecast_units.sum().round(1).sub(
        series.set_index(["style_code", "location_code"]).forecast_units_total, fill_value=0).abs().max() < 0.1

    ref = pd.read_csv(CSV).rename(columns={"model": "style_code", "lokalizacja": "location_code"})
    m = ref.merge(series, on=["style_code", "location_code"])
    assert len(m) == 120
    assert ((m.forecast_units_total - m.M2_4tyg).abs() / m.M2_4tyg).max() < 0.05
    assert (m.baseline_b1_units_total - m.B1_4tyg).abs().max() < 0.05
    assert (m.flag_new_model == m.nowy_model).all()
    assert (m.flag_possible_stockout == m.podejrzenie_braku_towaru).all()


def test_origin_without_data_fails():
    if not (DATA / "fact_sales.parquet").exists():
        pytest.skip("brak danych")
    with pytest.raises(ValueError, match="dane nie sięgają"):
        compute_forecast(DATA, pd.Timestamp("2026-11-09"))
