"""Flaga podejrzenia braku towaru: sprzedaż serii dużo poniżej oczekiwanej z udziału w modelu (sekcja 5 notebooka)."""

from __future__ import annotations

import numpy as np


def detect_stockouts(Y: np.ndarray, model_cols: dict[str, np.ndarray], start: dict[str, int],
                     min_exp: float = 15.0, frac: float = 0.2, win: int = 8,
                     min_hist: int = 4, min_age: int = 6) -> tuple[np.ndarray, np.ndarray]:
    Tn, Sn = Y.shape
    F = np.zeros((Tn, Sn), bool)
    E = np.full((Tn, Sn), np.nan)
    for model, ix in model_cols.items():
        sub = np.nan_to_num(Y[:, ix])
        tot = sub.sum(1)
        t0 = start[model]
        for j, c in enumerate(ix):
            hist: list[tuple[float, float]] = []      # tygodnie bez flagi: (sprzedaż serii, sprzedaż modelu)
            for t in range(t0, Tn):
                if len(hist) >= min_hist and (t - t0) >= min_age:
                    own = sum(h[0] for h in hist[-win:])
                    tw = sum(h[1] for h in hist[-win:])
                    if 0 < own < tw:
                        sh = own / tw
                        e = sh * (tot[t] - sub[t, j]) / (1 - sh)
                        E[t, c] = e
                        if e >= min_exp and sub[t, j] <= frac * e:
                            F[t, c] = True
                            continue                  # oflagowany tydzień nie wchodzi do udziału
                hist.append((sub[t, j], tot[t]))
    return F, E
