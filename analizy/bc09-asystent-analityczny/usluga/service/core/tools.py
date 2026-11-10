"""Zestaw narzędzi asystenta. Jedyne punkty wejścia modelu to TOOL_NAMES; każde wywołanie jest rejestrowane."""
import json
import time

from . import config, db, docs
from .forecast import Forecaster
from .tasks import TaskStore

TOOL_NAMES = ("run_sql", "search_docs", "forecast", "propose_task")   # brak approve_task: zatwierdza tylko człowiek

# Opisy narzędzi w formacie wywołań funkcji: model widzi tylko name, description i parameters. Opis jest częścią instrukcji,
# dlatego zawiera limity (wiersze, czas) i zasady użycia (np. tabele zawsze ze schematem).
TOOL_SPECS = [
    {"type": "function", "function": {
        "name": "run_sql",
        "description": "Wykonuje JEDNO zapytanie SELECT (DuckDB) na schematach dbo i reporting (tylko odczyt, maks. "
                       f"{config.SQL_MAX_ROWS} wierszy, limit czasu {config.SQL_TIMEOUT_S} s). Tabele zawsze ze schematem, np. dbo.FactSales.",
        "parameters": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}}},
    {"type": "function", "function": {
        "name": "search_docs",
        "description": "Wyszukuje DOKUMENTY procedur Nordvik (najlepsze 3; pełna treść z wersją, datą obowiązywania, właścicielem i statusem). "
                       "Można też podać doc_id (np. D09), aby przeczytać konkretny dokument. Gdy tytuł ma kilka wersji, zwracane są wszystkie.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer", "default": 3},
                                                        "doc_id": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "forecast",
        "description": "Prognoza sprzedaży w SZTUKACH na tygodnie ISO (model sezonowy z przedziałem 80%). Podaj style_code (model) albo "
                       "category; opcjonalnie store_code (bez niego zwraca wszystkie lokalizacje). Dla modeli bez historii odmawia z powodem.",
        "parameters": {"type": "object", "properties": {
            "start_week": {"type": "string", "description": "np. 2026-W39"}, "n_weeks": {"type": "integer", "default": 4},
            "style_code": {"type": "string"}, "category": {"type": "string"}, "store_code": {"type": "string"}},
            "required": ["start_week"]}}},
    {"type": "function", "function": {
        "name": "propose_task",
        "description": "Tworzy WYŁĄCZNIE szkic zadania dla człowieka (status 'szkic'). Nie zatwierdza i nie wykonuje zadania.",
        "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "description": {"type": "string"},
                                                        "owner": {"type": "string", "description": "zespół/osoba odpowiedzialna"}},
                       "required": ["title", "description", "owner"]}}},
]


class Toolbox:
    def __init__(self, con=None, tasks_path=None, sanitize_docs=True, column_warnings=True, docs_dir=None, tasks=None, shared=None):
        self.con = con or db.open_readonly()
        self.column_warnings = column_warnings
        if shared is not None:   # DI: indeks dokumentów i prognoza są niezmienne, więc współdzielone między żądaniami
            self.quarantine, self.index, self.forecaster = shared.quarantine, shared.index, shared.forecaster
        else:
            chunks, self.quarantine = docs.load_docs(sanitize=sanitize_docs, docs_dir=docs_dir or config.DOCS)
            self.index = docs.DocIndex(chunks)
            self.forecaster = Forecaster(self.con)
        self.tasks = tasks if tasks is not None else TaskStore(tasks_path or config.TASKS_PATH)
        self.trace = []

    def call(self, name, args):
        # Jedyny punkt wejścia modelu do narzędzi. Nieznana nazwa (np. approve_task), błędne argumenty i odrzucone zapytanie SQL
        # wracają do modelu jako zwykły wynik z ok=False i powodem, a nie jako wyjątek: model może poprawić wywołanie.
        t0 = time.time()
        if name not in TOOL_NAMES:
            out = {"ok": False, "error": f"Nieznane narzędzie: {name}. Dostępne: {', '.join(TOOL_NAMES)}."}
        else:
            try:
                out = getattr(self, "_" + name)(**(args or {}))
            except TypeError as e:
                out = {"ok": False, "error": f"Błędne argumenty: {e}"}
            except db.SqlRejected as e:
                out = {"ok": False, "error": str(e), "rejected": True}
        # Każde wywołanie (także nieudane) trafia do śladu: z niego korzystają oceniacz (które narzędzia, ile zbędnych wywołań) i audyt.
        self.trace.append({"tool": name, "args": args, "ok": bool(out.get("ok")), "error": out.get("error"),
                           "refused": out.get("refused"), "ms": int((time.time() - t0) * 1000)})
        return out

    def _run_sql(self, sql):
        cols, rows, trunc = db.run_select(self.con, sql)
        out = {"ok": True, "columns": cols, "rows": [list(r) for r in rows], "n_rows": len(rows), "truncated": trunc}
        if self.column_warnings:
            w = db.column_warnings(sql)
            if w:
                out["warnings"] = w
        return out

    def _search_docs(self, query="", k=3, doc_id=None):
        res = self.index.search_docs(query, max(1, min(int(k), 5)), doc_id)
        # dokument o tym samym tytule w innej wersji dokładamy zawsze, żeby model mógł pokazać konflikt/nieaktualność
        have = {r["doc_id"] for r in res}
        titles = {r["title"] for r in res}
        for d in sorted({c.doc_id for c in self.index.chunks if c.title in titles}):
            if d not in have:
                res += self.index.search_docs("", doc_id=d)
        return {"ok": True, "results": res}

    def _forecast(self, **kw):
        return self.forecaster.forecast(**kw)

    def _propose_task(self, title, description, owner):
        t = self.tasks.propose(title, description, owner)
        return {"ok": True, "task": t, "note": "Utworzono szkic. Zatwierdzić może wyłącznie człowiek poza asystentem."}


def to_json(obj, limit=6000):
    # Wynik narzędzia dla modelu: JSON obcięty do `limit` znaków, żeby jeden duży wynik nie zalewał kontekstu.
    s = json.dumps(obj, ensure_ascii=False, default=str)
    return s if len(s) <= limit else s[:limit] + '..."[obcięto]"'
