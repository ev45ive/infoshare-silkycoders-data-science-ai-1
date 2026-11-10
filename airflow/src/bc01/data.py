"""Wczytanie danych BC-01 w kontrakcie "as of": tylko dni przed poniedziałkiem-origin."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SALES_COLUMNS = ["DateKey", "ProductKey", "StoreKey", "Quantity"]


def load_sales(data_dir: Path, origin: pd.Timestamp) -> pd.DataFrame:
    """Zwraca sprzedaż (sztuki) z dniami przed origin, z kolumnami model i tydzień ISO."""
    origin = pd.Timestamp(origin).normalize()
    if origin.weekday() != 0:
        raise ValueError(f"origin musi być poniedziałkiem, dostano {origin.date()}")

    sales = pd.read_parquet(data_dir / "fact_sales.parquet", columns=SALES_COLUMNS)
    dates = pd.read_parquet(data_dir / "dim_date.parquet", columns=["DateKey", "Date"])
    products = pd.read_parquet(data_dir / "dim_product.parquet", columns=["ProductKey", "StyleCode"])

    df = sales.merge(dates, on="DateKey", how="inner").merge(products, on="ProductKey", how="inner")
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    df = df[df["Date"] < origin].copy()
    df["week_start"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit="D")
    return df.rename(columns={"StyleCode": "model", "StoreKey": "store_key", "Quantity": "qty"})[
        ["week_start", "model", "store_key", "qty"]
    ]


def weekly_matrix(sales: pd.DataFrame) -> pd.DataFrame:
    """Sztuki tygodniowo: wiersze tygodnie, kolumny (model, store_key); brak wiersza = 0 (zgodnie z sekcją 3 notebooka)."""
    return (
        sales.groupby(["week_start", "model", "store_key"])["qty"]
        .sum()
        .unstack(["model", "store_key"])
        .sort_index()
        .fillna(0.0)
    )


def top_models(sales: pd.DataFrame, origin: pd.Timestamp, n: int, lookback_weeks: int) -> list[str]:
    """N modeli o największej sprzedaży w lookback_weeks tygodniach przed origin (łącznie po lokalizacjach)."""
    origin = pd.Timestamp(origin).normalize()
    start = origin - pd.Timedelta(weeks=lookback_weeks)
    window = sales[(sales["week_start"] >= start) & (sales["week_start"] < origin)]
    totals = window.groupby("model")["qty"].sum().sort_values(ascending=False, kind="stable")
    return list(totals.head(n).index)
