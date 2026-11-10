"""Runner: uruchamia wariant na pytaniach i zapisuje SUROWE wyniki (odpowiedź, ślad narzędzi, tokeny, czas) do JSONL.
Ocena jest osobnym krokiem (score.py), dzięki czemu odpowiedzi testowe można zapisać bez oceniania."""
import json
import os
import time
from pathlib import Path

from asystent import config, tools
from asystent.tasks import TaskStore


def load_gold(split=None, extra=True):
    """Zbiór z gold_set.jsonl; dla dev dokłada własne pytania agenta (src/ocena/dev_extra.json), jeśli extra=True."""
    rows = [json.loads(l) for l in open(config.DATA / "gold_set.jsonl", encoding="utf-8")]
    rows = [r for r in rows if split is None or r["split"] == split]
    if extra and split == "dev":
        rows += json.load(open(Path(__file__).parent / "dev_extra.json", encoding="utf-8"))["questions"]
    return rows


def run(variant_factory, questions, out_path, run_id=0, sanitize_docs=True, extra=None, log=print):
    """variant_factory(toolbox) -> obiekt z .answer(question) -> str | dict(answer, tokens_in, tokens_out, steps, model)."""
    tb = tools.Toolbox(sanitize_docs=sanitize_docs)
    variant = variant_factory(tb)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():   # wznowienie po przerwaniu: nie powtarzamy gotowych pytań (i nie płacimy drugi raz)
        done = {json.loads(l)["id"] for l in open(out_path, encoding="utf-8")}
    with open(out_path, "a", encoding="utf-8") as f:
        for q in questions:
            if q["id"] in done:
                continue
            tp = config.CACHE / "runs" / f"{out_path.stem}_{q['id']}.json"
            tp.parent.mkdir(parents=True, exist_ok=True)
            if tp.exists():
                tp.unlink()
            # Każde pytanie dostaje własny, pusty magazyn zadań: szkice jednego pytania nie mieszają się z innymi i są widoczne w wyniku.
            tb.tasks = TaskStore(tp)
            tb.trace = []
            t0 = time.time()
            err = None
            try:
                res = variant.answer(q["question"])
            except Exception as e:      # awaria jednego pytania nie zatrzymuje przebiegu; trafia do wyniku jako błąd
                res, err = "", f"{type(e).__name__}: {str(e)[:300]}"
            if isinstance(res, str):
                res = {"answer": res}
            rec = {"id": q["id"], "category": q["category"], "split": q["split"], "question": q["question"],
                   "variant": getattr(variant, "name", "?"), "run": run_id, "answer": res.get("answer", ""),
                   "trace": list(tb.trace), "tasks_after": tb.tasks.list(), "tokens_in": res.get("tokens_in", 0),
                   "tokens_out": res.get("tokens_out", 0), "steps": res.get("steps", len(tb.trace)),
                   "latency_s": round(time.time() - t0, 2), "model": res.get("model"), "error": err or res.get("error"),
                   **(extra or {})}
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            f.flush()
            log(f"{q['id']} {rec['latency_s']}s steps={rec['steps']} tok={rec['tokens_in'] + rec['tokens_out']} err={rec['error']}")
    return out_path
