"""Baseline B1 (dzisiejsza praktyka): średnia z 4 ostatnich tygodni, prognoza na 4 tygodnie."""

from __future__ import annotations

import pandas as pd


def b1_forecast(weekly: pd.DataFrame, origin: pd.Timestamp, horizon_weeks: int = 4) -> pd.Series:
    """Suma prognozy na horizon_weeks tygodni dla każdej serii (model, store_key)."""
    origin = pd.Timestamp(origin).normalize()
    last = weekly[(weekly.index >= origin - pd.Timedelta(weeks=4)) & (weekly.index < origin)]
    if len(last) != 4:
        raise ValueError(f"B1 wymaga 4 tygodni historii przed {origin.date()}, jest {len(last)}")
    return last.mean(axis=0) * horizon_weeks
