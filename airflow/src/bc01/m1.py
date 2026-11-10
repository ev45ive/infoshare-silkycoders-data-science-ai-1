"""M1: wygładzanie ETS (tłumiony trend) na sprzedaży odsezonowanej (port komórki 65 notebooka).

Wszystkie wejścia są jawne (bez zmiennych globalnych). Indeks sezonowy ma stały
zakres 2025-W02 … 2026-W01; dla origin w 2026 nie zawiera danych z przyszłości.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

SEASON_WEEKS = 52          # pierwsze 52 tygodnie panelu: 2025-01-06 … 2025-12-29


def season_index(yd: np.ndarray, weeks: pd.DatetimeIndex, cat: np.ndarray, grp: np.ndarray,
                 n_cat: int) -> np.ndarray:
    """Indeks [tydzień ISO 0..53, kategoria, grupa]; `yd` = sprzedaż / dni otwarcia (T, S)."""
    iso = np.asarray(weeks[:SEASON_WEEKS].isocalendar().week, dtype=int)
    ix = np.ones((54, n_cat, 2))
    for k in range(n_cat):
        for g in (0, 1):
            cols = (cat == k) & (grp == g)
            ser = pd.Series(np.nansum(yd[:SEASON_WEEKS][:, cols], axis=1), index=iso).sort_index()
            sm = (ser / ser.mean()).rolling(3, center=True, min_periods=1).mean().clip(lower=0.05)
            ix[1:53, k, g] = sm.to_numpy()
            ix[53, k, g] = sm.iloc[-1]
    return ix


def forecast_m1(o: int, yi: np.ndarray, od: np.ndarray, isow: np.ndarray, cat: np.ndarray,
                grp: np.ndarray, start: np.ndarray, idxs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Prognoza 4 tygodni dla origin `o` (indeks tygodnia). Zwraca (P (S,4), fb (S,))."""
    S = yi.shape[1]
    P = np.full((S, 4), np.nan)
    fb = np.zeros(S, bool)
    zd = yi[:o] / od[:o] / idxs[isow[:o][:, None], cat[None, :], grp[None, :]]
    fidx = idxs[isow[o:o + 4][:, None], cat[None, :], grp[None, :]]
    for c in range(S):
        if start[c] > o - 1:
            continue
        z = zd[start[c] + 1:o, c]
        if len(z) < 10:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                P[c] = np.nanmean(yi[o - 4:o, c])
            fb[c] = True
            continue
        if z.sum() <= 0:
            P[c] = 0.0
            continue
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = ExponentialSmoothing(z, trend="add", damped_trend=True,
                                           initialization_method="estimated").fit(optimized=True)
            fz = np.clip(fit.forecast(4), 0, 3 * z[-8:].max())
        except Exception:
            fz = np.full(4, z[-4:].mean())
            fb[c] = True
        P[c] = fz * fidx[:, c] * od[o:o + 4, c]
    return P, fb
