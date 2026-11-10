"""Rejestruje metodę główną M1a (wskazaną z góry w fazie 6 notebooka BC-04) jako model z aliasem `kandydat`.

To NIE jest rekomendacja: w walidacji M1a nie pobiła B1 (zob. MODEL_CARD.md). Alias `kandydat` oznacza „do przeglądu”.
Użycie: MLFLOW_TRACKING_URI=http://127.0.0.1:5000 PYTHONPATH=src python src/register_model.py
"""
import json
import os
import tempfile
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import bc04_core as core
import bc04_model
import log_runs

HERE = Path(__file__).resolve().parents[1]
MODEL_NAME = "bc04-sell-through-risk"
ALIAS = "kandydat"


def card(vm: dict, n_models: dict, rng: dict, dv: str, cv: dict, val_run_id: str) -> str:
    m = vm
    return f"""# Karta modelu: {MODEL_NAME} (metoda M1a)

**Status: kandydat do przeglądu, NIE rekomendacja.** M1a to metoda główna wskazana z góry w fazie 6 notebooka BC-04. W walidacji po kolekcjach ma Brier {m['brier']:.3f} i jest **gorsza** niż prosta ekstrapolacja B1. Rekomendacja z fazy 8 oryginału nie powstała.

## Co przewiduje (etykieta, dokładnie jak w notebooku)
`risk = 1`, gdy sell-through narastający modelu (`StyleCode`, cała sieć) w dniu 55 od pierwszej faktycznej sprzedaży (koniec 8. tygodnia) jest niższy niż próg τ = {core.TAU:.0%}. Sell-through = sprzedane / (sprzedane + stan), narastająco od premiery, sumowany po SKU i lokalizacjach. Populacja: modele bez rabatu do dnia 55 (66 z 72; 6 przecenionych od dnia 42 wykluczono, bo ich etykieta jest zmieszana z rabatem).

## Wejście (kolejność nieistotna, nazwy obowiązkowe)
| Cecha | Jednostka / definicja |
|---|---|
| `pred55` | ekstrapolacja liniowa sell-through na dzień 55 z tempa ostatnich 14 dni [udział 0-1] |
| `st_d` | sell-through narastający w dniu decyzji [udział 0-1] |
| `trend` | ln((sprzedaż 7 dni + 1) / (sprzedaż 7 dni wcześniej + 1)) [bez jednostki] |
| `avail_core` | udział SKU w rozmiarach M, L, ONE ze stanem > 0 w sieci [udział 0-1]; w uczeniu bez zmienności, współczynnik = 0 |
| `restock` | supply_d / supply_0 - 1: uzupełnienia dostaw do dnia decyzji [udział] |
| `ln_price` | ln(cena netto modelu w PLN) |
| `k` | tydzień decyzji od pierwszej sprzedaży (liczba całkowita) |

Cechy liczone wyłącznie z danych do końca dnia decyzji. Definicje: notebook BC-04, sekcja „Transform: tabela modelowa”.

## Wyjście
Tabela: `p_risk` (prawdopodobieństwo `risk = 1`, 0-1; NaN poza zakresem) i `status` (`ok` albo `poza zakresem: <powód>`).

## Zakres ważności
- Tygodnie decyzji `k` = {bc04_model.K_RANGE[0]}-{bc04_model.K_RANGE[1]} (dni 13-48). Inny `k` zwraca status „poza zakresem”, bez ekstrapolacji.
- Cecha poza przedziałem widzianym w uczeniu także daje „poza zakresem”: {json.dumps(rng, ensure_ascii=False)}. Dla `avail_core` nie ma przedziału (stała w uczeniu).
- Wartość spoza [0, 1] w `pred55`, `st_d`, `avail_core`, brak kolumny lub NaN: błąd (ValueError), nie wynik.

## Uczenie i walidacja
- Uczenie: regresja logistyczna (StandardScaler + L2, C = 1), {n_models['all']} modeli z kolekcji SS25, AW25, SS26 ({n_models['SS25']} / {n_models['AW25']} / {n_models['SS26']}), 396 wierszy model x moment. Ziarno {core.SEED}.
- Walidacja po kolekcjach (LOCO, wartości out-of-fold z uruchomienia `{val_run_id}`): Brier {m['brier']:.3f} [{m['brier_ci90_lo']:.3f}; {m['brier_ci90_hi']:.3f}], log loss {m['log_loss']:.3f}, AUC {m['auc']:.3f}, ECE (5 przedziałów) {m['ece_5']:.3f}. Brier per kolekcja: SS25 {m['brier__SS25']:.3f}, AW25 {m['brier__AW25']:.3f}, SS26 {m['brier__SS26']:.3f}. Przedział: bootstrap po modelach, 90%.
- Kalibracja: brak osobnej kalibracji (surowe wyjście regresji logistycznej). Wykres: artefakt `calibration.png` w uruchomieniu walidacyjnym.
- Próg decyzyjny i założenia kosztowe (parametry uruchomienia): δ = 20%, Δ = 25 p.p., h = 1,5%/mies., m = 2, ε = 50%, τ = 60%. **Próg decyzyjny dla tego modelu nie jest ustalony** (wymagałby fazy 8 oryginału).

## Znane ograniczenia
- Jedna zakończona kolekcja AW (AW25, 22 modele); kurtki i swetry (większość AW26) mają w historii dokładnie jedną kolekcję. Moc wniosków jest mała, a przedziały szerokie.
- Stany magazynowe pochodzą z jednorazowego eksportu o nieznanej jakości (99,9% spójności ze sprzedażą w audycie), brak danych o dostawach (uzupełnienia widać tylko jako wzrost stanu).
- W foldzie AW25 błąd jest wyraźnie większy (Brier {m['brier__AW25']:.3f}) niż w SS25 i SS26.
- Model uczony na wszystkich 66 modelach; metryki walidacyjne dotyczą wersji uczonych bez testowanej kolekcji, nie tego samego obiektu.
- Modele AW26 z transzy sierpniowej (wiek > 7 tygodni) są poza zakresem; czy rozszerzyć zakres, to pytanie do zleceniodawcy.

## Wersje
Dane: sha256 {dv[:16]}; kod: commit {cv['git_commit']}, `bc04_core.py` sha256 {cv['core_sha256']}.
"""


def main():
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
    client = MlflowClient()
    last = json.loads((HERE / "reference" / "last_suite.json").read_text())
    exp = client.get_experiment_by_name(last["experiment"])
    val_run = client.search_runs([exp.experiment_id], filter_string=f"tags.suite_id = '{last['suite_id']}' and params.method = 'M1a'")[0]
    vm = val_run.data.metrics

    dv, cv = log_runs.data_version(), log_runs.code_version()
    ds = core.build_dataset(log_runs.DATA, HERE / "cache")
    D = ds.D
    n_models = {"all": D.StyleCode.nunique(), **{c: D[D.Collection == c].StyleCode.nunique() for c in core.COLLS}}
    feats = bc04_model.FEATURES
    pipe = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)).fit(D[feats], core.label(D, core.TAU))
    rng = {c: [float(D[c].min()), float(D[c].max())] for c in feats if c not in ("k", "avail_core")}
    contract = {"features": feats, "k_range": list(bc04_model.K_RANGE), "training_range": rng}

    mlflow.set_experiment(last["experiment"])
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        joblib.dump(pipe, td / "pipe.joblib")
        (td / "contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=1), encoding="utf-8")
        text = card(vm, n_models, rng, dv, cv, val_run.info.run_id)
        (td / "MODEL_CARD.md").write_text(text, encoding="utf-8")
        (HERE / "MODEL_CARD.md").write_text(text, encoding="utf-8")

        X = D[feats].head(5)
        wrapper = bc04_model.Bc04RiskModel()
        class _Ctx:  # minimalny kontekst tylko do wyliczenia sygnatury przed zapisem
            artifacts = {"pipe": str(td / "pipe.joblib"), "contract": str(td / "contract.json")}
        wrapper.load_context(_Ctx)
        sig = infer_signature(X, wrapper.predict(None, X))

        with mlflow.start_run(run_name=f"model__M1a__{dv[:8]}") as run:
            mlflow.log_params({"method": "M1a", "features": ",".join(feats), "seed": core.SEED, "tau": core.TAU, "k_range": str(bc04_model.K_RANGE),
                               "decision_threshold": "nie ustalony", **{f"cost_{k}": v for k, v in core.COST.items() if k != "tau"}})
            mlflow.set_tags({"kind": "model", "validation_run_id": val_run.info.run_id, "data_version_sha256": dv, "git_commit": cv["git_commit"],
                             "code_sha256_core": cv["core_sha256"], "status": "kandydat (nie rekomendacja)"})
            info = mlflow.pyfunc.log_model(name="model", python_model=wrapper, artifacts={"pipe": str(td / "pipe.joblib"), "contract": str(td / "contract.json")},
                                           signature=sig, input_example=X, code_paths=[str(HERE / "src" / "bc04_model.py")],
                                           registered_model_name=MODEL_NAME, pip_requirements=["mlflow==3.5.0", "scikit-learn==1.9.1", "pandas==2.3.3", "numpy==2.5.4", "joblib"])
            mlflow.log_artifact(str(td / "MODEL_CARD.md"))

    version = str(max(int(v.version) for v in client.search_model_versions(f"name='{MODEL_NAME}'")))
    client.update_registered_model(MODEL_NAME, description="Ryzyko niedoboru sell-through (< 60% w dniu 55) dla modelu sezonowego Nordvik; metoda M1a. Kandydat, nie rekomendacja. Zob. MODEL_CARD.md.")
    for k, v in {"data_version_sha256": dv[:16], "decision_weeks": f"{bc04_model.K_RANGE[0]}-{bc04_model.K_RANGE[1]}", "validation_status": "walidacja LOCO: gorsza niż B1",
                 "validation_run_id": val_run.info.run_id, "label": "ST(dzień 55) < 60%", "n_models_train": str(n_models["all"])}.items():
        client.set_model_version_tag(MODEL_NAME, version, k, v)
    client.set_registered_model_alias(MODEL_NAME, ALIAS, version)
    print(f"zarejestrowano {MODEL_NAME} v{version}, alias @{ALIAS}, model_uri={info.model_uri}")


if __name__ == "__main__":
    main()
