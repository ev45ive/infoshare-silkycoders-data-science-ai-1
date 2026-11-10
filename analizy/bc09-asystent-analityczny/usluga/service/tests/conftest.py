"""Wspólne elementy testów usługi: model testowy (fake_chat), klient API z prawdziwą bazą stanu, fabryka użytkowników i pomocnicy logowania i zadawania pytań."""
import dataclasses
import json
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from svc import auth                      # noqa: E402
from svc.api import create_app            # noqa: E402
from svc.config import get_settings       # noqa: E402


# Atrapy odpowiedzi modelu w formacie SDK (message.tool_calls[i].function.name/arguments): wystarczają, by pętla narzędzi rdzenia działała bez sieci.
class Fn:
    def __init__(self, name, args): self.name, self.arguments = name, args


class TC:
    def __init__(self, i, name, args): self.id, self.function = i, Fn(name, json.dumps(args))


class Msg:
    def __init__(self, content=None, tool_calls=None): self.content, self.tool_calls = content, tool_calls


def fake_chat(messages, tools=None, label=""):
    """Deterministyczny model testowy (bez kosztu). Prefiks pytania wybiera scenariusz:
    TASK: szkic zadania; TASK2: dwa szkice w jednym pytaniu; APPROVE: próba wywołania nieistniejącego approve_task; SQLW: zapis SQL (DROP).
    Inne pytanie: zwykła odpowiedź. Po wyniku narzędzia (ostatnia wiadomość 'tool') model kończy odpowiedzią tekstową. Zwraca (wiadomość, tokeny_we, tokeny_wy)."""
    q, last = messages[1]["content"], messages[-1]["role"]
    if tools and last != "tool":
        if q.startswith("TASK:"):
            return Msg(tool_calls=[TC("a", "propose_task", {"title": "Dosyłka kurtek", "description": q[5:], "owner": "Zakupy"})]), 100, 20
        if q.startswith("TASK2:"):
            return Msg(tool_calls=[TC("a", "propose_task", {"title": "Pierwsze", "description": "d", "owner": "Zakupy"}),
                                   TC("b", "propose_task", {"title": "Drugie", "description": "d", "owner": "Zakupy"})]), 100, 20
        if q.startswith("APPROVE:"):
            return Msg(tool_calls=[TC("a", "approve_task", {"task_id": 1, "approver": "model"})]), 100, 20
        if q.startswith("SQLW:"):
            return Msg(tool_calls=[TC("a", "run_sql", {"sql": "drop table dbo.FactSales"})]), 100, 20
    if last == "tool":
        return Msg(f"Po narzędziu: {messages[-1]['content'][:60]}"), 50, 10
    return Msg(f"Odpowiedź testowa na: {q[:40]}"), 50, 10


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def client(settings):
    with TestClient(create_app(settings, base_chat=fake_chat)) as c:
        yield c


@pytest.fixture()
def store(client):
    return client.app.state.store


def new_user(store, role, active=True):
    name, pw = f"t_{uuid.uuid4().hex[:10]}", uuid.uuid4().hex
    u = store.create_user(name, auth.hash_password(pw), role)
    if not active:
        store.set_active(name, False)
    return {"name": name, "pw": pw, "id": u["user_id"], "role": role}


def login(client, u, pw=None):
    r = client.post("/auth/token", data={"username": u["name"], "password": pw or u["pw"]})
    return {"Authorization": f"Bearer {r.json()['access_token']}"} if r.status_code == 200 else None


def ask(client, headers, question, thread_id=None):
    if thread_id is None:
        thread_id = client.post("/threads", json={}, headers=headers).json()["thread_id"]
    r = client.post(f"/threads/{thread_id}/messages", json={"question": question}, headers=headers)
    return thread_id, r


@pytest.fixture()
def users(client, store):
    return {"a": new_user(store, "requester"), "b": new_user(store, "requester"), "c": new_user(store, "approver"), "d": new_user(store, "approver")}
