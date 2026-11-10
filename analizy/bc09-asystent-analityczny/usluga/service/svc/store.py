"""Warstwa dostępu do stanu usługi (PostgreSQL, rola bc09_svc: tylko DML). Każda funkcja to jedno zapytanie; reguły dostępu sprawdza API, a niezmienniki (cztery oczy) także baza."""
import hashlib
import json
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


def make_pool(settings, max_size=10):
    # autocommit: każda funkcja Store to jedno zapytanie, więc nie ma otwartych transakcji. dict_row: wiersze jako słowniki.
    # search_path=svc: nazwy tabel bez schematu (users, tasks, ...) wskazują na schemat usługi.
    pool = ConnectionPool(settings.conninfo, min_size=1, max_size=max_size, open=False,
                          kwargs={"autocommit": True, "row_factory": dict_row, "options": "-c search_path=svc"})
    pool.open(wait=True, timeout=15)
    return pool


class OneDraftPerQuestion(TypeError):   # TypeError, bo rdzeń zamienia go na błąd narzędzia dla modelu
    pass


class Store:
    def __init__(self, pool, approval_ttl_hours=72):
        self.pool, self.ttl = pool, approval_ttl_hours

    def _one(self, sql, args=()):
        with self.pool.connection() as c:
            return c.execute(sql, args).fetchone()

    def _all(self, sql, args=()):
        with self.pool.connection() as c:
            return c.execute(sql, args).fetchall()

    # --- użytkownicy ---------------------------------------------------------------------
    def create_user(self, username, password_hash, role):
        return self._one("INSERT INTO users(username, password_hash, role) VALUES (%s,%s,%s) "
                         "ON CONFLICT (username) DO UPDATE SET password_hash=EXCLUDED.password_hash, role=EXCLUDED.role, active=true RETURNING *",
                         (username, password_hash, role))

    def user_by_name(self, username):
        return self._one("SELECT * FROM users WHERE username=%s", (username,))

    def user_by_id(self, user_id):
        return self._one("SELECT * FROM users WHERE user_id=%s", (user_id,))

    def set_active(self, username, active):
        return self._one("UPDATE users SET active=%s WHERE username=%s RETURNING username, active", (active, username))

    # --- wątki i wiadomości --------------------------------------------------------------
    def create_thread(self, owner_id, title=None):
        return self._one("INSERT INTO threads(owner_id, title) VALUES (%s,%s) RETURNING *", (owner_id, title))

    def thread_owned(self, thread_id, owner_id):
        """Własność sprawdzana w zapytaniu: cudzy i nieistniejący wątek są nieodróżnialne (oba dają None)."""
        return self._one("SELECT * FROM threads WHERE thread_id=%s AND owner_id=%s", (thread_id, owner_id))

    def threads_of(self, owner_id):
        return self._all("SELECT thread_id, title, created_at FROM threads WHERE owner_id=%s ORDER BY created_at DESC LIMIT 100", (owner_id,))

    def add_message(self, thread_id, role, content, trace=None, tokens=None):
        return self._one("INSERT INTO messages(thread_id, role, content, trace, tokens) VALUES (%s,%s,%s,%s,%s) RETURNING message_id",
                         (thread_id, role, content, json.dumps(trace, ensure_ascii=False, default=str) if trace is not None else None, tokens))["message_id"]

    def messages(self, thread_id):
        return self._all("SELECT message_id, role, content, trace, tokens, created_at FROM messages WHERE thread_id=%s ORDER BY message_id", (thread_id,))

    # --- zadania -------------------------------------------------------------------------
    def propose_task(self, thread_id, requester_id, message_id, title, description, owner):
        """Szkic zadania: klucz idempotencji = wątek + wiadomość (jeden szkic na pytanie). Ponowne wykonanie węzła zwraca ten sam wiersz."""
        key = hashlib.sha256(f"{thread_id}|{message_id}".encode()).hexdigest()
        row = self._one("INSERT INTO tasks(thread_id, requester_id, idem_key, title, description, owner) VALUES (%s,%s,%s,%s,%s,%s) "
                        "ON CONFLICT (idem_key) DO NOTHING RETURNING *", (thread_id, requester_id, key, str(title)[:200], str(description)[:2000], str(owner)[:100]))
        if row:
            return row
        row = self._one("SELECT * FROM tasks WHERE idem_key=%s", (key,))
        if (row["title"], row["description"], row["owner"]) != (str(title)[:200], str(description)[:2000], str(owner)[:100]):
            raise OneDraftPerQuestion("Dozwolony jest jeden szkic zadania na pytanie.")
        return row

    def mark_pending(self, task_id):
        # Szkic -> oczekuje i ustawienie terminu ważności (expires_at). Warunek status='szkic' czyni krok idempotentnym: drugie wykonanie nic nie zmienia.
        return self._one("UPDATE tasks SET status='oczekuje', expires_at=now() + make_interval(hours => %s) WHERE task_id=%s AND status='szkic' RETURNING *",
                         (self.ttl, task_id))

    def task(self, task_id):
        return self._one("SELECT * FROM tasks WHERE task_id=%s", (task_id,))

    def tasks_of(self, requester_id):
        return self._all("SELECT * FROM tasks WHERE requester_id=%s ORDER BY task_id DESC LIMIT 100", (requester_id,))

    def pending_for(self, approver_id):
        return self._all("SELECT t.*, u.username AS requester FROM tasks t JOIN users u ON u.user_id=t.requester_id "
                         "WHERE t.status='oczekuje' AND t.requester_id<>%s AND t.expires_at>now() ORDER BY t.task_id", (approver_id,))

    def decide(self, task_id, approver_id, action, edits=None):
        """Atomowa decyzja: tylko z 'oczekuje', nie wygasłe, approver != requester (także CHECK w bazie). Zwraca wiersz albo None."""
        edits = edits or {}
        status = {"approve": "zatwierdzone", "reject": "odrzucone"}[action]
        # Jedno UPDATE robi wszystko naraz: WHERE jest jednocześnie bramką (status 'oczekuje', nie wygasłe, zatwierdzający != autor), więc dwie równoległe
        # decyzje nie przejdą obie (druga zwróci None). COALESCE(nowa, stara) stosuje tylko pola faktycznie edytowane; `edited` przyjmuje true,
        # gdy którekolwiek pole podano (raz ustawione zostaje).
        return self._one(
            "UPDATE tasks SET status=%s, approver_id=%s, decided_at=now(), title=COALESCE(%s,title), description=COALESCE(%s,description), owner=COALESCE(%s,owner), "
            "edited = edited OR (%s::text IS NOT NULL OR %s::text IS NOT NULL OR %s::text IS NOT NULL) "
            "WHERE task_id=%s AND status='oczekuje' AND requester_id<>%s AND expires_at>now() RETURNING *",
            (status, approver_id, edits.get("title"), edits.get("description"), edits.get("owner"), edits.get("title"), edits.get("description"), edits.get("owner"), task_id, approver_id))

    def expire_due(self):
        # Wywoływane z maintenance: oznacza przeterminowane zadania jako wygasłe i zwraca je (do wznowienia wstrzymanych wątków).
        return self._all("UPDATE tasks SET status='wygasle' WHERE status='oczekuje' AND expires_at<=now() RETURNING task_id, thread_id")

    # --- audyt i zużycie -----------------------------------------------------------------
    def audit(self, actor_id, action, thread_id=None, task_id=None, detail=None):
        self._one("INSERT INTO audit_log(actor_id, action, thread_id, task_id, detail) VALUES (%s,%s,%s,%s,%s) RETURNING audit_id",
                  (actor_id, action, thread_id, task_id, json.dumps(detail, ensure_ascii=False, default=str) if detail is not None else None))

    def tokens_today(self, user_id):
        r = self._one("SELECT tokens FROM usage_daily WHERE user_id=%s AND day=current_date", (user_id,))
        return int(r["tokens"]) if r else 0

    def add_usage(self, user_id, tokens):
        # Upsert: jedna linia na (użytkownik, dzień), tokeny dodawane atomowo w bazie (bez odczytu i zapisu po stronie aplikacji).
        self._one("INSERT INTO usage_daily(user_id, day, tokens) VALUES (%s, current_date, %s) ON CONFLICT (user_id, day) DO UPDATE SET tokens = usage_daily.tokens + EXCLUDED.tokens RETURNING tokens",
                  (user_id, int(tokens)))

    def ping(self):
        return self._one("SELECT 1 AS ok")["ok"] == 1


class PgTaskStore:
    """Adapter z interfejsem TaskStore rdzenia (propose/list), zapisujący szkic w bazie stanu. Zatwierdzenia tu NIE ma: robi je kod usługi po decyzji człowieka."""

    def __init__(self, store, thread_id, requester_id, message_id):
        self.store, self.thread_id, self.requester_id, self.message_id = store, thread_id, requester_id, message_id
        self.last = None

    def propose(self, title, description, owner):
        r = self.store.propose_task(self.thread_id, self.requester_id, self.message_id, title, description, owner)
        self.last = r
        return {"id": r["task_id"], "title": r["title"], "description": r["description"], "owner": r["owner"], "status": "szkic", "created_by": "asystent"}

    def list(self):
        return [self.last] if self.last else []
