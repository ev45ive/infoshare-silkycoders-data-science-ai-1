"""Trwałość zatwierdzenia po awarii procesu (dwa osobne procesy) oraz zgodność kopii rdzenia z zamrożonym rdzeniem."""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVICE = HERE.parent
ANALIZA = SERVICE.parents[1]
PY = sys.executable


def _run(*args):
    r = subprocess.run([PY, str(HERE / "restart_helper.py"), *args], capture_output=True, text=True, encoding="utf-8", cwd=str(SERVICE), timeout=240,
                       env={**__import__("os").environ, "PYTHONUTF8": "1"})
    assert r.returncode == 0, r.stderr[-800:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_pending_approval_survives_process_crash_and_executes_exactly_once():
    """Zadanie czekające na zatwierdzenie przetrwa nagłe zakończenie procesu; decyzja wykonuje się dokładnie raz, bez zdublowanych szkiców."""
    p1 = _run("phase1")                                   # proces 1 kończy się os._exit(0) w trakcie oczekiwania na zatwierdzenie
    p2 = _run("phase2", json.dumps(p1))                   # proces 2: nowy silnik, ten sam thread_id w bazie stanu
    assert p2["first"] == 200 and p2["status"] == "zatwierdzone"
    assert p2["second"] == 404                            # drugie kliknięcie nic nie robi
    assert p2["tasks_in_thread"] == 1                     # brak zdublowanych szkiców po wznowieniu
    assert p2["pending_after"] is None and "zatwierdzone" in p2["last_message"]


def _ast(p):
    # Odcisk struktury kodu (AST) bez komentarzy i układu linii. Ten sam algorytm co w _build/freeze_final.py (ast_fp).
    return hashlib.sha256(ast.dump(ast.parse(Path(p).read_text(encoding="utf-8"))).encode()).hexdigest()[:16]


def test_core_copy_differs_from_frozen_core_only_by_declared_di_patches():
    """Kopia rdzenia w usłudze różni się od zamrożonego rdzenia wyłącznie trzema zadeklarowanymi łatkami wstrzykiwania zależności; oryginał jest nietknięty."""
    frozen_dir, core_dir = ANALIZA / "src" / "asystent", SERVICE / "core"
    frozen = json.loads((ANALIZA / "wyniki" / "zamrozenie_konfiguracji.json").read_text(encoding="utf-8"))["ast_sha256_16"]
    changed = []
    for f in sorted(core_dir.glob("*.py")):
        key = f"src/asystent/{f.name}"
        if _ast(f) != frozen.get(key):
            changed.append(f.name)
    assert set(changed) == {"agent.py", "config.py", "tools.py"}, changed          # tylko deklarowane łatki wstrzykiwania zależności
    for name in ("prompts.py", "db.py", "docs.py", "forecast.py", "llm.py", "tasks.py"):
        assert _ast(core_dir / name) == frozen[f"src/asystent/{name}"]     # prompty, kontrole SQL, dokumenty, prognoza, limity: kod bez zmian
    # oryginał nietknięty od zamrożenia: porównujemy strukturę kodu, a nie bajty (do plików dopisano wyłącznie komentarze)
    assert all(_ast(ANALIZA / k) == v for k, v in frozen.items())
