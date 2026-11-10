"""Zadania okresowe: python -m svc.maintenance [expire] [retention DNI].
expire     oznacza wygasłe zatwierdzenia i kończy ich wątki (węzeł decyzji dostaje 'expire')
retention  usuwa punkty kontrolne zakończonych wątków starszych niż N dni (domyślnie 30); wątki wstrzymane nie są ruszane"""
import sys

from .config import get_settings
from .graph import Engine
from .store import Store, make_pool


def main(argv):
    s = get_settings()
    pool = make_pool(s)
    store = Store(pool, s.approval_ttl_hours)
    eng = Engine(store, pool, s)
    cmd = argv[0] if argv else "expire"
    if cmd == "expire":
        rows = store.expire_due()
        for r in rows:
            eng.resume(r["thread_id"], {"action": "expire"})
        print(f"wygasło zatwierdzeń: {len(rows)}")
    elif cmd == "retention":
        days = int(argv[1]) if len(argv) > 1 else 30
        old = store._all("SELECT thread_id FROM threads t WHERE created_at < now() - make_interval(days => %s) "
                         "AND NOT EXISTS (SELECT 1 FROM tasks k WHERE k.thread_id=t.thread_id AND k.status='oczekuje')", (days,))
        for r in old:
            eng.saver.delete_thread(str(r["thread_id"]))
        print(f"usunięto punkty kontrolne wątków: {len(old)}")
    pool.close()


if __name__ == "__main__":
    main(sys.argv[1:])
