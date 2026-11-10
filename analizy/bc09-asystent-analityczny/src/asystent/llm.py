"""Cienka warstwa nad API modelu językowego: twardy limit tokenów (rejestr zużycia w pliku), ponawianie, brak sekretów w kodzie.

Klucz API tylko ze zmiennej środowiskowej OPENAI_API_KEY (SDK czyta ją sam; OPENAI_BASE_URL także).
Rejestr zużycia sumuje tokeny z WSZYSTKICH sesji i przebiegów; przed każdym wywołaniem sprawdzamy limit.
"""
import json
import os
import time
from datetime import date

from . import config


class BudgetExceeded(Exception):
    pass


# Blokada plikowa (O_CREAT|O_EXCL): zapisy rejestru z kilku procesów naraz nie gubią tokenów. Martwa blokada po przerwanym procesie
# jest usuwana po `timeout` sekundach.
def _lock_acquire(path, timeout=30):
    t0 = time.time()
    while True:
        try:
            return os.open(str(path) + ".lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.time() - t0 > timeout:      # martwa blokada po przerwanym procesie
                try:
                    os.unlink(str(path) + ".lock")
                except OSError:
                    pass
            time.sleep(0.05)


def _lock_release(fd, path):
    os.close(fd)
    try:
        os.unlink(str(path) + ".lock")
    except OSError:
        pass


def ledger():
    p = config.LEDGER_PATH
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"limit_tokens": config.TOTAL_TOKEN_LIMIT, "total_tokens": 0, "calls": 0, "by_label": {}, "first_use": str(date.today())}


def record(label, model, tin, tout):
    config.CACHE.mkdir(exist_ok=True)
    fd = _lock_acquire(config.LEDGER_PATH)
    try:
        led = ledger()
        led["total_tokens"] += tin + tout
        led["calls"] += 1
        b = led["by_label"].setdefault(label, {"calls": 0, "in": 0, "out": 0, "model": model})
        b["calls"] += 1
        b["in"] += tin
        b["out"] += tout
        config.LEDGER_PATH.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    finally:
        _lock_release(fd, config.LEDGER_PATH)


# Twardy limit łączny: zanim wykonamy wywołanie, sprawdzamy, czy zużycie + zapas na jedno wywołanie (`reserve`) nie przekroczy limitu.
def check_budget(reserve=25_000):
    led = ledger()
    if led["total_tokens"] + reserve > config.TOTAL_TOKEN_LIMIT:
        raise BudgetExceeded(f"Limit tokenów: zużyto {led['total_tokens']} z {config.TOTAL_TOKEN_LIMIT}.")
    return led["total_tokens"]


_client = None


def client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(max_retries=3, timeout=90)
    return _client


def chat(messages, tools=None, label="", model=None, max_tokens=1200):
    """Jedno wywołanie. Zwraca (message, tokens_in, tokens_out). Temperatura 0 i stałe ziarno (nie gwarantują identyczności)."""
    check_budget()
    # Temperatura 0 i stałe ziarno zmniejszają rozrzut odpowiedzi, ale go nie usuwają (dwa przebiegi tych samych pytań mogą się różnić).
    kw = dict(model=model or config.LLM_MODEL, messages=messages, temperature=0, seed=7, max_tokens=max_tokens)
    if tools:
        kw["tools"] = tools
    r = client().chat.completions.create(**kw)
    u = r.usage
    record(label, kw["model"], u.prompt_tokens, u.completion_tokens)
    return r.choices[0].message, u.prompt_tokens, u.completion_tokens


def embed(texts, label="embed", model=None):
    check_budget()
    m = model or config.EMBED_MODEL
    r = client().embeddings.create(model=m, input=list(texts))
    record(label, m, r.usage.prompt_tokens, 0)
    return [d.embedding for d in r.data]
