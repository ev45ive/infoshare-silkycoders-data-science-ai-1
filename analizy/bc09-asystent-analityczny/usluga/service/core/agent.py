"""Warianty z modelem językowym: W2 (RAG bez liczb), W3 (agent z narzędziami), W4 (orkiestrator + sub-agenci SQL i dokumenty).
Najmniejsza własna pętla wywołań narzędzi, bez frameworka."""
import json

from . import config, llm, prompts, tools
from .tools import TOOL_SPECS, to_json

SPEC = {s["function"]["name"]: s for s in TOOL_SPECS}
MAX_TOOL_CALLS = 14


class Usage:
    # Licznik zużycia na jedno pytanie: tokeny wejścia i wyjścia oraz liczba wywołań modelu. W W4 współdzielony przez orkiestratora i sub-agentów.
    def __init__(self):
        self.tin = self.tout = self.calls = 0

    def add(self, i, o):
        self.tin += i
        self.tout += o
        self.calls += 1

    @property
    def total(self):
        return self.tin + self.tout


def run_loop(system, user, specs, dispatch, usage, label, max_steps=config.MAX_STEPS, budget=config.PER_QUESTION_TOKEN_LIMIT, chat=None):
    """Pętla narzędzi z limitem rund i tokenów na pytanie. Po wyczerpaniu limitu wymuszamy odpowiedź bez narzędzi."""
    chat = chat or llm.chat   # DI: usługa wstrzykuje bramkę z limitem na użytkownika
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    n_calls = 0
    # Jedna runda = jedno wywołanie modelu. Jeśli model nie prosi o narzędzia, to koniec: to jest odpowiedź. Jeśli prosi, wykonujemy je
    # i oddajemy wyniki modelowi (wiadomości 'tool'), a on decyduje, co dalej. Limity rund i tokenów chronią przed nieskończoną pętlą.
    for _ in range(max_steps):
        if usage.total > budget:
            break
        m, i, o = chat(msgs, specs, label)
        usage.add(i, o)
        if not m.tool_calls:
            return m.content or ""
        msgs.append({"role": "assistant", "content": m.content, "tool_calls": [
            {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in m.tool_calls]})
        for tc in m.tool_calls:
            # Argumenty wywołania to tekst JSON od modelu: błędny JSON i przekroczenie limitu wywołań wracają do modelu jako błąd narzędzia,
            # a nie jako wyjątek (model może się poprawić).
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = None
            if args is None:
                res = {"ok": False, "error": "Argumenty nie są poprawnym JSON."}
            elif n_calls >= MAX_TOOL_CALLS:
                res = {"ok": False, "error": "Limit wywołań narzędzi na pytanie wyczerpany."}
            else:
                n_calls += 1
                res = dispatch(tc.function.name, args)
            msgs.append({"role": "tool", "tool_call_id": tc.id, "content": to_json(res, 14000 if tc.function.name == "search_docs" else 4500)})
    # Po wyczerpaniu rund lub tokenów prosimy o odpowiedź BEZ narzędzi, z jawnym wskazaniem, czego nie udało się sprawdzić.
    msgs.append({"role": "user", "content": "Limit kroków wyczerpany. Odpowiedz teraz na podstawie tego, co ustalono; wyraźnie wskaż, czego nie udało się sprawdzić."})
    m, i, o = chat(msgs, None, label)
    usage.add(i, o)
    return m.content or ""


def _result(text, usage, name, extra=None):
    return {"answer": text, "tokens_in": usage.tin, "tokens_out": usage.tout, "steps": usage.calls, "model": config.LLM_MODEL, **(extra or {})}


class W2:
    """RAG bez narzędzi: fragmenty dokumentów w kontekście (BM25), brak dostępu do liczb."""
    name = "W2"

    def __init__(self, tb, label="W2", k=5):
        self.tb, self.label, self.k = tb, label, k
        self.system = (prompts._COMMON + "\n\nW tym trybie NIE masz dostępu do danych liczbowych (sprzedaż, zapasy, prognozy) ani do narzędzi: "
                       "na pytania o liczby napisz, że nie masz do nich dostępu. Nie zmieniasz danych i nie tworzysz zadań.\n\n"
                       + prompts.RULES_DOCS + "\n\n" + prompts.RULES_REFUSAL)

    def answer(self, question):
        usage = Usage()
        res = self.tb.call("search_docs", {"query": question, "k": 3})["results"]
        ctx = "\n\n".join(
            f"[{r['doc_id']} | {r['title']} | wersja {r['version']} | obowiązuje od {r['valid_from']} | właściciel: {r['owner']} | status: {r['status']}]\n{r['text']}"
            for r in res) or "(brak pasujących dokumentów)"
        user = f"FRAGMENTY DOKUMENTÓW:\n{ctx}\n\nPYTANIE: {question}"
        m, i, o = llm.chat([{"role": "system", "content": self.system}, {"role": "user", "content": user}], None, self.label)
        usage.add(i, o)
        return _result(m.content or "", usage, self.name)


class W3:
    """Agent z narzędziami run_sql, search_docs, forecast, propose_task."""
    name = "W3"

    def __init__(self, tb, label="W3", use_dict=True, max_steps=config.MAX_STEPS, names=("run_sql", "search_docs", "forecast", "propose_task"),
                 conflict_rule=True, chat=None):
        self.tb, self.label, self.max_steps, self.chat = tb, label, max_steps, chat
        self.tb.column_warnings = use_dict   # wariant bez słownika (H2) nie dostaje też ostrzeżeń o kolumnach
        self.system = prompts.build_system(use_dict=use_dict, con=tb.con, conflict_rule=conflict_rule)
        self.specs = [SPEC[n] for n in names]

    def answer(self, question):
        usage = Usage()
        text = run_loop(self.system, question, self.specs, self.tb.call, usage, self.label, self.max_steps, chat=self.chat)
        return _result(text, usage, self.name)


class W4:
    """Orkiestrator + sub-agenci. Orkiestrator deleguje liczby (ask_sql) i procedury (ask_docs); forecast i propose_task wywołuje sam."""
    name = "W4"

    def __init__(self, tb, label="W4"):
        self.tb, self.label = tb, label
        con = tb.con
        self.sql_system = prompts.SQL_AGENT + "\n\nSCHEMAT:\n" + prompts.schema_text(con) + "\n" + prompts.schema_notes() + \
            "\n\nSŁOWNIK METRYK:\n" + prompts.metric_dictionary()
        self.doc_system = prompts.DOC_AGENT + "\n\n" + prompts.RULES_DOCS
        self.orch_system = (prompts._COMMON + "\n\nJesteś orkiestratorem. Nie masz bezpośredniego dostępu do SQL ani dokumentów: deleguj przez ask_sql (liczby z hurtowni; "
                            "podaj w zadaniu dokładnie okres, przekrój i metrykę) i ask_docs (procedury). Prognozy robisz narzędziem forecast, szkice zadań propose_task. "
                            "Liczby i cytaty przepisuj z odpowiedzi sub-agentów bez zmian (nie licz z pamięci). Cytaty (Tytuł, vX.Y), konflikty i statusy NIEAKTUALNY "
                            "przekaż użytkownikowi. Gdy odpowiedź jest listą obiektów (np. sklepów), zakończ ją linią: LISTA: kod1, kod2. Poniżej reguły obowiązujące też Ciebie:\n\n"
                            + prompts.RULES_REFUSAL + "\n\n" + prompts.RULES_DOCS)
        self.specs = [
            {"type": "function", "function": {"name": "ask_sql", "description": "Zleca sub-agentowi SQL policzenie liczb z hurtowni (zadanie w języku naturalnym, dokładny okres i przekrój).",
                                              "parameters": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]}}},
            {"type": "function", "function": {"name": "ask_docs", "description": "Zleca sub-agentowi dokumentów znalezienie procedury; zwraca podsumowanie z cytatami, konfliktami i statusami.",
                                              "parameters": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]}}},
            SPEC["forecast"], SPEC["propose_task"]]

    def answer(self, question):
        usage = Usage()

        def dispatch(name, args):
            # Orkiestrator woła sub-agentów jak narzędzia: ask_sql i ask_docs uruchamiają własne, mniejsze pętle (z własnym promptem
            # i tylko jednym narzędziem); forecast i propose_task idą bezpośrednio do skrzynki narzędzi.
            if name == "ask_sql":
                t = run_loop(self.sql_system, str(args.get("task", "")), [SPEC["run_sql"]], self.tb.call, usage, self.label + ":sql", 6)
                return {"ok": True, "summary": t}
            if name == "ask_docs":
                t = run_loop(self.doc_system, str(args.get("task", "")), [SPEC["search_docs"]], self.tb.call, usage, self.label + ":docs", 4)
                return {"ok": True, "summary": t}
            return self.tb.call(name, args)

        text = run_loop(self.orch_system, question, self.specs, dispatch, usage, self.label + ":orch", config.MAX_STEPS)
        return _result(text, usage, self.name)
