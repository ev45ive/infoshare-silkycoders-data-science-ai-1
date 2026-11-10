"""E3: jedno uruchomienie MLflow na metodę z poprzedniego zadania (walidacja LOCO), jawne logowanie bez autologu.

Użycie: MLFLOW_TRACKING_URI=http://127.0.0.1:5000 python src/log_runs.py [--experiment NAZWA]
Nie loguje sekretów ani zmiennych środowiskowych; artefakty to małe pliki (wykres, prognozy walidacyjne, cechy).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
from mlflow import MlflowClient
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import bc04_core as core

HERE = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv("NORDVIK_BC04_DATA", HERE.parents[2] / "datasets/synthetic/bc04")).resolve()
EXPERIMENT = "bc04-sell-through-przecena"

STATUS = {"B0g": "punkt_odniesienia", "B0": "punkt_odniesienia", "B1": "punkt_odniesienia", "B2": "punkt_odniesienia",
          "M1a": "kandydat (metoda główna wskazana z góry)", "M1r": "kandydat", "M2": "kandydat", "M2 + Platt": "kandydat",
          "M2 + izotoniczna": "kandydat", "M3": "kandydat",
          "M1a bez avail_core": "ablacja", "M1a bez ln_price": "ablacja", "M1a bez restock": "ablacja"}


def data_version() -> str:
    h = hashlib.sha256()
    for t in core.TABLES:
        h.update(hashlib.sha256((DATA / f"{t}.parquet").read_bytes()).digest())
    return h.hexdigest()


def code_version() -> dict:
    sha = hashlib.sha256((Path(core.__file__)).read_bytes()).hexdigest()[:16]
    try:
        commit = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = "brak-git"
    return {"git_commit": commit, "core_sha256": sha}


def fold_metrics(O: pd.DataFrame, m: str, tau: float) -> dict:
    """Metryki zbiorcze (z przedziałem bootstrap po modelach) i per kolekcja testowa (fold LOCO)."""
    bs = core.boot_setup(O)
    br, brci = core.boot_mean(O, core.sq_err(O, m), bs)
    ll, _ = core.boot_mean(O, core.log_loss_rows(O, m), bs)
    ct, ctci = core.boot_mean(O, core.rule_cost(O, m, tau), bs)
    cth, _ = core.boot_mean(O, core.rule_cost(O, m, tau, "theory"), bs)
    out = {"brier": br, "brier_ci90_lo": brci[0], "brier_ci90_hi": brci[1], "log_loss": ll, "auc": core.auc(O, m),
           "ece_5": core.ece(O["p__" + m], O.y), "cost_per_row_tuned": ct, "cost_tuned_ci90_lo": ctci[0], "cost_tuned_ci90_hi": ctci[1],
           "cost_per_row_theory": cth, "n_rows": len(O), "n_models": O.StyleCode.nunique(), "risk_base_rate": O.y.mean()}
    for c in core.COLLS:
        g = O[O.Collection == c]
        out[f"brier__{c}"] = core.sq_err(g, m).mean()
        out[f"log_loss__{c}"] = core.log_loss_rows(g, m).mean()
        out[f"cost_per_row_tuned__{c}"] = core.rule_cost(g, m, tau).mean()
        out[f"n_rows__{c}"], out[f"n_models__{c}"] = len(g), g.StyleCode.nunique()
        if g.y.nunique() > 1:
            out[f"auc__{c}"] = core.auc(g, m)
    return out


def calibration_png(O, m, path):
    cc = core.calib_curve(O, m)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.errorbar(cc.p_śr, cc.udział, yerr=[cc.udział - cc.od, cc.do - cc.udział], fmt="o-", capsize=3)
    ax.plot([0, 1], [0, 1], "k:", lw=0.8)
    ax.set_title(f"{m}: kalibracja (LOCO, {O.StyleCode.nunique()} modeli)")
    ax.set_xlabel("przewidywane prawdopodobieństwo ryzyka [-]")
    ax.set_ylabel("faktyczny udział ryzykownych (τ = 60%) [-]")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def coefficients(D: pd.DataFrame, m: str) -> pd.DataFrame | None:
    feats = core.FEATURES[m]
    if m.startswith("M1a"):
        est = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)).fit(D[feats], core.label(D, core.TAU))
        return pd.DataFrame({"cecha": feats, "wspolczynnik_std": est[-1].coef_[0]})
    if m == "M1r":
        est = make_pipeline(StandardScaler(), Ridge(alpha=3.0)).fit(D[feats], D.st55)
        return pd.DataFrame({"cecha": feats, "wspolczynnik_std": est[-1].coef_})
    return None


def common_tags(kind, status, reason, suite, dv, cv, scope):
    return {"kind": kind, "status": status, "reason": reason, "suite_id": suite, "data_version_sha256": dv, "git_commit": cv["git_commit"],
            "code_sha256_core": cv["core_sha256"], "decision_days": ",".join(map(str, core.DAYS)), "validation": "LOCO po kolekcjach (SS25, AW25, SS26)",
            "scope": scope}


def common_params(extra: dict) -> dict:
    p = {"seed": core.SEED, "tau": core.TAU, "decision_days": str(core.DAYS), "validation": "LOCO", "bootstrap": "po modelach, B=1000, 90%",
         **{f"cost_{k}": v for k, v in core.COST.items() if k != "tau"}}
    p.update(extra)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", default=EXPERIMENT)
    args = ap.parse_args()
    plt.switch_backend("Agg")
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
    mlflow.set_experiment(args.experiment)
    client = MlflowClient()
    dv, cv, suite = data_version(), code_version(), uuid.uuid4().hex[:8]
    print("klient", mlflow.__version__, "| dane", dv[:12], "| kod", cv, "| suite", suite)

    t_all = time.time()
    t0 = time.time()
    ds = core.build_dataset(DATA, HERE / "cache")
    t_data = time.time() - t0
    D = ds.D
    scope = f"{D.StyleCode.nunique()} modeli (bez 6 cenzurowanych), {len(D)} wierszy model x moment"

    for m, f in core.METH.items():
        t0 = time.time()
        methods = {m: f, "B1": core.m_B1} if m == "M3" else {m: f}
        O = core.run_cv(methods, core.TAU, D)
        n_fallback = int(O["p__M3"].isna().sum()) if m == "M3" else 0
        if m == "M3":
            O["p__M3"] = O["p__M3"].fillna(O["p__B1"])
        t_val = time.time() - t0
        met = fold_metrics(O, m, core.TAU)
        met["validation_elapsed_s"] = t_val
        params = common_params({"method": m, "features": ",".join(core.FEATURES[m]), "hyperparameters": core.HYPER[m],
                                "m3_fallback_rows": n_fallback if m == "M3" else "n/a"})
        reason = {"M1a": "metoda główna wskazana z góry w fazie 6; w notebooku nie pobiła B1"}.get(m, "")
        with mlflow.start_run(run_name=f"{m}__loco__{dv[:8]}"):
            mlflow.log_params(params)
            mlflow.set_tags(common_tags("metoda", STATUS[m], reason, suite, dv, cv, scope))
            mlflow.log_metrics({k: float(v) for k, v in met.items()})
            mlflow.log_dict({"method": m, "features": core.FEATURES[m]}, "features.json")
            with tempfile.TemporaryDirectory() as td:
                calibration_png(O, m, Path(td) / "calibration.png")
                mlflow.log_artifact(str(Path(td) / "calibration.png"))
                oof = O[["StyleCode", "Collection", "Category", "k", "d", "y", "st_d", "st55"]].assign(p=O["p__" + m], thr_tuned=O["thr__" + m], thr_theory=O.thr_theory)
                oof.to_csv(Path(td) / "oof_predictions.csv", index=False)
                mlflow.log_artifact(str(Path(td) / "oof_predictions.csv"))
                coef = coefficients(D, m)
                if coef is not None:
                    coef.to_csv(Path(td) / "coefficients.csv", index=False)
                    mlflow.log_artifact(str(Path(td) / "coefficients.csv"))
        print(f"{m:22s} Brier {met['brier']:.4f} | LL {met['log_loss']:.4f} | AUC {met['auc']:.4f} | czas {t_val:5.1f}s")

    # polityki bez modelu i reguła kosztowa EV: koszt decyzji bez prognozy (pytanie: czy metoda bije dzisiejszą praktykę)
    Op = core.add_ev(core.run_cv({"B0g": core.m_B0g}, core.TAU, D), D)
    ct = core.cost_table(Op, core.TAU)
    pol = dict(core.basic_policies(Op, core.TAU))
    pol["reguła kosztowa EV (M1r)"] = Op.flag__EV.to_numpy()
    bs = core.boot_setup(Op)
    for name, fl in pol.items():
        v = np.where(fl, ct.c_flag, ct.c_no)
        est, ci = core.boot_mean(Op, v, bs)
        met = {"cost_per_row_tuned": est, "cost_tuned_ci90_lo": ci[0], "cost_tuned_ci90_hi": ci[1], "n_rows": len(Op), "n_models": Op.StyleCode.nunique(),
               "flag_share": float(np.mean(fl))}
        for c in core.COLLS:
            ix = (Op.Collection == c).to_numpy()
            met[f"cost_per_row_tuned__{c}"] = float(v[ix].mean())
            met[f"n_rows__{c}"], met[f"n_models__{c}"] = int(ix.sum()), Op[ix].StyleCode.nunique()
        with mlflow.start_run(run_name=f"polityka: {name}__loco__{dv[:8]}"):
            mlflow.log_params(common_params({"method": name, "features": "", "hyperparameters": "polityka bez modelu (koszt decyzji)"}))
            mlflow.set_tags(common_tags("polityka", "punkt_odniesienia", "porównanie kosztu z dzisiejszą praktyką", suite, dv, cv, scope))
            mlflow.log_metrics({k: float(v_) for k, v_ in met.items()})
        print(f"[polityka] {name:42s} koszt/wiersz {est:,.0f}")

    total = time.time() - t_all
    for r in client.search_runs([client.get_experiment_by_name(args.experiment).experiment_id], filter_string=f"tags.suite_id = '{suite}'"):
        client.set_tag(r.info.run_id, "suite_elapsed_s", f"{total:.1f}")
        client.set_tag(r.info.run_id, "suite_data_build_s", f"{t_data:.1f}")
    print(f"Pełne porównanie: {total:.1f}s (w tym dane i M3: {t_data:.1f}s) | suite_id={suite}")
    (HERE / "reference").mkdir(exist_ok=True)
    (HERE / "reference" / "last_suite.json").write_text(json.dumps({"suite_id": suite, "experiment": args.experiment, "elapsed_s": total}))


if __name__ == "__main__":
    main()
