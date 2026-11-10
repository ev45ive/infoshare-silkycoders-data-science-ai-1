"""Pomocnik testu trwałości: faza 1 tworzy wstrzymane zatwierdzenie i kończy proces NAGLE (os._exit), faza 2 w nowym procesie je kończy.
python restart_helper.py phase1  -> JSON na stdout;  python restart_helper.py phase2 '<json z fazy 1>' -> JSON na stdout"""
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fastapi.testclient import TestClient  # noqa: E402

from conftest import fake_chat, login, new_user, ask  # noqa: E402
from svc.api import create_app             # noqa: E402
from svc.config import get_settings        # noqa: E402

s = get_settings()
if sys.argv[1] == "phase1":
    c = TestClient(create_app(s, base_chat=fake_chat))
    c.__enter__()
    store = c.app.state.store
    a, appr = new_user(store, "requester"), new_user(store, "approver")
    tid, r = ask(c, login(c, a), "TASK: restart test " + uuid.uuid4().hex[:6])
    print(json.dumps({"thread_id": tid, "task_id": r.json()["task"]["task_id"], "a": {k: str(v) for k, v in a.items()}, "c": {k: str(v) for k, v in appr.items()}}), flush=True)
    os._exit(0)                                       # brak graceful shutdown: symulacja awarii procesu
else:
    p = json.loads(sys.argv[2])
    with TestClient(create_app(s, base_chat=fake_chat)) as c:
        hc = login(c, p["c"])
        d1 = c.post(f"/approvals/{p['task_id']}/decision", json={"action": "approve"}, headers=hc)
        d2 = c.post(f"/approvals/{p['task_id']}/decision", json={"action": "approve"}, headers=hc)
        n = c.app.state.store._one("SELECT count(*) AS n FROM tasks WHERE thread_id=%s", (p["thread_id"],))["n"]
        det = c.get(f"/threads/{p['thread_id']}", headers=login(c, p["a"])).json()
        print(json.dumps({"first": d1.status_code, "status": d1.json().get("status"), "second": d2.status_code, "tasks_in_thread": n,
                          "pending_after": det["pending_task"], "last_message": det["messages"][-1]["content"]}))
