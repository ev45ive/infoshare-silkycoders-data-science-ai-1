"""Rdzeń obliczeń BC-04 przeniesiony z notebooka bc04-sell-through-przecena.ipynb (fazy 2-7) bez zmian logiki.

Cel: te same liczby co w notebooku (parytet), ale wywoływalne z kodu pod śledzeniem MLflow.
Źródło każdej funkcji: odpowiednia komórka notebooka (nazwy zachowane).
"""
from __future__ import annotations

import itertools
import warnings
from pathlib import Path
from types import SimpleNamespace

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import norm
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=FutureWarning)

SEED = 20260920
COST = dict(delta=0.20, delta_clear=0.25, hold_m=0.015, hold_months=2, eps=0.50, tau=0.60)
TAU = COST["tau"]
EPS = COST["eps"]
DAYS = [13, 20, 27, 34, 41, 48]
HIST = ["SS25", "AW25", "SS26"]
COLLS = ["SS25", "AW25", "SS26"]
GRID = np.round(np.arange(0.05, 0.96, 0.05), 2)
TABLES = ["dim_date", "dim_store", "dim_product", "merch_plan", "fact_sales", "fact_inventory_daily"]


# ----------------------------------------------------------------------------- dane (notebook: Load Data, 2.1-2.5, Transform)
def build_dataset(data_dir: Path, cache_dir: Path) -> SimpleNamespace:
    cache_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    for t in TABLES:
        con.execute(f"CREATE OR REPLACE VIEW {t} AS SELECT * FROM read_parquet('{(data_dir / (t + '.parquet')).as_posix()}')")
    dim_store = con.sql("SELECT * FROM dim_store").df()
    dim_product = con.sql("SELECT * FROM dim_product").df()
    merch_plan = con.sql("SELECT * FROM merch_plan").df()
    con.execute("""CREATE OR REPLACE VIEW pm AS
        SELECT p.ProductKey, p.SKU, p.StyleCode, p.Category, p.Size, p.Color, p.ListPrice, p.UnitCost,
               m.Collection, m.LaunchDate, m.PlannedUnits
        FROM dim_product p JOIN merch_plan m USING (StyleCode)""")
    con.execute("""CREATE OR REPLACE VIEW sales_pm AS
        SELECT CAST(d.Date AS DATE) AS Date, f.StoreKey, f.Quantity, f.UnitPrice, f.DiscountAmount, f.GrossAmount, f.NetAmount,
               f.UnitCost AS SaleUnitCost, pm.ProductKey, pm.StyleCode, pm.Category, pm.Size, pm.Collection, pm.LaunchDate
        FROM fact_sales f JOIN pm USING (ProductKey) JOIN dim_date d USING (DateKey)""")
    con.execute("""CREATE OR REPLACE VIEW inv_pm AS
        SELECT CAST(d.Date AS DATE) AS Date, i.StoreKey, i.ProductKey, i.StockQuantity,
               pm.StyleCode, pm.Category, pm.Size, pm.Collection, pm.LaunchDate
        FROM fact_inventory_daily i JOIN pm USING (ProductKey) JOIN dim_date d USING (DateKey)""")

    # 2.3: pierwsza faktyczna sprzedaż modelu
    first_sale = con.sql("SELECT StyleCode, min(Date) AS first_sale FROM sales_pm GROUP BY 1").df()
    first_sale["first_sale"] = pd.to_datetime(first_sale.first_sale)
    mp = merch_plan.merge(first_sale, on="StyleCode")
    first_sale_map = pd.Series(mp.set_index("StyleCode").first_sale)
    con.execute("CREATE OR REPLACE TABLE fs AS SELECT * FROM (SELECT StyleCode, min(Date) AS first_sale FROM sales_pm GROUP BY 1)")

    # 2.5: dzień pierwszego rabatu modelu
    ds = con.sql("""
        SELECT s.StyleCode, s.Quantity,
               round(s.DiscountAmount / (s.Quantity * s.UnitPrice), 3) AS rate, date_diff('day', fs.first_sale, s.Date) AS age_d
        FROM sales_pm s JOIN fs USING (StyleCode)""").df()
    fd_map = ds[ds.rate > 0].groupby("StyleCode").age_d.min()

    # Transform: dzienne serie modeli
    inv = con.sql("SELECT Date, StoreKey, ProductKey, StockQuantity AS st FROM inv_pm").df()
    sal = con.sql("""SELECT Date, StoreKey, ProductKey, sum(Quantity) AS q, sum(CASE WHEN DiscountAmount > 0 THEN Quantity ELSE 0 END) AS qd
                     FROM sales_pm GROUP BY ALL""").df()
    for d_ in (inv, sal):
        d_["Date"] = pd.to_datetime(d_["Date"])
    sku = con.sql("SELECT ProductKey, StyleCode, Collection, Size, Category FROM pm").df()
    stores = sorted(dim_store.StoreKey)

    def build_collection(coll):
        sk = sku[sku.Collection == coll].sort_values("ProductKey").reset_index(drop=True)
        cols = {(p, s): j for j, (p, s) in enumerate(itertools.product(sk.ProductKey, stores))}
        i = inv[inv.ProductKey.isin(sk.ProductKey)]
        dates = pd.date_range(i.Date.min(), i.Date.max())
        di = pd.Series(range(len(dates)), index=dates)
        S = np.full((len(dates), len(cols)), np.nan)
        ri, ci = i.Date.map(di).to_numpy(), np.array([cols[(p, s)] for p, s in zip(i.ProductKey, i.StoreKey)])
        S[ri, ci] = np.maximum(i.st.to_numpy(), 0)
        Q, QD = np.zeros_like(S), np.zeros_like(S)
        s_ = sal[sal.ProductKey.isin(sk.ProductKey) & sal.Date.isin(dates)]
        rs, cs_ = s_.Date.map(di).to_numpy(), np.array([cols[(p, s)] for p, s in zip(s_.ProductKey, s_.StoreKey)])
        Q[rs, cs_], QD[rs, cs_] = s_.q.to_numpy(), s_.qd.to_numpy()
        seen = ~np.isnan(S)
        first_obs = np.where(seen.any(0), seen.argmax(0), len(dates))
        S_imp, IMP = S.copy(), np.zeros(S.shape, bool)
        for d in range(len(dates)):
            miss = np.isnan(S_imp[d])
            if miss.any():
                prev = S_imp[d - 1] if d > 0 else np.zeros(S.shape[1])
                S_imp[d, miss] = np.maximum(np.nan_to_num(prev[miss]) - Q[d, miss], 0)
                IMP[d, miss] = d > first_obs[miss]
        S_imp = np.nan_to_num(S_imp)
        mcol = np.repeat(sk.StyleCode.to_numpy(), len(stores))
        gs = lambda M: pd.DataFrame(M, index=dates).T.groupby(mcol).sum().T
        stock, imp_stock = gs(S_imp), gs(S_imp * IMP)
        cum, cumd, u = gs(Q).cumsum(), gs(QD).cumsum(), gs(Q)
        net = S_imp.reshape(len(dates), len(sk), len(stores)).sum(2) > 0
        core = sk.Size.isin(["M", "L", "ONE"]).to_numpy()
        av = lambda mask: pd.DataFrame(net[:, mask], index=dates).T.groupby(sk.StyleCode.to_numpy()[mask]).mean().T
        parts = {"stock": stock, "imp_stock": imp_stock, "cum": cum, "cumd": cumd, "u": u, "avail_core": av(core), "avail_all": av(np.ones(len(sk), bool))}
        out = pd.concat({k: v.stack() for k, v in parts.items()}, axis=1).rename_axis(["Date", "StyleCode"]).reset_index()
        out["Collection"] = coll
        return out

    ms = pd.concat([build_collection(c) for c in ["SS25", "AW25", "SS26", "AW26"]], ignore_index=True)
    ms["first_sale"] = ms.StyleCode.map(first_sale_map)
    ms["age_d"] = (ms.Date - ms.first_sale).dt.days
    ms = ms[ms.age_d >= 0].sort_values(["StyleCode", "age_d"]).reset_index(drop=True)
    ms["supply"] = ms.cum + ms.stock
    ms["st"] = ms.cum / ms.supply
    ms["u7"] = ms.groupby("StyleCode").u.transform(lambda s: s.rolling(7, min_periods=1).sum())
    CAT = sku.drop_duplicates("StyleCode").set_index("StyleCode").Category
    ms["Category"] = ms.StyleCode.map(CAT)
    ms["first_disc_d"] = ms.StyleCode.map(fd_map)

    # Transform: tabela modelowa
    prod = dim_product.merge(merch_plan, on="StyleCode", how="left")
    prod["net_price"] = prod["ListPrice"] / 1.23
    P_ = {k: ms.pivot(index="StyleCode", columns="age_d", values=k) for k in ["cum", "supply", "stock", "st", "u7", "avail_core", "avail_all"]}
    price = prod.groupby("StyleCode").agg(p=("net_price", "first"), c=("UnitCost", "first"))
    mod = ms.groupby("StyleCode").agg(Collection=("Collection", "first"), Category=("Category", "first"),
                                      first_disc_d=("first_disc_d", "first"), age_max=("age_d", "max"))

    def cum_at(day):
        return P_["cum"][day] if day >= 0 else pd.Series(0.0, index=P_["cum"].index)

    def rows_at(d, models):
        ix = models
        r = pd.DataFrame(index=ix)
        r["d"], r["k"] = d, (d + 1) // 7
        r["Collection"], r["Category"], r["first_disc_d"] = mod.Collection.reindex(ix), mod.Category.reindex(ix), mod.first_disc_d.reindex(ix)
        r["st_d"], r["cum_d"], r["supply_d"] = P_["st"][d].reindex(ix), P_["cum"][d].reindex(ix), P_["supply"][d].reindex(ix)
        r["rate14"] = ((cum_at(d) - cum_at(d - 14)) / 14 / P_["supply"][d]).reindex(ix)
        r["pred55"] = np.minimum(1.0, r.st_d + r.rate14 * (55 - d))
        r["trend"] = np.log((P_["u7"][d] + 1) / (P_["u7"][d - 7] + 1)).reindex(ix)
        r["avail_core"], r["avail_all"] = P_["avail_core"][d].reindex(ix), P_["avail_all"][d].reindex(ix)
        r["restock"] = (P_["supply"][d] / P_["supply"][0] - 1).reindex(ix)
        r["ln_price"] = np.log(price.p.reindex(ix))
        r["p"], r["c"] = price.p.reindex(ix), price.c.reindex(ix)
        r["cum55"], r["supply55"], r["st55"] = P_["cum"][55].reindex(ix), P_["supply"][55].reindex(ix), P_["st"][55].reindex(ix)
        r["q_rest"] = r.cum55 - r.cum_d
        return r.reset_index()

    hist_models = mod.index[mod.Collection.isin(HIST)]
    D_all = pd.concat([rows_at(d, hist_models) for d in DAYS], ignore_index=True)
    D_all["censored"] = D_all.first_disc_d < 56
    D = D_all[~D_all.censored].reset_index(drop=True)
    cats = sorted(D_all.Category.unique())
    for _df in (D, D_all):
        _df["cat"] = _df.Category.map({c: i for i, c in enumerate(cats)})

    # M3: dopasowania krzywej (cache w katalogu zadania)
    m3_file = cache_dir / "m3_curve_fits.parquet"
    if m3_file.exists():
        _m3 = pd.read_parquet(m3_file)
    else:
        out = []
        for i, r in enumerate(D_all.itertuples()):
            c55, sd = fit_curve(P_["cum"].loc[r.StyleCode].to_numpy(), int(r.d), seed=SEED + i)
            out.append((min(c55 / r.supply_d, 1.0) if c55 == c55 else np.nan, sd / r.supply_d if sd == sd else np.nan))
        _m3 = pd.DataFrame(out, columns=["mu3", "s_fit"], index=D_all.index)
        _m3.insert(0, "key", D_all.StyleCode + "|" + D_all.d.astype(str))
        _m3.to_parquet(m3_file)
    _m3k = _m3.set_index("key")
    for _df in (D, D_all):
        key = _df.StyleCode + "|" + _df.d.astype(str)
        _df["mu3"], _df["s_fit"] = key.map(_m3k.mu3).to_numpy(), key.map(_m3k.s_fit).to_numpy()
    return SimpleNamespace(D=D, D_all=D_all, ms=ms, P_=P_, mod=mod, cats=cats)


# ----------------------------------------------------------------------------- M3 (notebook: Faza 6)
def _curve(t, A, th):
    return A * (1 - np.exp(-(t + 1) / th))


def fit_curve(cum_series, d, n_boot=40, seed=0):
    t = np.arange(d + 1, dtype=float)
    y = cum_series[: d + 1].astype(float)
    cd = y[-1]

    def one(yy):
        try:
            p, _ = curve_fit(_curve, t, yy, p0=[cd * 1.5, 40.0], bounds=([max(cd, 1.0), 2.0], [cd * 8 + 10, 400.0]), maxfev=4000)
            return p
        except Exception:
            return np.array([np.nan, np.nan])

    p0 = one(y)
    if np.isnan(p0[0]):
        return np.nan, np.nan
    res = y - _curve(t, *p0)
    rg = np.random.default_rng(seed)
    c55 = [_curve(55.0, *one(np.maximum.accumulate(_curve(t, *p0) + rg.choice(res, len(res))))) for _ in range(n_boot)]
    return _curve(55.0, *p0), float(np.nanstd(c55))


# ----------------------------------------------------------------------------- ocena (notebook: Faza 5-7)
def label(df, tau):
    return (df.st55 < tau).astype(int).to_numpy()


def cost_table(df, tau, delta=None, d_clear=None, eps=None, hold=None):
    delta = COST["delta"] if delta is None else delta
    d_clear = COST["delta_clear"] if d_clear is None else d_clear
    eps = EPS if eps is None else eps
    hold = COST["hold_m"] if hold is None else hold
    S = np.maximum(0.0, tau * df.supply55 - df.cum55)
    k_miss = (S * (d_clear * df.p + hold * COST["hold_months"] * df.c)).to_numpy()
    k_flag = (delta * df.p * df.q_rest).to_numpy()
    return pd.DataFrame({"c_no": k_miss, "c_flag": k_flag + (1 - eps) * k_miss, "k_flag": k_flag, "k_miss": k_miss}, index=df.index)


def theory_threshold(df, tau, **kw):
    ct, y = cost_table(df, tau, **kw), pd.Series(label(df, tau), index=df.index)
    eps = EPS if kw.get("eps") is None else kw["eps"]
    out = {}
    for k_, ix in df.groupby("k").groups.items():
        out[k_] = float(np.clip(ct.loc[ix, "k_flag"].mean() / (eps * ct.loc[ix, "k_miss"].sum() / max(y.loc[ix].sum(), 1)), 0.02, 0.98))
    return out


def pick_threshold(df, p, tau, **kw):
    ct, out = cost_table(df, tau, **kw), {}
    c_flag, c_no = ct.c_flag.to_numpy(), ct.c_no.to_numpy()
    for k_, ix in df.reset_index(drop=True).groupby("k").indices.items():
        tot = [np.where(p[ix] > t, c_flag[ix], c_no[ix]).sum() for t in GRID]
        out[k_] = float(GRID[np.isclose(tot, np.min(tot))].max())
    return out


def _sigma(resid, k_tr, k_te):
    s = pd.Series(resid).groupby(k_tr).std(ddof=1)
    return np.maximum(pd.Series(k_te).map(s).fillna(s.mean()).to_numpy(), 0.03)


def m_B0g(tr, te, tau):
    return np.full(len(te), label(tr, tau).mean())


def m_B0(tr, te, tau):
    y = pd.Series(label(tr, tau), index=tr.index)
    n, g = tr.groupby("Category").size(), y.mean()
    w = n / (n + 30)
    est = w * y.groupby(tr.Category).mean() + (1 - w) * g
    return te.Category.map(est).fillna(g).to_numpy()


def m_B1(tr, te, tau):
    s = _sigma((tr.st55 - tr.pred55).to_numpy(), tr.k.to_numpy(), te.k.to_numpy())
    return norm.cdf((tau - te.pred55.to_numpy()) / s)


def m_B2(tr, te, tau):
    res = tr.st55 - tr.pred55
    n = tr.groupby("Category").size()
    bias = res.groupby(tr.Category).mean() * (n / (n + 30))
    s = _sigma((res - tr.Category.map(bias)).to_numpy(), tr.k.to_numpy(), te.k.to_numpy())
    mu = te.pred55 + te.Category.map(bias).fillna(0.0)
    return norm.cdf((tau - mu.to_numpy()) / s)


FE_M1 = ["pred55", "st_d", "trend", "avail_core", "restock", "ln_price", "k"]
FE_M2 = FE_M1 + ["rate14", "avail_all", "cat"]


def make_logit(feats, C=1.0):
    def f(tr, te, tau):
        m = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=2000)).fit(tr[feats], label(tr, tau))
        return m.predict_proba(te[feats])[:, 1]
    return f


def make_ridge(feats, alpha=3.0):
    def f(tr, te, tau):
        m = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(tr[feats], tr.st55)
        res = (tr.st55 - m.predict(tr[feats])).to_numpy() * np.sqrt(len(tr) / (len(tr) - len(feats) - 1))
        return norm.cdf((tau - m.predict(te[feats])) / _sigma(res, tr.k.to_numpy(), te.k.to_numpy()))
    return f


def _gbm():
    return lgb.LGBMClassifier(n_estimators=150, learning_rate=0.03, max_depth=2, num_leaves=4, min_child_samples=20, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, reg_lambda=5.0, random_state=SEED, verbose=-1, n_jobs=1)


def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def make_gbm(feats, cal=None):
    def f(tr, te, tau):
        X, y = tr[feats], label(tr, tau)
        p_te = _gbm().fit(X, y).predict_proba(te[feats])[:, 1]
        if cal is None:
            return p_te
        oof = np.zeros(len(tr))
        for a, b in GroupKFold(5).split(X, y, tr.StyleCode):
            oof[b] = _gbm().fit(X.iloc[a], y[a]).predict_proba(X.iloc[b])[:, 1]
        if cal == "platt":
            return LogisticRegression(C=1e6).fit(_logit(oof).reshape(-1, 1), y).predict_proba(_logit(p_te).reshape(-1, 1))[:, 1]
        return IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(oof, y).predict(p_te)
    return f


def m_M3(tr, te, tau):
    ok = tr.mu3.notna()
    res = (tr.st55 - tr.mu3)[ok]
    bias_k = res.groupby(tr.k[ok]).mean()
    s_k = _sigma((res - tr.k[ok].map(bias_k)).to_numpy(), tr.k[ok].to_numpy(), te.k.to_numpy())
    mu = te.mu3 + te.k.map(bias_k).fillna(0.0)
    sd = np.sqrt(te.s_fit.fillna(0.0).to_numpy() ** 2 + s_k ** 2)
    p = norm.cdf((tau - mu.to_numpy()) / sd)
    return np.where(te.mu3.isna(), np.nan, p)


BASE = {"B0g": m_B0g, "B0": m_B0, "B1": m_B1, "B2": m_B2}
METH = {
    **BASE,
    "M1a": make_logit(FE_M1),
    "M1a bez avail_core": make_logit([f for f in FE_M1 if f != "avail_core"]),
    "M1a bez ln_price": make_logit([f for f in FE_M1 if f != "ln_price"]),
    "M1a bez restock": make_logit([f for f in FE_M1 if f != "restock"]),
    "M1r": make_ridge(FE_M1),
    "M2": make_gbm(FE_M2),
    "M2 + Platt": make_gbm(FE_M2, "platt"),
    "M2 + izotoniczna": make_gbm(FE_M2, "iso"),
    "M3": m_M3,
}
# cechy per metoda (do parametrów uruchomień); None = metoda bez cech z tabeli (częstość bazowa) lub wyłącznie pred55
FEATURES = {
    "B0g": [], "B0": ["Category"], "B1": ["pred55"], "B2": ["pred55", "Category"],
    "M1a": FE_M1, "M1a bez avail_core": [f for f in FE_M1 if f != "avail_core"],
    "M1a bez ln_price": [f for f in FE_M1 if f != "ln_price"], "M1a bez restock": [f for f in FE_M1 if f != "restock"],
    "M1r": FE_M1, "M2": FE_M2, "M2 + Platt": FE_M2, "M2 + izotoniczna": FE_M2, "M3": ["mu3", "s_fit"],
}
HYPER = {
    "B0g": "brak", "B0": "skurczenie n/(n+30) do częstości globalnej", "B1": "sigma_k z treningu; P=Phi((tau-pred55)/sigma_k)",
    "B2": "korekta kategorii skurczona n/(n+30)",
    "M1a": "LogisticRegression C=1, L2, StandardScaler", "M1a bez avail_core": "jak M1a bez avail_core",
    "M1a bez ln_price": "jak M1a bez ln_price", "M1a bez restock": "jak M1a bez restock",
    "M1r": "Ridge alpha=3 na st55, P=Phi((tau-mu)/sigma_k)",
    "M2": "LGBM depth=2 leaves=4 n=150 lr=0.03 reg_lambda=5 min_child=20 subsample=0.8 colsample=0.8 n_jobs=1",
    "M2 + Platt": "jak M2 + kalibracja Platta (OOF GroupKFold 5)", "M2 + izotoniczna": "jak M2 + kalibracja izotoniczna (OOF GroupKFold 5)",
    "M3": "krzywa A(1-exp(-(t+1)/theta)), bootstrap reszt 40x, bias_k i sigma_k z treningu",
}


def run_cv(methods, tau, data):
    outs = []
    for test_c in COLLS:
        tr, te = data[data.Collection != test_c], data[data.Collection == test_c]
        o = te.copy()
        o["y"] = label(te, tau)
        for name, f in methods.items():
            inner = pd.concat([pd.Series(f(tr[tr.Collection != c], tr[tr.Collection == c], tau), index=tr[tr.Collection == c].index)
                               for c in tr.Collection.unique()])
            o["p__" + name] = f(tr, te, tau)
            o["thr__" + name] = te.k.map(pick_threshold(tr.loc[inner.index], inner.to_numpy(), tau)).to_numpy()
        o["thr_theory"] = te.k.map(theory_threshold(tr, tau)).to_numpy()
        outs.append(o)
    return pd.concat(outs, ignore_index=True)


def ridge_mu_sd(tr, te, feats=FE_M1, alpha=3.0):
    m = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(tr[feats], tr.st55)
    res = (tr.st55 - m.predict(tr[feats])).to_numpy() * np.sqrt(len(tr) / (len(tr) - len(feats) - 1))
    return m.predict(te[feats]), _sigma(res, tr.k.to_numpy(), te.k.to_numpy())


def ev_flag(te, mu, sd, tau, delta=None, d_clear=None, eps=None, hold=None):
    delta = COST["delta"] if delta is None else delta
    d_clear = COST["delta_clear"] if d_clear is None else d_clear
    eps = EPS if eps is None else eps
    hold = COST["hold_m"] if hold is None else hold
    z = (tau - mu) / sd
    exp_short = sd * (norm.pdf(z) + z * norm.cdf(z))
    k_miss = exp_short * te.supply_d.to_numpy() * (d_clear * te.p.to_numpy() + hold * COST["hold_months"] * te.c.to_numpy())
    k_flag = delta * te.p.to_numpy() * np.maximum(mu - te.st_d.to_numpy(), 0) * te.supply_d.to_numpy()
    return k_flag + (1 - eps) * k_miss < k_miss


def add_ev(O, D, tau=TAU):
    """Prognoza ciągła M1r (uczona na kolekcjach treningowych foldu) i flaga reguły kosztowej EV."""
    O["mu_r"], O["sd_r"] = np.nan, np.nan
    for c in COLLS:
        tr_, te_ = D[D.Collection != c], D[D.Collection == c]
        mu_, sd_ = ridge_mu_sd(tr_, te_)
        ix = O.index[O.Collection == c]
        O.loc[ix, "mu_r"], O.loc[ix, "sd_r"] = mu_, sd_
    O["flag__EV"] = ev_flag(O, O.mu_r.to_numpy(), O.sd_r.to_numpy(), tau)
    return O


def policy_cost(O, tau, flag, **kw):
    ct = cost_table(O, tau, **kw)
    return np.where(flag, ct.c_flag, ct.c_no)


def rule_cost(O, m, tau, which="tuned", **kw):
    thr = O["thr__" + m] if which == "tuned" else O["thr_theory"]
    return policy_cost(O, tau, O["p__" + m] > thr, **kw)


def basic_policies(O, tau):
    return {"nie flaguj nigdy": np.zeros(len(O), bool), "flaguj zawsze": np.ones(len(O), bool),
            "praktyka robocza (ST < prosta do celu)": (O.st_d < tau * (O.d + 1) / 56).to_numpy()}


def boot_setup(O, B=1000, seed=SEED):
    ids = O.StyleCode.unique()
    return ids, np.random.default_rng(seed).multinomial(len(ids), np.ones(len(ids)) / len(ids), size=B)


def _by_model(O, vals, ids):
    t = pd.DataFrame({"v": np.asarray(vals, float), "n": 1.0, "id": O.StyleCode.to_numpy()}).groupby("id").sum().reindex(ids)
    return t.v.to_numpy(), t.n.to_numpy()


def boot_mean(O, vals, bs):
    ids, W = bs
    v, n = _by_model(O, vals, ids)
    return v.sum() / n.sum(), np.quantile((W @ v) / (W @ n), [0.05, 0.95])


def sq_err(O, m):
    return (O["p__" + m] - O.y) ** 2


def log_loss_rows(O, m):
    p = O["p__" + m].clip(1e-3, 1 - 1e-3)
    return -(O.y * np.log(p) + (1 - O.y) * np.log(1 - p))


def ece(p, y, bins=5):
    b = np.minimum((np.asarray(p) * bins).astype(int), bins - 1)
    return sum((b == i).mean() * abs(np.asarray(p)[b == i].mean() - np.asarray(y)[b == i].mean()) for i in range(bins) if (b == i).any())


def auc(O, m):
    return roc_auc_score(O.y, O["p__" + m]) if O["p__" + m].nunique() > 1 else 0.5


def calib_curve(O, m, bins=5, B=400, seed=3):
    b = np.minimum((O["p__" + m] * bins).astype(int), bins - 1).to_numpy()
    ids_ = O.StyleCode.unique()
    rg = np.random.default_rng(seed)
    out = []
    for i in range(bins):
        msk = b == i
        if msk.sum() < 5:
            continue
        v, n = _by_model(O, np.where(msk, O.y, 0), ids_)[0], _by_model(O, msk.astype(float), ids_)[0]
        Wb = rg.multinomial(len(ids_), np.ones(len(ids_)) / len(ids_), size=B)
        den = Wb @ n
        est = np.where(den > 0, (Wb @ v) / np.where(den > 0, den, 1), np.nan)
        out.append((O["p__" + m][msk].mean(), O.y[msk].mean(), *np.nanquantile(est, [.05, .95]), int(msk.sum())))
    return pd.DataFrame(out, columns=["p_śr", "udział", "od", "do", "n"])


def run_main_cv(ds: SimpleNamespace):
    """Cała walidacja z fazy 6: LOCO dla wszystkich metod + EV. Zwraca tabelę out-of-fold (jak `O` w notebooku)."""
    O = run_cv(METH, TAU, ds.D)
    O["p__M3"] = O["p__M3"].fillna(O["p__B1"])
    return add_ev(O, ds.D)
