"""Operacje administracyjne (CLI): python -m svc.admin <polecenie>.
  setup                      tworzy tabele punktów kontrolnych LangGraph (rolą właściciela; rola usługi nie ma CREATE)
  seed-users                 zakłada użytkowników szkoleniowych (ala, bartek: wnioskodawcy; celina: zatwierdzająca), hasła z .env
  create-user LOGIN ROLA     hasło z BC09_NEW_USER_PASSWORD
  deactivate LOGIN | activate LOGIN
Hasła nigdy nie są wypisywane."""
import os
import sys

from psycopg import connect
from psycopg.rows import dict_row

from .auth import hash_password
from .config import get_settings
from .store import Store, make_pool


def cmd_setup():
    from langgraph.checkpoint.postgres import PostgresSaver
    s = get_settings(owner=True)
    with connect(s.conninfo, autocommit=True, row_factory=dict_row, options="-c search_path=svc") as conn:
        PostgresSaver(conn).setup()
    print("tabele punktów kontrolnych gotowe (schemat svc)")


def main(argv):
    if not argv:
        print(__doc__); return 1
    if argv[0] == "setup":
        cmd_setup(); return 0
    store = Store(make_pool(get_settings()))
    if argv[0] == "seed-users":
        for login, role, env in (("ala", "requester", "BC09_SEED_PW_ALA"), ("bartek", "requester", "BC09_SEED_PW_BARTEK"), ("celina", "approver", "BC09_SEED_PW_CELINA")):
            store.create_user(login, hash_password(os.environ[env]), role)
        print("użytkownicy szkoleniowi gotowi: ala, bartek (wnioskodawcy), celina (zatwierdzająca); hasła w .env")
    elif argv[0] == "create-user" and len(argv) == 3 and argv[2] in ("requester", "approver"):
        store.create_user(argv[1], hash_password(os.environ["BC09_NEW_USER_PASSWORD"]), argv[2]); print("utworzono", argv[1])
    elif argv[0] in ("deactivate", "activate") and len(argv) == 2:
        print(store.set_active(argv[1], argv[0] == "activate"))
    else:
        print(__doc__); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
