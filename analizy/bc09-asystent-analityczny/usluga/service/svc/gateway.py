"""Bramka modelu językowego dla usługi: limit dzienny tokenów na użytkownika i limit czasu żądania. Wywołanie idzie przez rdzeń (core.llm.chat),
więc obowiązuje też łączny twardy limit z rejestru (3 mln tokenów dla całego BC-09)."""
import time

from core import llm as core_llm


class QuotaExceeded(Exception):
    pass


class RequestTimeout(Exception):
    pass


def make_chat(store, user_id, daily_limit, timeout_s, base_chat=None, label="svc"):
    # Zwraca funkcję `chat` o tym samym interfejsie co core.llm.chat, którą rdzeń woła zamiast bezpośrednio modelu (wstrzyknięcie zależności).
    # Przed każdym wywołaniem sprawdza limit dzienny użytkownika i czas żądania, po wywołaniu dopisuje zużycie do bazy.
    # base_chat pozwala w testach podstawić fałszywy model (bez kosztu i sieci).
    base = base_chat or core_llm.chat
    t0 = time.time()

    def chat(messages, tools=None, label_="", model=None, max_tokens=1200):
        if store.tokens_today(user_id) >= daily_limit:
            raise QuotaExceeded("Dzienny limit tokenów wyczerpany.")
        if time.time() - t0 > timeout_s:
            raise RequestTimeout("Przekroczono limit czasu żądania.")
        m, tin, tout = base(messages, tools, label)
        store.add_usage(user_id, tin + tout)
        return m, tin, tout

    return chat
