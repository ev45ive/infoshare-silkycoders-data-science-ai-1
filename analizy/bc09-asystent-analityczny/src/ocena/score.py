"""Ocena surowych wyników: tabela per pytanie i agregaty z przedziałami Wilsona."""
import json

import pandas as pd

from asystent import config, docs
from . import oceniacz

_HERE = __import__("pathlib").Path(__file__).parent
SPECS_DEV = json.load(open(_HERE / "checks_dev.json", encoding="utf-8"))
SPECS_DEV.update(json.load(open(_HERE / "dev_extra.json", encoding="utf-8"))["checks"])


def corpus():
    return oceniacz.load_corpus(docs.load_docs()[0])


def score_file(path, specs=SPECS_DEV):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    cor = corpus()
    out = []
    for r in rows:
        spec = specs.get(r["id"])
        if not isinstance(spec, dict):
            continue
        s = oceniacz.evaluate(r, spec, cor)
        out.append({"id": r["id"], "category": r["category"], "variant": r["variant"], "run": r["run"],
                    "tokens": r["tokens_in"] + r["tokens_out"], "steps": r["steps"], "latency_s": r["latency_s"],
                    "error": r["error"], **{k: v for k, v in s.items() if k != "checks"},
                    "failed": ",".join(k for k in s["checks"] if not s[k])})
    return pd.DataFrame(out)


def summary(df):
    """Poprawność wg kategorii z przedziałem Wilsona."""
    rows = []
    for cat, g in list(df.groupby("category")) + [("RAZEM", df)]:
        k, n = int(g["correct"].sum()), len(g)
        lo, hi = oceniacz.wilson(k, n)
        rows.append({"kategoria": cat, "poprawne": k, "n": n, "odsetek": round(k / n, 3), "wilson_95": f"{lo:.2f}-{hi:.2f}",
                     "tokeny_śr": int(g["tokens"].mean()), "kroki_śr": round(g["steps"].mean(), 1), "czas_s_śr": round(g["latency_s"].mean(), 1)})
    return pd.DataFrame(rows)
