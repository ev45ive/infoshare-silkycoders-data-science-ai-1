"""Regresja jakości usługi przez REST na rzeczywistym modelu (koszt: tokeny z rejestru 3 mln). Użycie: python regression_rest.py <dev|test> <run>.
Zapisuje surowe odpowiedzi do usluga/wyniki/rest_<split>_r<run>.jsonl w formacie zgodnym z oceniaczem z analizy (status 'oczekuje' = szkic do zatwierdzenia).
Zbiór testowy: uruchamiany jednorazowo i NIE oceniany (klucz poza zasięgiem)."""
import dataclasses
import json
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVICE = HERE.parent
ANALIZA = SERVICE.parents[1]
sys.path.insert(0, str(SERVICE)); sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ANALIZA / "src"))
from fastapi.testclient import TestClient  # noqa: E402

from conftest import login                  # noqa: E402
from ocena import runner                    # noqa: E402
from svc import auth                        # noqa: E402
from svc.api import create_app              # noqa: E402
from svc.config import get_settings         # noqa: E402

split, run = sys.argv[1], int(sys.argv[2])
settings = dataclasses.replace(get_settings(), daily_token_limit=5_000_000)      # regresja zużywa więcej niż domyślny limit dzienny pilotażu
out = SERVICE.parent / "wyniki" / f"rest_{split}_r{run}.jsonl"
out.parent.mkdir(exist_ok=True)
done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")} if out.exists() else set()
with TestClient(create_app(settings)) as c:                                      # prawdziwy model: brak base_chat
    store = c.app.state.store
    user = {"name": f"reg_{uuid.uuid4().hex[:8]}", "pw": uuid.uuid4().hex}
    store.create_user(user["name"], auth.hash_password(user["pw"]), "requester")
    h = login(c, user)
    with open(out, "a", encoding="utf-8") as f:
        for q in runner.load_gold(split):
            if q["id"] in done:
                continue
            t0 = time.time()
            tid = c.post("/threads", json={}, headers=h).json()["thread_id"]
            r = c.post(f"/threads/{tid}/messages", json={"question": q["question"]}, headers=h)
            dt = round(time.time() - t0, 2)
            j = r.json() if r.status_code == 200 else {}
            task = j.get("task")
            rec = {"id": q["id"], "category": q["category"], "split": q["split"], "question": q["question"], "variant": "REST_W3_p3", "run": run,
                   "answer": j.get("answer", ""), "trace": [{"tool": s["tool"], "args": s["args"], "ok": s["ok"], "error": s["error"]} for s in j.get("steps", [])],
                   "tasks_after": [{"status": "szkic" if task["status"] in ("szkic", "oczekuje") else task["status"]}] if task else [],
                   "tokens_in": j.get("tokens", 0), "tokens_out": 0, "steps": len(j.get("steps", [])), "latency_s": dt, "model": "gpt-4.1-mini",
                   "error": None if r.status_code == 200 else f"HTTP {r.status_code}"}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            print(q["id"], r.status_code, dt, "s", j.get("tokens"), flush=True)
