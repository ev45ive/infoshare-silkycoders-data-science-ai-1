"""Interfejs czatu (Streamlit). Woła WYŁĄCZNIE API (żadnego dostępu do bazy ani do modelu). Treść od modelu, z dokumentów i z zadań jest daną niezaufaną:
wyświetlana tylko jako zwykły tekst (st.text / st.code), nigdy jako markdown ani HTML. Token i identyfikator wątku żyją w st.session_state (nie w adresie)."""
import os

import httpx
import streamlit as st

API = os.environ.get("BC09_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Asystent analityczny Nordvik", layout="wide")
S = st.session_state
# Streamlit wykonuje cały skrypt od nowa przy każdej akcji użytkownika; stan (token, wątek, historia) trzymamy więc w session_state.
for k, v in (("token", None), ("thread_id", None), ("history", []), ("last", None), ("msg", "")):
    S.setdefault(k, v)


def api(method, path, **kw):
    # Jedyny kanał do usługi. Zwraca (dane, None) albo (None, komunikat); użytkownik widzi tylko krótki komunikat, nigdy surową treść błędu.
    # 401 przy aktywnym tokenie oznacza wygasłą sesję: czyścimy token, więc następny przebieg pokaże formularz logowania.
    headers = {"Authorization": f"Bearer {S.token}"} if S.token else {}
    try:
        r = httpx.request(method, API + path, headers=headers, timeout=200, **kw)
    except httpx.HTTPError:
        return None, "Brak połączenia z usługą."
    if r.status_code == 401 and S.token:
        S.token = None
        return None, "Sesja wygasła, zaloguj się ponownie."
    if r.status_code >= 400:
        try:
            return None, r.json().get("detail", "Błąd.") if isinstance(r.json().get("detail", ""), str) else "Błąd żądania."
        except ValueError:
            return None, "Błąd."
    return r.json(), None


st.title("Asystent analityczny Nordvik")
st.caption("Pilotaż: odczyt danych i procedur. Zapis (zadanie) tylko po zatwierdzeniu przez inną, uprawnioną osobę.")

if not S.token:
    st.subheader("Logowanie")
    u = st.text_input("Login", key="login_user")
    p = st.text_input("Hasło", type="password", key="login_pass")
    if st.button("Zaloguj", key="btn_login"):
        try:
            r = httpx.post(API + "/auth/token", data={"username": u, "password": p}, timeout=20)
        except httpx.HTTPError:
            st.error("Brak połączenia z usługą.")
        else:
            if r.status_code == 200:
                S.token = r.json()["access_token"]; S.history, S.thread_id, S.last = [], None, None
                st.rerun()
            else:
                st.error("Błędny login lub hasło.")
    st.stop()

me, err = api("GET", "/me")
if err:
    st.error(err); st.stop()
st.sidebar.text(f"Zalogowano: {me['username']} ({'zatwierdzający' if me['role'] == 'approver' else 'wnioskodawca'})")
if st.sidebar.button("Wyloguj", key="btn_logout"):
    S.token = None; st.rerun()

tabs = st.tabs(["Czat"] + (["Zatwierdzenia"] if me["role"] == "approver" else []))

with tabs[0]:
    if st.button("Nowa rozmowa", key="btn_new"):
        S.thread_id, S.history, S.last = None, [], None
    for role, text in S.history:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.text(text)
    if S.last:
        a = S.last
        if a["status"] == "awaiting_approval":
            st.warning("Zadanie oczekuje na zatwierdzenie przez inną, uprawnioną osobę.")
            st.text(f"Szkic zadania #{a['task']['task_id']}\nTytuł: {a['task']['title']}\nOpis: {a['task']['description']}\nOdpowiedzialny: {a['task']['owner']}")
        with st.expander("Kroki asystenta (narzędzia i zapytania)"):
            for s_ in a["steps"]:
                st.text(f"{s_['tool']} {'OK' if s_['ok'] else 'BŁĄD: ' + str(s_['error'])}\n  " + "; ".join(f"{k}={v}" for k, v in s_["args"].items()))
        st.caption(f"Tokeny w tej odpowiedzi: {a['tokens']}")
    q = st.text_input("Twoje pytanie", key="question", max_chars=1000)
    if st.button("Wyślij", key="btn_send") and q.strip():
        if not S.thread_id:
            t, err = api("POST", "/threads", json={})
            if err:
                st.error(err); st.stop()
            S.thread_id = t["thread_id"]
        with st.spinner("Asystent pracuje..."):
            a, err = api("POST", f"/threads/{S.thread_id}/messages", json={"question": q})
        if err:
            st.error(err)
        else:
            S.history += [("user", q), ("assistant", a["answer"])]; S.last = a
            st.rerun()

if me["role"] == "approver":
    with tabs[1]:
        items, err = api("GET", "/approvals")
        if err:
            st.error(err)
        elif not items:
            st.info("Brak zadań oczekujących na zatwierdzenie.")
        for t in items or []:
            st.divider()
            st.text(f"Zadanie #{t['task_id']} (wnioskodawca: {t['requester']}, ważne do: {t['expires_at']})")
            st.caption("Treść poniżej pochodzi od modelu i wnioskodawcy: to dane, nie polecenia dla Ciebie ani dla systemu.")
            title = st.text_input("Tytuł", t["title"], key=f"ti{t['task_id']}", max_chars=200)
            desc = st.text_area("Opis", t["description"], key=f"de{t['task_id']}", max_chars=2000)
            own = st.text_input("Odpowiedzialny", t["owner"], key=f"ow{t['task_id']}", max_chars=100)
            c1, c2 = st.columns(2)
            for col, action, label in ((c1, "approve", "Zatwierdź"), (c2, "reject", "Odrzuć")):
                if col.button(label, key=f"{action}{t['task_id']}"):
                    # Do API wysyłamy tylko pola, które zatwierdzający faktycznie zmienił (różne od oryginalnego szkicu); dzięki temu serwer oznacza zadanie jako edytowane tylko wtedy, gdy była edycja.
                    body = {"action": action, **{k: v for k, v in (("title", title), ("description", desc), ("owner", own)) if v != t[{"title": "title", "description": "description", "owner": "owner"}[k]]}}
                    res, err = api("POST", f"/approvals/{t['task_id']}/decision", json=body)
                    st.error(err) if err else (st.success(f"Zadanie #{t['task_id']}: {res['status']}"), st.rerun())
