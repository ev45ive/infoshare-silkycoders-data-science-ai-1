"""REST API usługi BC-09. Kontrola dostępu jest tutaj i w bazie (nie w interfejsie i nie w prompcie). Endpointy `def` (nie `async def`): graf jest synchroniczny,
więc FastAPI uruchamia je w puli wątków i nie blokuje pętli zdarzeń."""
import logging
import time
import uuid
from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core import llm as core_llm
from . import auth, schemas
from .config import get_settings
from .gateway import QuotaExceeded, RequestTimeout
from .graph import Engine
from .store import Store, make_pool

log = logging.getLogger("svc")
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/token", description="Zaloguj się (POST /auth/token), a następnie użyj tokenu Bearer.")


def create_app(settings=None, base_chat=None, engine=None):
    # Fabryka aplikacji. Parametry służą testom: wstrzyknięcie ustawień, fałszywego modelu (base_chat) lub gotowego silnika; produkcyjnie (svc.main) wszystko domyślne.
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app):
        # Start: pula połączeń do PostgreSQL, magazyn (Store) i silnik grafu (Engine) w app.state; zamknięcie puli przy zatrzymaniu usługi.
        pool = make_pool(settings)
        store = Store(pool, settings.approval_ttl_hours)
        app.state.store, app.state.engine = store, engine or Engine(store, pool, settings, base_chat=base_chat)
        yield
        pool.close()

    app = FastAPI(title="Asystent analityczny Nordvik (BC-09)", version="1.0", lifespan=lifespan,
                  description="Usługa pilotażowa. Zapisy tylko po zatwierdzeniu przez uprawnionego człowieka innego niż wnioskodawca. Środowisko szkoleniowe (bez TLS).")
    app.state.settings = settings

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        rid = uuid.uuid4().hex[:12]
        request.state.rid = rid
        t0 = time.time()
        resp = await call_next(request)
        resp.headers["X-Request-ID"] = rid
        log.info("rid=%s %s %s -> %s %.0fms", rid, request.method, request.url.path, resp.status_code, (time.time() - t0) * 1000)   # bez treści i bez nagłówków
        return resp

    @app.exception_handler(Exception)
    async def generic(request: Request, exc: Exception):
        log.exception("rid=%s błąd wewnętrzny", getattr(request.state, "rid", "-"))             # szczegóły tylko w logach serwera
        return JSONResponse({"detail": "Błąd wewnętrzny.", "request_id": getattr(request.state, "rid", None)}, status_code=500)

    # --- zależności ------------------------------------------------------------------------
    # Kontrola dostępu składa się z trzech zależności FastAPI: current_user (kto pyta), approver (czy ma rolę zatwierdzającego), own_thread (czy wątek jego).
    def current_user(request: Request, token: str = Depends(oauth2)):
        try:
            claims = auth.decode_token(settings.jwt_secret, token)
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Nieprawidłowy lub wygasły token.", headers={"WWW-Authenticate": "Bearer"})
        user = request.app.state.store.user_by_id(claims["sub"])
        if not user or not user["active"]:
            raise HTTPException(401, "Konto nieaktywne.", headers={"WWW-Authenticate": "Bearer"})
        return user                                       # rola z bazy, nie z tokenu: zmiana roli działa od razu

    def approver(user=Depends(current_user)):
        if user["role"] != "approver":
            raise HTTPException(403, "Wymagana rola zatwierdzającego.")
        return user

    def own_thread(thread_id: uuid.UUID, request: Request, user=Depends(current_user)):
        t = request.app.state.store.thread_owned(str(thread_id), user["user_id"])
        if not t:
            raise HTTPException(404, "Nie znaleziono wątku.")   # cudzy i nieistniejący: ta sama odpowiedź
        return t

    def thread_out(t):
        return schemas.ThreadOut(thread_id=t["thread_id"], title=t["title"], created_at=t["created_at"])

    def msg_out(m):
        return schemas.MessageOut(message_id=m["message_id"], role=m["role"], content=m["content"], created_at=m["created_at"])

    def task_out(t, requester=None):
        return schemas.TaskOut(task_id=t["task_id"], thread_id=t["thread_id"], title=t["title"], description=t["description"], owner=t["owner"],
                               status=t["status"], requester=requester, expires_at=t["expires_at"], edited=t["edited"])

    # --- punkty końcowe ----------------------------------------------------------------------
    @app.get("/health", tags=["system"])
    def health(request: Request):
        try:
            return {"status": "ok" if request.app.state.store.ping() else "degraded"}
        except Exception:
            return JSONResponse({"status": "degraded"}, status_code=503)

    @app.post("/auth/token", response_model=schemas.TokenOut, tags=["auth"])
    def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
        # Ta sama odpowiedź 401 i podobny czas dla złego loginu, złego hasła i konta nieaktywnego (brak wyliczania loginów); każda próba trafia do audytu.
        store = request.app.state.store
        user = store.user_by_name(form.username[:64])
        if not auth.verify_or_dummy(form.password, user["password_hash"] if user else None) or not user["active"]:
            store.audit(user["user_id"] if user else None, "login_failed", detail={"username": form.username[:64]})
            raise HTTPException(401, "Błędny login lub hasło.")
        store.audit(user["user_id"], "login")
        return schemas.TokenOut(access_token=auth.issue_token(settings.jwt_secret, user["user_id"], user["role"], settings.token_ttl_min), expires_in=settings.token_ttl_min * 60)

    @app.get("/me", response_model=schemas.MeOut, tags=["auth"])
    def me(user=Depends(current_user)):
        return schemas.MeOut(username=user["username"], role=user["role"])

    @app.post("/threads", response_model=schemas.ThreadOut, status_code=201, tags=["rozmowy"])
    def create_thread(body: schemas.ThreadCreate, request: Request, user=Depends(current_user)):
        t = request.app.state.store.create_thread(user["user_id"], body.title)
        return thread_out(t)

    @app.get("/threads", response_model=list[schemas.ThreadOut], tags=["rozmowy"])
    def list_threads(request: Request, user=Depends(current_user)):
        return [thread_out(t) for t in request.app.state.store.threads_of(user["user_id"])]

    @app.get("/threads/{thread_id}", response_model=schemas.ThreadDetail, tags=["rozmowy"])
    def get_thread(request: Request, t=Depends(own_thread)):
        st, eng = request.app.state.store, request.app.state.engine
        tid = eng.pending(t["thread_id"])
        return schemas.ThreadDetail(thread=thread_out(t), messages=[msg_out(m) for m in st.messages(t["thread_id"])],
                                    pending_task=task_out(st.task(tid)) if tid else None)

    @app.post("/threads/{thread_id}/messages", response_model=schemas.AnswerOut, tags=["rozmowy"])
    def ask(body: schemas.MessageIn, request: Request, t=Depends(own_thread), user=Depends(current_user)):
        # Kolejność: wątek należy do użytkownika (404) -> długość pytania (413) -> wątek nie czeka na decyzję (409) -> zapis pytania -> wywołanie grafu.
        # Błędy limitów z bramki mapujemy na kody: 429 limit dzienny użytkownika, 504 czas żądania, 503 limit łączny modelu dla całego pilotażu.
        st, eng = request.app.state.store, request.app.state.engine
        if len(body.question) > settings.max_question_chars:
            raise HTTPException(413, f"Pytanie przekracza {settings.max_question_chars} znaków.")
        if eng.pending(t["thread_id"]):
            raise HTTPException(409, "Wątek czeka na zatwierdzenie zadania; zadaj pytanie w nowym wątku.")
        mid = st.add_message(t["thread_id"], "user", body.question)
        try:
            r = eng.ask(t["thread_id"], user["user_id"], mid, body.question)
        except QuotaExceeded:
            raise HTTPException(429, "Dzienny limit zużycia wyczerpany.")
        except RequestTimeout:
            raise HTTPException(504, "Przekroczono limit czasu żądania.")
        except core_llm.BudgetExceeded:
            raise HTTPException(503, "Limit zużycia modelu dla pilotażu wyczerpany.")
        st.audit(user["user_id"], "ask", t["thread_id"], r["task_id"], {"tools": [x["tool"] for x in r["trace"]], "tokens": r["tokens"]})
        task = task_out(st.task(r["task_id"])) if r["task_id"] else None
        return schemas.AnswerOut(answer=r["answer"], status="awaiting_approval" if r["awaiting"] else "answered", task=task,
                                 steps=[schemas.StepOut(**x) for x in r["trace"]], tokens=r["tokens"])

    @app.get("/tasks", response_model=list[schemas.TaskOut], tags=["zadania"])
    def my_tasks(request: Request, user=Depends(current_user)):
        return [task_out(t) for t in request.app.state.store.tasks_of(user["user_id"])]

    @app.get("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["zadania"])
    def get_task(task_id: int, request: Request, user=Depends(current_user)):
        t = request.app.state.store.task(task_id)
        # Widoczność: autor widzi swoje zadania; zatwierdzający widzi oczekujące oraz te, które sam rozpatrzył. Reszta dostaje 404 (jak brak zadania).
        mine = t and str(t["requester_id"]) == str(user["user_id"])
        visible_to_approver = t and user["role"] == "approver" and (t["status"] == "oczekuje" or str(t["approver_id"]) == str(user["user_id"]))
        if not (mine or visible_to_approver):
            raise HTTPException(404, "Nie znaleziono zadania.")
        return task_out(t)

    @app.get("/approvals", response_model=list[schemas.TaskOut], tags=["zatwierdzanie"])
    def approvals(request: Request, user=Depends(approver)):
        return [task_out(t, requester=t["requester"]) for t in request.app.state.store.pending_for(user["user_id"])]

    @app.post("/approvals/{task_id}/decision", response_model=schemas.TaskOut, tags=["zatwierdzanie"])
    def decide(task_id: int, body: schemas.Decision, request: Request, user=Depends(approver)):
        # Cztery oczy egzekwowane na trzech poziomach: (1) rola 'approver' z bazy, (2) tutaj: wnioskodawca != zatwierdzający (403 + wpis w audycie),
        # (3) w bazie: warunek w store.decide i CHECK w tabeli. Dopiero po tych kontrolach graf jest wznawiany z decyzją człowieka.
        st, eng = request.app.state.store, request.app.state.engine
        t = st.task(task_id)
        if not t or t["status"] != "oczekuje":
            raise HTTPException(404, "Nie znaleziono zadania oczekującego na zatwierdzenie.")
        if str(t["requester_id"]) == str(user["user_id"]):
            st.audit(user["user_id"], "self_approval_denied", t["thread_id"], task_id)
            raise HTTPException(403, "Wnioskodawca nie może zatwierdzić własnego zadania.")
        if t["expires_at"] and t["expires_at"].timestamp() < time.time():
            raise HTTPException(410, "Termin zatwierdzenia minął.")
        edits = {k: v for k, v in (("title", body.title), ("description", body.description), ("owner", body.owner)) if v is not None}
        eng.resume(t["thread_id"], {"action": body.action, "approver_id": str(user["user_id"]), "edits": edits})
        done = st.task(task_id)
        if done["status"] == "oczekuje":                   # np. wyścig z drugą decyzją: stan niezmieniony
            raise HTTPException(409, "Zadanie zostało już rozpatrzone.")
        return task_out(done)

    @app.get("/procedures/search", response_model=list[schemas.ProcedureHit], tags=["procedury"])
    def search(q: str, request: Request, user=Depends(current_user)):
        hits = request.app.state.engine.shared.index.search_docs(q[:200], k=3)
        return [schemas.ProcedureHit(doc_id=h["doc_id"], title=h["title"], version=h["version"], valid_from=h["valid_from"], owner=h["owner"], status=h["status"],
                                     snippet=h["text"][:600]) for h in hits]

    return app
