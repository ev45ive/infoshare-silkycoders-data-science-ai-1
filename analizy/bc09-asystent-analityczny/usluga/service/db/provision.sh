#!/bin/bash
# Tworzy bazę stanu usługi BC-09 w lokalnej instancji PostgreSQL (kontener retaildw-postgres-1) jako administrator lokalny.
# NIE dotyka bazy retaildw. Usunięcie: ./drop_state_db.sh. Hasła i sekrety tylko z service/.env (plik poza repozytorium).
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
C=retaildw-postgres-1
psqla() { docker exec -i "$C" psql -U postgres -v ON_ERROR_STOP=1 "$@"; }

psqla <<SQL
SELECT 'CREATE ROLE bc09_state_owner LOGIN' WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='bc09_state_owner')\gexec
SELECT 'CREATE ROLE bc09_svc LOGIN' WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='bc09_svc')\gexec
ALTER ROLE bc09_state_owner PASSWORD '${BC09_STATE_OWNER_PASSWORD}';
ALTER ROLE bc09_svc PASSWORD '${BC09_STATE_SVC_PASSWORD}' NOCREATEDB NOCREATEROLE;
SELECT 'CREATE DATABASE retaildw_bc09_state OWNER bc09_state_owner' WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname='retaildw_bc09_state')\gexec
REVOKE ALL ON DATABASE retaildw_bc09_state FROM PUBLIC;
GRANT CONNECT ON DATABASE retaildw_bc09_state TO bc09_svc;
SQL

# migracje rolą właściciela (wejście przez stdin: bez ścieżek hosta w poleceniu docker)
for f in db/migrations/*.sql; do
  echo "migracja: $f"
  docker exec -i -e PGPASSWORD="${BC09_STATE_OWNER_PASSWORD}" "$C" psql -h 127.0.0.1 -U bc09_state_owner -d retaildw_bc09_state -v ON_ERROR_STOP=1 -q < "$f"
done
echo "gotowe: baza retaildw_bc09_state (role: bc09_state_owner, bc09_svc)"
