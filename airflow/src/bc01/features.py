"""Cechy BC-01 w chwili origin (port komórek 48–52 notebooka).

Zasada: cechy sprzedażowe używają wyłącznie tygodni < origin; cechy kalendarza
tygodnia docelowego są znane z góry. Kolumna `y` to cel (surowa sprzedaż) i nie
wchodzi do cech.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .panel import Panel
from .stockouts import detect_stockouts

# Tygodnie, w których Kraków (przebudowa z wymiaru sklepu) był zamknięty / po przebudowie (notebook, komórka 48)
KRK_WORKS_WEEKS = ["2026-03-09", "2026-03-16", "2026-03-23"]
KRK_POST_FROM = "2026-03-30"
COLL_ORDER = ["BASIC", "SS25", "AW25", "SS26", "AW26"]
CAL_COLS = ["open_days", "moving", "wk_easter", "wk_corpus", "wk_black_friday", "wk_xmas_eve",
            "trading_sunday", "holidays_monsat"]


@dataclass(frozen=True)
class Context:
    T: int                          # liczba tygodni z danymi; origin = indeks T
    WX: pd.DatetimeIndex            # T tygodni z danymi + 4 przyszłe
    OD: np.ndarray                  # (len(WX), S) dni otwarcia
    DISC: np.ndarray                # (T, S) stopa rabatu modelu (plan cen, znany z góry)
    CAL: pd.DataFrame               # indeks WX: store_open_days, holidays_monsat, trading_sunday, wk_*
    ISOW: np.ndarray                # (len(WX),) numer tygodnia ISO
    MOVING: np.ndarray              # (len(WX),) tygodnie wokół świąt ruchomych
    KRK_WORKS: np.ndarray           # (len(WX),)
    KRK_POST: np.ndarray            # (len(WX),)
    KRK: np.ndarray                 # (S,) seria Krakowa
    START: np.ndarray               # (S,) indeks tygodnia startu serii
    CAT: np.ndarray                 # (S,) kod kategorii
    STO: np.ndarray                 # (S,) indeks sklepu
    COLL: np.ndarray                # (S,) kod kolekcji
    BASIC: np.ndarray               # (S,) bool
    LAUNCH: pd.DatetimeIndex        # (S,) planowana premiera modelu
    MODEL_COLS: dict                # model -> indeksy kolumn serii
    CAT_CODES: dict                 # kategoria -> kod
    CAT_OF_COL: np.ndarray          # (S,) indeks kategorii (kolumny = serie)
    SERIES: pd.DataFrame            # model, store_key (kolejność kolumn)


def build_context(panel: Panel, cal: pd.DataFrame, meta: pd.DataFrame, disc: pd.DataFrame,
                  online_key: int, krk_key: int) -> Context:
    """`cal` indeks: WX (T + 4 tyg.); `meta` indeks: model, kolumny category, collection, launch;
    `disc` indeks: tygodnie z danymi, kolumny: modele."""
    series = panel.series
    T = len(panel.weeks)
    WX = pd.DatetimeIndex(cal.index)
    if not WX[:T].equals(pd.DatetimeIndex(panel.weeks)):
        raise ValueError("kalendarz musi zaczynać się od tygodni panelu")
    S = len(series)
    models = series.model.to_numpy()
    store_keys = series.store_key.to_numpy()

    is_online = store_keys == online_key
    OD = np.where(is_online[None, :], 7.0, cal.store_open_days.to_numpy(float)[:, None])

    disc_w = disc.reindex(index=panel.weeks).fillna(0.0)
    DISC = disc_w.reindex(columns=models).fillna(0.0).to_numpy(float)

    iso = WX.isocalendar()
    ISOW = iso.week.to_numpy().astype(int)
    MOVING = ((cal.wk_easter + cal.wk_before_easter + cal.wk_corpus + cal.wk_easter.shift(1).fillna(0)) > 0).to_numpy()

    cat_codes = {c: i for i, c in enumerate(sorted(meta.category.unique()))}
    coll_codes = {c: i for i, c in enumerate(COLL_ORDER)}
    cat_of = meta.category.reindex(models).to_numpy()
    coll_of = meta.collection.reindex(models).to_numpy()
    launch = pd.to_datetime(meta.launch.reindex(models).to_numpy())
    START = np.array([panel.start[m] for m in models], dtype=int)

    return Context(
        T=T, WX=WX, OD=OD, DISC=DISC, CAL=cal, ISOW=ISOW, MOVING=MOVING,
        KRK_WORKS=np.asarray(WX.isin(pd.to_datetime(KRK_WORKS_WEEKS))),
        KRK_POST=np.asarray(WX >= pd.Timestamp(KRK_POST_FROM)),
        KRK=(store_keys == krk_key),
        START=START,
        CAT=np.array([cat_codes[c] for c in cat_of]),
        STO=store_keys.astype(int) - 1,
        COLL=np.array([coll_codes[c] for c in coll_of]),
        BASIC=(coll_of == "BASIC"),
        LAUNCH=pd.DatetimeIndex(launch),
        MODEL_COLS=panel.model_cols,
        CAT_CODES=cat_codes,
        CAT_OF_COL=np.array([cat_codes[c] for c in cat_of]),
        SERIES=series,
    )


def clean_sales(panel: Panel) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Zwraca (F, E, YI): flagi braku towaru, oczekiwanie, sprzedaż oczyszczona (w flagach = E)."""
    F, E = detect_stockouts(panel.y, panel.model_cols, panel.start)
    YI = panel.y.copy()
    YI[F] = E[F]
    return F, E, YI


def aggregates(ctx: Context, YI: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """MT: sprzedaż modelu we wszystkich lokalizacjach (przed startem NaN); CT: sprzedaż kategorii."""
    MT = np.full_like(YI, np.nan)
    CT = np.zeros_like(YI)
    for m, ix in ctx.MODEL_COLS.items():
        MT[:, ix] = np.nansum(YI[:, ix], axis=1, keepdims=True)
        MT[: ctx.START[ix[0]], ix] = np.nan
    for k in range(len(ctx.CAT_CODES)):
        ixs = np.where(ctx.CAT_OF_COL == k)[0]
        CT[:, ixs] = np.nansum(YI[:, ixs], axis=1, keepdims=True)
    return MT, CT


GROUPS = {
    "lag": ["lag1", "lag2", "lag3", "lag4", "m4", "m8", "m13", "trend"],
    "ident": ["cat", "store", "coll", "is_basic", "age_series", "age_launch"],
    "pool": ["mdl_m4", "mdl_last", "share8", "cat_mom"],
    "cal": CAL_COLS,
    "season": ["iso_week", "lag52", "m8_ly"],
    "disc": ["disc"],
    "krk": ["krk_works", "krk_post"],
}


def feature_rows(ctx: Context, t: int, Y: np.ndarray, F: np.ndarray, YI: np.ndarray,
                 MT: np.ndarray, CT: np.ndarray) -> pd.DataFrame:
    """Wiersze cech dla origin t (poniedziałek tygodnia t), po jednym na horyzont h = 1..4."""
    cs = np.where(ctx.START <= t - 1)[0]
    win = lambda A_, n: A_[max(0, t - n):t][:, cs]
    f = {f"lag{k}": YI[t - k, cs] for k in (1, 2, 3, 4)}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        f["m4"], f["m8"], f["m13"] = (np.nanmean(win(YI, n), 0) for n in (4, 8, 13))
        f["trend"] = (f["m4"] + 0.5) / (f["m8"] + 0.5)
        f["mdl_m4"] = np.nanmean(win(MT, 4), 0)
        f["share8"] = np.nansum(win(YI, 8), 0) / (np.nansum(win(MT, 8), 0) + 1e-9)
        f["cat_mom"] = (np.nansum(win(CT, 4), 0) + 1) / (np.nansum(CT[max(0, t - 8):max(0, t - 4)][:, cs], 0) + 1)
    f["mdl_last"] = MT[t - 1, cs]
    f["cat"], f["store"], f["coll"] = ctx.CAT[cs], ctx.STO[cs], ctx.COLL[cs]
    f["is_basic"] = ctx.BASIC[cs].astype(int)
    f["age_series"] = t - ctx.START[cs]
    f["age_launch"] = np.asarray((ctx.WX[t] - ctx.LAUNCH[cs]).days, dtype=float) / 7

    out = []
    for h in (1, 2, 3, 4):
        tw = t + h - 1
        d = dict(f)
        d.update(t=t, h=h, tw=tw, c=cs)
        d["open_days"] = ctx.OD[tw, cs]
        d["moving"] = float(ctx.MOVING[tw])
        for k in ("wk_easter", "wk_corpus", "wk_black_friday", "wk_xmas_eve", "trading_sunday", "holidays_monsat"):
            d[k] = float(ctx.CAL[k].iloc[tw])
        d["iso_week"] = ctx.ISOW[tw]
        d["lag52"] = YI[tw - 52, cs] if tw - 52 >= 0 else np.full(len(cs), np.nan)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            d["m8_ly"] = np.nanmean(YI[t - 60:t - 52][:, cs], 0) if t - 60 >= 0 else np.full(len(cs), np.nan)
        d["disc"] = ctx.DISC[tw, cs] if tw < ctx.T else np.zeros(len(cs))
        d["krk_works"] = (ctx.KRK_WORKS[tw] & ctx.KRK[cs]).astype(float)
        d["krk_post"] = (ctx.KRK_POST[tw] & ctx.KRK[cs]).astype(float)
        d["y"] = Y[tw, cs] if tw < ctx.T else np.full(len(cs), np.nan)
        d["flag_tw"] = F[tw, cs] if tw < ctx.T else np.zeros(len(cs), bool)
        out.append(pd.DataFrame(d))
    return pd.concat(out, ignore_index=True)
