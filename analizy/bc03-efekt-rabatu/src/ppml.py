"""Silnik estymacji dla analizy BC-03: regresja Poissona (PPML) z efektami stałymi, SE klastrowane, bootstrap po modelach.

Panel: wiersze uporządkowane (model, kanał, tydzień); jeden model = ciągły blok `BLOCK` wierszy, dzięki czemu bootstrap
klastrowy to sklejanie bloków, a SE klastrowe to `np.add.reduceat`.
"""
import numpy as np
import pandas as pd


def ppml(X, y, w=None, maxit=80, tol=1e-8):
    """Poisson IRLS bez interceptu. Z wagami `w` estymuje model stawki y/w (odpowiednik offsetu log w).

    Kolumny współliniowe obsługuje pseudo-odwrotność: współczynniki estymowalne są jednoznaczne.
    """
    w = np.ones(len(y)) if w is None else w
    r = y / w
    eta = np.log(r + 0.5 / np.maximum(w, 1))
    dev_old = np.inf
    for _ in range(maxit):
        mu = np.exp(eta)
        z = eta + (r - mu) / mu
        XtW = X.T * (w * mu)
        Ainv = np.linalg.pinv(XtW @ X, rcond=1e-10, hermitian=True)
        b = Ainv @ (XtW @ z)
        eta_new = np.clip(X @ b, -30, 30)
        mu_new = np.exp(eta_new)
        dev = 2 * np.sum(w * (np.where(r > 0, r * np.log(np.where(r > 0, r, 1) / mu_new), 0) - (r - mu_new)))
        if dev > dev_old + 1e-8:            # krok za duży: połowimy
            eta = (eta + eta_new) / 2
            continue
        converged = abs(dev_old - dev) < tol * (abs(dev) + 1)
        eta, dev_old = eta_new, dev
        if converged:
            break
    return b, np.exp(eta), Ainv


def cluster_cov(X, res, Ainv, starts):
    """Estymator sandwich klastrowany; `res` = reszty score (w*(r-mu)) w kolejności wierszy, klastry = bloki zaczynające się w `starts`."""
    S = np.add.reduceat(X * res[:, None], starts, axis=0)
    G = len(starts)
    return Ainv @ (S.T @ S) @ Ainv * G / (G - 1)


class Design:
    """Kolumny niezależne od wylosowanych modeli + budowa efektów stałych dla danego losowania modeli."""

    def __init__(self, Pm, bf_start, post_cells, spec="cc", harmonics=2, cat_season=True, bf_ind=True, post=True):
        self.Pm = Pm.reset_index(drop=True)
        P = self.Pm
        self.models = list(P.StyleCode.unique())
        self.M = len(self.models)
        self.nT = P.t.nunique()
        self.BLOCK = len(P) // self.M
        assert (P.groupby("StyleCode").size() == self.BLOCK).all()
        self.cats = sorted(P.Category.unique())
        self.chs = ["ONLINE", "STORE"]
        self.y = P.Qty.values.astype(float)
        ch = (P.Channel == "STORE").values.astype(int)          # 0 = ONLINE, 1 = STORE (kolejność alfabetyczna jak w panelu)
        self.ch = ch
        self.cat_i = P.Category.map({c: i for i, c in enumerate(self.cats)}).values
        self.model_cat = np.array([self.cat_i[i * self.BLOCK] for i in range(self.M)])
        cols, names = [], []
        idx = ch * self.nT + P.t.values
        W = np.zeros((len(P), 2 * self.nT)); W[np.arange(len(P)), idx] = 1
        cols.append(W); names += [f"wk{c}_{t}" for c in range(2) for t in range(self.nT)]
        if cat_season:
            ang = 2 * np.pi * P.woy.values / 52.0
            for c in self.cats:
                m = (P.Category == c).values.astype(float)
                for k in range(1, harmonics + 1):
                    cols.append((m * np.sin(k * ang))[:, None]); names.append(f"sin{k}_{c}")
                    cols.append((m * np.cos(k * ang))[:, None]); names.append(f"cos{k}_{c}")
        bf = (P.WeekStart == bf_start).values.astype(float)
        self.bf = bf
        if bf_ind:
            for c in self.cats:
                for j, chn in enumerate(self.chs):
                    cols.append((bf * (P.Category == c).values * (ch == j))[:, None]); names.append(f"bf_{c}_{chn}")
        key = pd.MultiIndex.from_frame(P[["StyleCode", "WeekStart"]])
        self.post_names = []
        if post:
            for k in (1, 2):
                sel = pd.MultiIndex.from_frame(post_cells[post_cells.k == k][["StyleCode", "WeekStart"]])
                ind = key.isin(sel).astype(float)
                for j, chn in enumerate(self.chs):
                    cols.append((ind * (ch == j))[:, None]); names.append(f"post{k}_{chn}"); self.post_names.append(names[-1])
        x = np.where(bf > 0, 0.0, np.log(1 - P.d.values))
        self.x = x
        self.treat_names = []
        if spec == "cc":
            for c in self.cats:
                for j, chn in enumerate(self.chs):
                    cols.append((x * (P.Category == c).values * (ch == j))[:, None]); names.append(f"eps_{c}_{chn}"); self.treat_names.append(names[-1])
        elif spec == "cat":
            for c in self.cats:
                cols.append((x * (P.Category == c).values)[:, None]); names.append(f"eps_{c}"); self.treat_names.append(names[-1])
            cols.append((x * (ch == 0))[:, None]); names.append("eps_online_shift"); self.treat_names.append(names[-1])
        elif spec == "pooled":
            for j, chn in enumerate(self.chs):
                cols.append((x * (ch == j))[:, None]); names.append(f"eps_{chn}"); self.treat_names.append(names[-1])
        else:
            raise ValueError(spec)
        self.B = np.hstack(cols)
        self.names = names
        self.ti = [names.index(n) for n in self.treat_names]
        self.pi = [names.index(n) for n in self.post_names]

    def rows_for(self, model_idx):
        return np.concatenate([np.arange(m * self.BLOCK, (m + 1) * self.BLOCK) for m in model_idx])

    def matrix(self, model_idx, fe="model"):
        rows = self.rows_for(model_idx)
        X = self.B[rows]
        K = len(model_idx)
        if fe == "model":                                       # model x kanał
            k_of_row = np.repeat(np.arange(K), self.BLOCK)
            F = np.zeros((len(rows), 2 * K)); F[np.arange(len(rows)), k_of_row * 2 + self.ch[rows]] = 1
        elif fe == "cat":                                       # tylko kategoria x kanał (bez efektów modelu)
            F = np.zeros((len(rows), 2 * len(self.cats))); F[np.arange(len(rows)), self.cat_i[rows] * 2 + self.ch[rows]] = 1
        else:
            raise ValueError(fe)
        return rows, np.hstack([X, F])

    def fit(self, model_idx=None, fe="model", cov=False):
        model_idx = np.arange(self.M) if model_idx is None else np.asarray(model_idx)
        rows, X = self.matrix(model_idx, fe)
        y = self.y[rows]
        b, mu, Ainv = ppml(X, y)
        out = dict(rows=rows, X=X, y=y, b=b, mu=mu, Ainv=Ainv)
        if cov:
            out["V"] = cluster_cov(X, y - mu, Ainv, np.arange(len(model_idx)) * self.BLOCK)
        return out

    def eff(self, b, rows=None):
        """Efekt (skala log) leczenia i tygodni po akcji w wierszach panelu: x_i' beta_treat oraz post_i' beta_post."""
        B = self.B if rows is None else self.B[rows]
        e = B[:, self.ti] @ b[self.ti]
        e_post = B[:, self.pi] @ b[self.pi] if self.pi else np.zeros(len(B))
        return e, e_post

    def strat_draw(self, rng):
        """Losowanie modeli ze zwracaniem w obrębie kategorii (zachowuje liczność kategorii)."""
        out = []
        for ci in range(len(self.cats)):
            ids = np.where(self.model_cat == ci)[0]
            out.extend(rng.choice(ids, size=len(ids), replace=True))
        return np.array(out)


def event_study(Pm, treated, control, weeks_rel, bf_start, harm=False):
    """Event study (PPML): modele `treated` vs `control` w tygodniach z `weeks_rel` (WeekStart -> tydzień względem startu akcji).

    Tydzień -1 to punkt odniesienia; tydzień Black Friday jest wyrzucany z próby (rabat na wszystkich modelach naraz).
    Zwraca (lista rel, współczynniki, ich macierz kowariancji klastrowana po modelach, próba).
    """
    P = Pm[Pm.StyleCode.isin(list(treated) + list(control)) & Pm.WeekStart.isin(list(weeks_rel)) & (Pm.WeekStart != bf_start)].copy()
    P = P.sort_values(["StyleCode", "Channel", "WeekStart"]).reset_index(drop=True)
    P["rel"] = P.WeekStart.map(weeks_rel)
    P["tr"] = P.StyleCode.isin(treated).astype(int)
    rels = sorted(r for r in set(P.rel) if r != -1)
    cols, names = [], []
    wk = pd.get_dummies(P.Channel.astype(str) + "|" + P.WeekStart.dt.strftime("%Y%m%d"), dtype=float)
    cols.append(wk.values); names += list(wk.columns)
    mfe = pd.get_dummies(P.StyleCode + "|" + P.Channel.astype(str), dtype=float)
    cols.append(mfe.values); names += list(mfe.columns)
    if harm:
        ang = 2 * np.pi * P.woy.values / 52.0
        for c in sorted(P.Category.unique()):
            m = (P.Category == c).values.astype(float)
            for k in (1, 2):
                cols.append((m * np.sin(k * ang))[:, None]); names.append(f"s{k}{c}")
                cols.append((m * np.cos(k * ang))[:, None]); names.append(f"c{k}{c}")
    ev_names = []
    for r in rels:
        cols.append(((P.rel == r) & (P.tr == 1)).values.astype(float)[:, None]); names.append(f"rel{r:+d}"); ev_names.append(f"rel{r:+d}")
    X = np.hstack(cols)
    y = P.Qty.values.astype(float)
    b, mu, Ainv = ppml(X, y)
    sm = P.StyleCode.values
    starts = np.r_[0, np.where(sm[1:] != sm[:-1])[0] + 1]
    V = cluster_cov(X, y - mu, Ainv, starts)
    ii = [names.index(n) for n in ev_names]
    return rels, b[ii], V[np.ix_(ii, ii)], P
