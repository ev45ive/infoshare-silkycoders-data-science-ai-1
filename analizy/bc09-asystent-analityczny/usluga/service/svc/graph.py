"""Graf LangGraph: pytanie -> (szkic zadania) -> wstrzymanie na zatwierdzenie -> decyzja -> odpowiedź.
Zasady z dokumentacji LangGraph (sprawdzone w zainstalowanej wersji): `interrupt` zapisuje stan w checkpointerze i czeka bezterminowo; wznowienie `Command(resume=...)`
z tym samym thread_id; węzeł po wznowieniu startuje OD POCZĄTKU, więc węzeł wstrzymania nie ma żadnych skutków ubocznych przed `interrupt`,
a skutki uboczne (szkic, decyzja) są w osobnych, idempotentnych węzłach. Model nie ma narzędzia zatwierdzającego: decyzję wykonuje apply_decision z danymi od API."""
from typing import Optional, TypedDict

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from core import agent as core_agent, db as core_db, tools as core_tools
from .gateway import make_chat
from .store import PgTaskStore


class State(TypedDict, total=False):
    thread_id: str
    user_id: str
    message_id: int
    question: str
    answer: str
    trace: list
    tokens: int
    task_id: Optional[int]
    decision: Optional[dict]
    final: str


class Engine:
    def __init__(self, store, pool, settings, base_chat=None, shared=None):
        self.store, self.settings, self.base_chat = store, settings, base_chat
        self.shared = shared or core_tools.Toolbox()     # indeks dokumentów i prognoza: niezmienne, współdzielone
        self.saver = PostgresSaver(pool)
        self.graph = self._build().compile(checkpointer=self.saver)

    # --- węzły ----------------------------------------------------------------------------
    def _ask(self, s: State):
        # Wywołanie asystenta (wariant W3 rdzenia). Każde żądanie dostaje własne połączenie read-only z DuckDB i własny magazyn szkiców (PgTaskStore),
        # a indeks dokumentów i prognoza są współdzielone (niezmienne). `chat` to bramka z limitem dziennym i czasem żądania.
        con = core_db.open_readonly()                    # osobne połączenie tylko do odczytu na żądanie
        try:
            tasks = PgTaskStore(self.store, s["thread_id"], s["user_id"], s["message_id"])
            tb = core_tools.Toolbox(con=con, tasks=tasks, shared=self.shared)
            chat = make_chat(self.store, s["user_id"], self.settings.daily_token_limit, self.settings.request_timeout_s, self.base_chat)
            res = core_agent.W3(tb, label="svc", chat=chat).answer(s["question"])
        finally:
            con.close()
        # Ślad wywołań trafia do stanu grafu i do bazy: argumenty obcinamy do 300 znaków, żeby nie zapisywać długich treści.
        trace = [{"tool": t["tool"], "args": {k: str(v)[:300] for k, v in (t.get("args") or {}).items()}, "ok": t["ok"], "error": t.get("error")} for t in tb.trace]
        return {"answer": res["answer"], "trace": trace, "tokens": res["tokens_in"] + res["tokens_out"], "task_id": tasks.last["task_id"] if tasks.last else None}

    def _route_after_ask(self, s: State):
        # Rozgałęzienie: pytanie bez szkicu kończy się od razu; ze szkicem idzie do wstrzymania na decyzję człowieka.
        return "mark_pending" if s.get("task_id") else "finish"

    def _mark_pending(self, s: State):
        self.store.mark_pending(s["task_id"])            # idempotentne: tylko szkic -> oczekuje
        self.store.audit(s["user_id"], "task_pending", s["thread_id"], s["task_id"])
        return {}

    def _await_approval(self, s: State):
        # JEDYNY węzeł z interrupt: graf zapisuje stan w PostgreSQL i staje. Po wznowieniu (Command(resume=...)) węzeł startuje od początku,
        # a interrupt zwraca już decyzję przekazaną przez API. Dlatego przed interrupt nie ma żadnych skutków ubocznych.
        t = self.store.task(s["task_id"])
        decision = interrupt({"task_id": t["task_id"], "title": t["title"], "description": t["description"], "owner": t["owner"], "status": t["status"]})
        return {"decision": decision}

    def _apply_decision(self, s: State):
        # Decyzję zapisuje kod usługi z danymi z API (kto zatwierdza, jakie poprawki), nie model. Reguły (nie wygasłe, nie autor) wymusza store.decide.
        d = s["decision"] or {}
        if d.get("action") in ("approve", "reject"):
            row = self.store.decide(s["task_id"], d["approver_id"], d["action"], d.get("edits"))
            self.store.audit(d["approver_id"], f"task_{d['action']}", s["thread_id"], s["task_id"], {"edits": d.get("edits"), "applied": bool(row)})
        else:                                            # wygaśnięcie (maintenance): zadanie jest już oznaczone jako wygasle
            self.store.audit(None, "task_expired", s["thread_id"], s["task_id"])
        return {}

    def _finish(self, s: State):
        text = s["answer"]
        if s.get("task_id"):
            t = self.store.task(s["task_id"])
            who = self.store.user_by_id(t["approver_id"])["username"] if t["approver_id"] else None
            text += f"\n\n[Zadanie #{t['task_id']}: {t['status']}" + (f" przez {who}" if who else "") + "]"
        self.store.add_message(s["thread_id"], "assistant", text, trace=s.get("trace"), tokens=s.get("tokens"))
        return {"final": text}

    def _build(self):
        # Topologia: START -> ask -> [mark_pending -> await_approval -> apply_decision ->] finish -> END; nawias tylko, gdy powstał szkic zadania.
        g = StateGraph(State)
        for name, fn in (("ask", self._ask), ("mark_pending", self._mark_pending), ("await_approval", self._await_approval),
                         ("apply_decision", self._apply_decision), ("finish", self._finish)):
            g.add_node(name, fn)
        g.add_edge(START, "ask")
        g.add_conditional_edges("ask", self._route_after_ask, {"mark_pending": "mark_pending", "finish": "finish"})
        g.add_edge("mark_pending", "await_approval")
        g.add_edge("await_approval", "apply_decision")
        g.add_edge("apply_decision", "finish")
        g.add_edge("finish", END)
        return g

    # --- API silnika -----------------------------------------------------------------------
    @staticmethod
    def cfg(thread_id):
        return {"configurable": {"thread_id": str(thread_id)}}

    def pending(self, thread_id):
        """Zadanie czekające w tym wątku (None, jeśli wątek nie jest wstrzymany)."""
        st = self.graph.get_state(self.cfg(thread_id))
        return st.values.get("task_id") if st and st.next else None

    def ask(self, thread_id, user_id, message_id, question):
        out = self.graph.invoke({"thread_id": str(thread_id), "user_id": str(user_id), "message_id": message_id, "question": question,
                                 "task_id": None, "decision": None}, self.cfg(thread_id))
        return {"answer": out.get("final") or out.get("answer"), "task_id": out.get("task_id"), "awaiting": bool(self.pending(thread_id)),
                "trace": out.get("trace", []), "tokens": out.get("tokens", 0)}

    def resume(self, thread_id, decision):
        out = self.graph.invoke(Command(resume=decision), self.cfg(thread_id))
        return {"final": out.get("final")}
