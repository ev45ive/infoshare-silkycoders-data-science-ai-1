"""Uruchamia KOPIĘ notebooka BC-04 (oryginał bez zmian) i zapisuje liczby referencyjne do parytetu."""
import os
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parents[1]
SRC_NB = HERE.parent / "bc04-sell-through-przecena.ipynb"
OUT = HERE / "reference"
OUT.mkdir(exist_ok=True)
os.environ["NORDVIK_BC04_DATA"] = str((HERE.parents[2] / "datasets/synthetic/bc04").resolve())

nb = nbformat.read(SRC_NB, as_version=4)
nb.cells.append(nbformat.v4.new_code_cell(
    "O.to_parquet('ref_O_final.parquet'); tab6.to_csv('ref_tab6.csv'); dt.to_csv('ref_pairs.csv'); D.to_parquet('ref_D.parquet')"
))
t0 = time.time()
NotebookClient(nb, timeout=7200, kernel_name="python3", resources={"metadata": {"path": str(OUT)}}).execute()
(OUT / "elapsed_s.txt").write_text(f"{time.time() - t0:.1f}\n")
nbformat.write(nb, OUT / "bc04-executed-copy.ipynb")
print("OK, czas [s]:", round(time.time() - t0, 1))
