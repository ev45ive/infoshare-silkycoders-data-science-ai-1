"""E1: test klienta z hosta (parametr, metryka, artefakt, model: zapis i odczyt z serwera)."""
import inspect
import os
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
from mlflow import MlflowClient
from sklearn.linear_model import LogisticRegression

URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(URI)
print("klient mlflow:", mlflow.__version__, "| serwer:", URI)
print("sygnatura log_model (sklearn):", inspect.signature(mlflow.sklearn.log_model))

mlflow.set_experiment("bc04-e1-test-klienta")
X = np.array([[0.0], [1.0], [2.0], [3.0]])
y = np.array([0, 0, 1, 1])
with mlflow.start_run(run_name="e1-test") as run:
    mlflow.log_param("metoda", "test")
    mlflow.log_metric("brier", 0.25)
    with tempfile.TemporaryDirectory() as td:
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.set_title("test artefaktu")
        p = Path(td) / "wykres.png"
        fig.savefig(p)
        mlflow.log_artifact(str(p))
    info = mlflow.sklearn.log_model(LogisticRegression().fit(X, y), name="model", input_example=X[:2])

c = MlflowClient()
r = c.get_run(run.info.run_id)
assert r.data.params["metoda"] == "test" and abs(r.data.metrics["brier"] - 0.25) < 1e-12
arts = [a.path for a in c.list_artifacts(run.info.run_id)]
assert "wykres.png" in arts, arts
loaded = mlflow.sklearn.load_model(info.model_uri)
assert loaded.predict(X).tolist() == [0, 0, 1, 1]
print("OK: parametr, metryka, artefakt i model zapisane i odczytane;", "model_uri:", info.model_uri)
