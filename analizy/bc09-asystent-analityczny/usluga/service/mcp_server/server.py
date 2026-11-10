"""Serwer MCP (oficjalny SDK `mcp` 2.x, klasa MCPServer, transport stdio). Woła API z tokenem użytkownika; nie ma dostępu do bazy ani do modelu.
Wystawione narzędzia: zapytaj_asystenta, status_zadania, szukaj_procedur. NIE MA narzędzia zatwierdzającego: zatwierdzenie robi człowiek w interfejsie zatwierdzeń."""
import os

import httpx
from mcp.server import MCPServer

API = os.environ.get("BC09_API_URL", "http://127.0.0.1:8000")
mcp = MCPServer("nordvik-asystent", instructions="Asystent analityczny Nordvik: pytania o dane i procedury. Zadania wymagają zatwierdzenia człowieka poza tym narzędziem.")


def _call(method, path, **kw):
    # Token użytkownika pochodzi ze zmiennej środowiskowej konfiguracji klienta MCP (nie z argumentów narzędzia, które widzi model). Serwer MCP ma więc
    # dokładnie takie uprawnienia jak ten użytkownik w API: nie więcej. Błędy wracają jako krótki tekst dla modelu klienta.
    token = os.environ.get("BC09_API_TOKEN")
    if not token:
        return None, "Brak tokenu: ustaw BC09_API_TOKEN (patrz mcp.json.example)."
    try:
        r = httpx.request(method, API + path, headers={"Authorization": f"Bearer {token}"}, timeout=200, **kw)
    except httpx.HTTPError:
        return None, "Brak połączenia z usługą."
    if r.status_code >= 400:
        d = r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else None
        return None, f"Błąd {r.status_code}: {d if isinstance(d, str) else 'żądanie odrzucone'}"
    return r.json(), None


@mcp.tool()
def zapytaj_asystenta(question: str, thread_id: str | None = None) -> str:
    """Zadaje pytanie asystentowi (dane, procedury, prognoza). Zwraca odpowiedź, kroki narzędzi i status zadania; zadania czekają na zatwierdzenie człowieka."""
    if thread_id is None:
        t, err = _call("POST", "/threads", json={})
        if err:
            return err
        thread_id = t["thread_id"]
    a, err = _call("POST", f"/threads/{thread_id}/messages", json={"question": question})
    if err:
        return err
    out = f"{a['answer']}\n\n[wątek: {thread_id}; tokeny: {a['tokens']}; narzędzia: {', '.join(s['tool'] for s in a['steps']) or '-'}]"
    if a["status"] == "awaiting_approval":
        out += f"\n[Zadanie #{a['task']['task_id']} czeka na zatwierdzenie przez uprawnioną osobę; to narzędzie nie może go zatwierdzić.]"
    return out


@mcp.tool()
def status_zadania(task_id: int) -> str:
    """Zwraca status własnego zadania (szkic, oczekuje, zatwierdzone, odrzucone, wygasle)."""
    t, err = _call("GET", f"/tasks/{task_id}")
    return err or f"Zadanie #{t['task_id']}: {t['status']} (tytuł: {t['title']})"


@mcp.tool()
def szukaj_procedur(query: str) -> str:
    """Wyszukuje dokumenty procedur Nordvik i zwraca fragmenty z wersją, datą i właścicielem (bez udziału modelu językowego)."""
    hits, err = _call("GET", "/procedures/search", params={"q": query})
    if err:
        return err
    return "\n\n".join(f"{h['title']} v{h['version']} (od {h['valid_from']}, {h['owner']}, status: {h['status']})\n{h['snippet']}" for h in hits) or "Brak pasujących dokumentów."


if __name__ == "__main__":
    mcp.run(transport="stdio")
