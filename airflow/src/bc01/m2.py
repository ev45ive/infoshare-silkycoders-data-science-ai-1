"""M2 BC-01: LightGBM (Poisson) na wierszach cech origin x seria x horyzont.

Konfiguracja zamrożona wg notebooka (wybór: ablacja grup cech i siatka parametrów na originach strojeniowych).
Źródło wartości: klucz (cechy, parametry) w cache notebooka, który ma prognozy dla wszystkich originów:
analizy/bc01-prognoza-popytu/cache/m2_runs_v1.pkl (cache nie jest w repo; test weryfikuje zgodność).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bc01.features import Context, feature_rows

# Kolejność zgodna z kluczem cache (33 cechy minus grupa "krk").
M2_FEATURES: tuple[str, ...] = (
    "h", "lag1", "lag2", "lag3", "lag4", "m4", "m8", "m13", "trend",
    "cat", "store", "coll", "is_basic", "age_series", "age_launch",
    "mdl_m4", "mdl_last", "share8", "cat_mom",
    "open_days", "moving", "wk_easter", "wk_corpus", "wk_black_friday", "wk_xmas_eve",
    "trading_sunday", "holidays_monsat", "iso_week", "lag52", "m8_ly", "disc",
)

M2_PARAMS: dict = dict(
    objective="poisson", learning_rate=0.05, num_leaves=15, min_child_samples=30,
    subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
    n_estimators=600, random_state=20260921, n_jobs=4, verbose=-1,
    deterministic=True, force_row_wise=True,
)

CAT_FEATURES: tuple[str, ...] = ("cat", "store", "coll")
FIRST_ORIGIN_INDEX = 8  # origin od tygodnia 8 (jak w notebooku: range(8, T + 1))


def build_rows(ctx: Context, Y: np.ndarray, F: np.ndarray, YI: np.ndarray,
               MT: np.ndarray, CT: np.ndarray, T: int) -> pd.DataFrame:
    """Wiersze cech dla wszystkich originów t = 8..T (włącznie), jak ROWS w notebooku."""
    parts = [feature_rows(ctx, t, Y, F, YI, MT, CT) for t in range(FIRST_ORIGIN_INDEX, T + 1)]
    return pd.concat(parts, ignore_index=True)


def fit_predict(rows: pd.DataFrame, origin_t: int, n_series: int,
                feats=M2_FEATURES, params: dict | None = None) -> np.ndarray:
    """Trening na wierszach znanych przed originem, predykcja wierszy z t == origin_t.

    Trening: y znane, tydzień docelowy tw <= origin_t - 1, bez flagi braku towaru w tygodniu docelowym.
    Zwraca (S, 4): prognoza sztuk dla każdej serii i horyzontu h = 1..4 (NaN, gdy brak wiersza).
    """
    from lightgbm import LGBMRegressor  # import lokalny: moduł ładowany także bez lightgbm

    params = dict(M2_PARAMS if params is None else params)
    feats = list(feats)
    known = rows[rows.y.notna() & ~rows.flag_tw.astype(bool)]
    tr = known[known.tw <= origin_t - 1]
    te = rows[rows.t == origin_t]
    cats = [f for f in CAT_FEATURES if f in feats]
    model = LGBMRegressor(**params).fit(tr[feats], tr.y, categorical_feature=cats)
    out = np.full((n_series, 4), np.nan)
    out[te.c.to_numpy(int), te.h.to_numpy(int) - 1] = model.predict(te[feats])
    return out
