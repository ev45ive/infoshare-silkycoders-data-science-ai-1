"""Wczytanie danych BC-01 w kontrakcie "as of": tylko dni przed poniedziałkiem-origin."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

SALES_COLUMNS = ["DateKey", "ProductKey", "StoreKey", "Quantity"]


@dataclass(frozen=True)
class Catalog:
    models: list[str]              # wszystkie StyleCode, posortowane (jak styles w notebooku)
    store_keys: list[int]
    store_code: dict[int, str]
    basic: set[str]                # modele z kolekcji BASIC (start serii = 0)


def load_catalog(data_dir: Path) -> Catalog:
    products = pd.read_parquet(data_dir / "dim_product.parquet", columns=["StyleCode"])
    stores = pd.read_parquet(data_dir / "dim_store.parquet", columns=["StoreKey", "StoreCode"])
    plan = pd.read_parquet(data_dir / "merch_plan.parquet", columns=["StyleCode", "Collection"])
    return Catalog(
        models=sorted(products["StyleCode"].unique()),
        store_keys=sorted(int(k) for k in stores["StoreKey"]),
        store_code={int(k): c for k, c in zip(stores["StoreKey"], stores["StoreCode"])},
        basic=set(plan.loc[plan["Collection"] == "BASIC", "StyleCode"]),
    )


def load_model_meta(data_dir: Path) -> pd.DataFrame:
    """Kategoria, kolekcja i data premiery modelu (indeks: model, jak StyleCode w notebooku)."""
    products = pd.read_parquet(data_dir / "dim_product.parquet", columns=["StyleCode", "Category"])
    plan = pd.read_parquet(data_dir / "merch_plan.parquet", columns=["StyleCode", "Collection", "LaunchDate"])
    meta = products.drop_duplicates("StyleCode").set_index("StyleCode").join(
        plan.set_index("StyleCode"), how="left")
    meta.index.name = "model"
    return meta.rename(columns={"Category": "category", "Collection": "collection", "LaunchDate": "launch"})


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
    df["week_start"] = df["Date"] - pd.to_timedelta(df["Date"].dt.day_of_week, unit="D")
    return df.rename(columns={"StyleCode": "model", "StoreKey": "store_key", "Quantity": "qty"})[
        ["week_start", "model", "store_key", "qty"]
    ]


def load_weekly_discount(data_dir: Path, origin: pd.Timestamp) -> pd.DataFrame:
    """Stopa rabatu modelu w tygodniu = SUM(DiscountAmount) / SUM(Quantity*UnitPrice) (sql/weekly_sales_style_store.sql)."""
    origin = pd.Timestamp(origin).normalize()
    sales = pd.read_parquet(data_dir / "fact_sales.parquet",
                            columns=["DateKey", "ProductKey", "Quantity", "UnitPrice", "DiscountAmount"])
    dates = pd.read_parquet(data_dir / "dim_date.parquet", columns=["DateKey", "Date"])
    products = pd.read_parquet(data_dir / "dim_product.parquet", columns=["ProductKey", "StyleCode"])
    df = sales.merge(dates, on="DateKey", how="inner").merge(products, on="ProductKey", how="inner")
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    df = df[df["Date"] < origin].copy()
    df["week_start"] = df["Date"] - pd.to_timedelta(df["Date"].dt.day_of_week, unit="D")
    df["list_value"] = df["Quantity"] * df["UnitPrice"]
    g = df.groupby(["week_start", "StyleCode"]).agg(list_value=("list_value", "sum"),
                                                   discount=("DiscountAmount", "sum")).reset_index()
    g["disc_rate"] = (g["discount"] / g["list_value"]).replace([float("inf"), float("-inf")], float("nan"))
    return g.pivot(index="week_start", columns="StyleCode", values="disc_rate").sort_index()


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
