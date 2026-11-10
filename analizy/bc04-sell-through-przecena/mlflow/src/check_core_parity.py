"""Parytet rdzenia (bc04_core) z notebookiem, bez MLflow: tabela modelowa D i prognozy out-of-fold."""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import bc04_core as core

HERE = Path(__file__).resolve().parents[1]
REF = HERE / "reference"
DATA = HERE.parents[2] / "datasets/synthetic/bc04"

t0 = time.time()
ds = core.build_dataset(DATA, HERE / "cache")
print(f"dane + M3: {time.time() - t0:.1f}s")
Dref = pd.read_parquet(REF / "ref_D.parquet")
num = [c for c in Dref.columns if Dref[c].dtype.kind in "fi" and c in ds.D.columns]
print("D: kształt", ds.D.shape, Dref.shape, "| max |różnica| cech:", float(np.nanmax(np.abs(ds.D[num].to_numpy() - Dref[num].to_numpy()))))

t0 = time.time()
O = core.run_main_cv(ds)
print(f"LOCO wszystkie metody: {time.time() - t0:.1f}s")
Oref = pd.read_parquet(REF / "ref_O_final.parquet")
for m in core.METH:
    print(f"{m:22s} max |p - p_ref| = {np.max(np.abs(O['p__' + m].to_numpy() - Oref['p__' + m].to_numpy())):.3e}")
print("flag EV zgodna:", bool((O.flag__EV.to_numpy() == Oref.flag__EV.to_numpy()).all()))
