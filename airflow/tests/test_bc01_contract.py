import pandas as pd
import pytest

from bc01.baseline import b1_forecast
from bc01.data import top_models, weekly_matrix


def _sales(rows):
    return pd.DataFrame(rows, columns=["week_start", "model", "store_key", "qty"]).assign(
        week_start=lambda d: pd.to_datetime(d.week_start)
    )


def test_weekly_matrix_has_no_rows_after_origin_contract():
    sales = _sales([("2026-09-07", "A", 1, 5), ("2026-09-14", "A", 1, 3)])
    origin = pd.Timestamp("2026-09-21")
    assert (sales.week_start < origin).all()
    assert weekly_matrix(sales).loc[pd.Timestamp("2026-09-14"), ("A", 1)] == 3


def test_top_models_uses_only_lookback_window_before_origin():
    origin = pd.Timestamp("2026-09-21")
    sales = _sales([
        ("2026-09-14", "A", 1, 10),
        ("2026-07-01", "B", 1, 500),  # poza oknem 8 tygodni, nie może wejść do rankingu
        ("2026-09-14", "B", 2, 2),
    ])
    assert top_models(sales, origin, n=1, lookback_weeks=8) == ["A"]


def test_b1_is_four_times_mean_of_last_four_weeks():
    weeks = pd.to_datetime(["2026-08-24", "2026-08-31", "2026-09-07", "2026-09-14", "2026-09-21"])
    weekly = pd.DataFrame({("A", 1): [1.0, 2.0, 3.0, 4.0, 99.0]}, index=weeks)  # 99 = tydzień origin, poza historią
    origin = pd.Timestamp("2026-09-21")
    result = b1_forecast(weekly, origin)
    assert result[("A", 1)] == pytest.approx(4 * 2.5)


def test_b1_rejects_missing_history():
    weekly = pd.DataFrame({("A", 1): [1.0]}, index=pd.to_datetime(["2026-09-14"]))
    with pytest.raises(ValueError):
        b1_forecast(weekly, pd.Timestamp("2026-09-21"))
