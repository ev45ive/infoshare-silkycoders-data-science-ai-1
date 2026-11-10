"""Opakowanie metody M1a (regresja logistyczna) jako model MLflow: cechy na wejściu, prawdopodobieństwo ryzyka na wyjściu.

Kontrakt (MODEL_CARD.md): wiek modelu poza zakresem walidacji zwraca status „poza zakresem”, nigdy cichą ekstrapolację.
"""
import json

import joblib
import mlflow.pyfunc
import numpy as np
import pandas as pd

FEATURES = ["pred55", "st_d", "trend", "avail_core", "restock", "ln_price", "k"]
K_RANGE = (2, 7)  # tygodnie decyzji użyte w uczeniu i walidacji (dni 13-48)
UNIT_INTERVAL = ["pred55", "st_d", "avail_core"]


class Bc04RiskModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.pipe = joblib.load(context.artifacts["pipe"])
        self.contract = json.loads(open(context.artifacts["contract"], encoding="utf-8").read())

    def predict(self, context, model_input, params=None):
        X = pd.DataFrame(model_input)
        missing = [c for c in FEATURES if c not in X.columns]
        if missing:
            raise ValueError(f"brak kolumn wejściowych: {missing}")
        X = X[FEATURES].astype(float)
        if X.isna().any().any():
            raise ValueError("wejście zawiera braki danych (NaN)")
        bad = [c for c in UNIT_INTERVAL if not X[c].between(0, 1).all()]
        if bad:
            raise ValueError(f"wartość poza dopuszczalnym przedziałem [0, 1]: {bad}")

        status = pd.Series("ok", index=X.index, dtype=object)
        for c, (lo, hi) in self.contract["training_range"].items():
            out = ~X[c].between(lo, hi)
            status[out & (status == "ok")] = f"poza zakresem: {c} poza przedziałem uczenia [{lo:.3g}; {hi:.3g}]"
        k_out = ~X["k"].between(*K_RANGE)  # wiek ma pierwszeństwo przed pozostałymi powodami
        status[k_out] = [f"poza zakresem: tydzień decyzji k={int(k)} poza walidowanym zakresem {K_RANGE[0]}-{K_RANGE[1]}" for k in X.loc[k_out, "k"]]

        p = np.full(len(X), np.nan)
        ok = (status == "ok").to_numpy()
        if ok.any():
            p[ok] = self.pipe.predict_proba(X.loc[ok])[:, 1]
        return pd.DataFrame({"p_risk": p, "status": status.to_numpy()})
