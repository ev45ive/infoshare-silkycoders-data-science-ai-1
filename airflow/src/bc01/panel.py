"""Macierz tygodniowa model x lokalizacja z zasadą startu serii (sekcja 3 i 5 notebooka)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

FIRST_WEEK = pd.Timestamp("2025-01-06")


@dataclass(frozen=True)
class Panel:
    weeks: pd.DatetimeIndex
    series: pd.DataFrame          # kolumny: model, store_key; kolejność = kolumny macierzy
    yraw: np.ndarray              # sztuki, brak sprzedaży = 0
    y: np.ndarray                 # NaN przed startem serii
    start: dict[str, int]         # model -> indeks tygodnia startu
    model_cols: dict[str, np.ndarray]


def build_panel(weekly: pd.DataFrame, origin: pd.Timestamp, models: list[str],
                store_keys: list[int], basic: set[str]) -> Panel:
    origin = pd.Timestamp(origin).normalize()
    weeks = pd.date_range(FIRST_WEEK, origin - pd.Timedelta(weeks=1), freq="W-MON")
    cols = pd.MultiIndex.from_product([list(models), list(store_keys)], names=["model", "store_key"])

    piv = weekly.pivot_table(index="week_start", columns=["model", "store_key"], values="qty", aggfunc="sum")
    yraw = piv.reindex(index=weeks, columns=cols).fillna(0.0).to_numpy(float)

    model_of_col = cols.get_level_values("model")
    model_cols = {m: np.flatnonzero(model_of_col == m) for m in models}
    # Tak jak w notebooku: model bez sprzedaży dostaje start 0 (argmax z samych zer).
    start = {m: (0 if m in basic else int(np.argmax(yraw[:, ix].sum(1) > 0))) for m, ix in model_cols.items()}

    start_col = np.array([start[m] for m in model_of_col])
    alive = np.arange(len(weeks))[:, None] >= start_col[None, :]
    y = np.where(alive, yraw, np.nan)
    return Panel(weeks=weeks, series=cols.to_frame(index=False), yraw=yraw, y=y, start=start, model_cols=model_cols)
