"""Kontrakt REST (Pydantic): ścisłe typy, limity długości, brak pól dodatkowych."""
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    # Wspólna baza: pola spoza kontraktu są odrzucane (422), więc klient nie może np. dosyłać pola status czy approver_id.
    model_config = ConfigDict(extra="forbid")


class TokenOut(Strict):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class MeOut(Strict):
    username: str
    role: Literal["requester", "approver"]


class ThreadOut(Strict):
    thread_id: UUID
    title: Optional[str] = None
    created_at: datetime


class ThreadCreate(Strict):
    title: Optional[str] = Field(None, max_length=120)


class MessageIn(Strict):
    question: str = Field(min_length=1, max_length=2000, description="Pytanie do asystenta (limit długości egzekwowany też w usłudze wg konfiguracji)")


class StepOut(Strict):
    tool: str
    ok: bool
    error: Optional[str] = None
    args: dict = {}


class TaskOut(Strict):
    task_id: int
    thread_id: UUID
    title: str
    description: str
    owner: str
    status: Literal["szkic", "oczekuje", "zatwierdzone", "odrzucone", "wygasle"]
    requester: Optional[str] = None
    expires_at: Optional[datetime] = None
    edited: bool = False


class AnswerOut(Strict):
    answer: str
    status: Literal["answered", "awaiting_approval"]
    task: Optional[TaskOut] = None
    steps: list[StepOut] = []
    tokens: int = 0


class MessageOut(Strict):
    message_id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ThreadDetail(Strict):
    thread: ThreadOut
    messages: list[MessageOut]
    pending_task: Optional[TaskOut] = None


class Decision(Strict):
    action: Literal["approve", "reject"]
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    owner: Optional[str] = Field(None, min_length=1, max_length=100)


class ProcedureHit(Strict):
    doc_id: str
    title: str
    version: str
    valid_from: str
    owner: str
    status: str
    snippet: str
