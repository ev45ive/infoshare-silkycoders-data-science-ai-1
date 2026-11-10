#!/bin/bash
# Usuwa bazę stanu i role usługi BC-09 (nieodwracalne: kasuje użytkowników, rozmowy, zadania, audyt i punkty kontrolne). Baza retaildw nietknięta.
set -euo pipefail
C=retaildw-postgres-1
read -r -p "Usunąć bazę retaildw_bc09_state i role bc09_*? wpisz TAK: " ans
[ "$ans" = "TAK" ] || { echo "przerwano"; exit 1; }
docker exec -i "$C" psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
DROP DATABASE IF EXISTS retaildw_bc09_state WITH (FORCE);
DROP ROLE IF EXISTS bc09_svc;
DROP ROLE IF EXISTS bc09_state_owner;
SQL
echo "usunięto"
