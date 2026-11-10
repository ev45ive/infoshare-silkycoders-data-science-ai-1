#!/usr/bin/env bash
# Manage the local RetailDW PostgreSQL database (docker compose + psql inside the container).
# Run `./retaildw.sh help` for the command list.
set -euo pipefail

CALLER_PWD=$PWD
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Relative paths only from here on: Git Bash path rewriting breaks absolute paths passed to docker.exe.
cd "$ROOT"
DB_DIR=db

DB_NAME=retaildw
OWNER=retaildw
RO_USER=retaildw_ro

die()  { echo "error: $*" >&2; exit 1; }
info() { echo "==> $*"; }

usage() {
    cat <<'EOF'
Usage: ./retaildw.sh <command> [options]

Lifecycle
  up                 Start the container if needed, then run baseline and migrate.
  down               Stop and remove the container; the data volume is kept.
  reset [-y|--yes]   DESTROY the data volume, then rebuild everything (setup). Asks first.
  setup              up + seed + load: a complete working database from scratch (safe to repeat).

Schema and data
  baseline           Idempotent setup: roles (passwords re-synced from .env), database, schemas, grants.
  migrate            Apply outstanding db/migrations/V###__*.sql (each in one transaction, tracked
                     in ops.schema_migrations with a checksum).
  seed               Seed dimensions and generate source data into src.* (no-op if already filled).
  load               Full reload of stg.* and dw.* from src.* via etl.load_* procedures.

Inspect
  status             Container, connection info, migration state and row counts.
  query [opts] SQL   Run SQL. Options: --ro (read-only role), --csv, -f FILE. SQL may also be piped in.
  psql [--ro]        Interactive psql session.
  logs [args]        Container logs (default: last 100 lines; e.g. `logs -f`).

Settings come from .env (copy .env.example). Examples:
  ./retaildw.sh setup
  ./retaildw.sh query "SELECT year_month, SUM(net_amount) FROM reporting.sales_daily GROUP BY 1 ORDER BY 1"
  ./retaildw.sh query --ro --csv -f report.sql > report.csv
EOF
}

load_env() {
    local line key val
    [[ -f .env ]] || die ".env not found. Create it with: cp .env.example .env"
    while IFS= read -r line || [[ -n $line ]]; do
        line=${line%$'\r'}
        if [[ -z $line || $line == \#* || $line != *=* ]]; then continue; fi
        key=${line%%=*}
        val=${line#*=}
        if [[ $key =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then export "$key=$val"; fi
    done < .env
    for key in POSTGRES_PASSWORD RETAILDW_PASSWORD RETAILDW_RO_PASSWORD; do
        [[ -n ${!key:-} ]] || die "$key is missing or empty in .env"
    done
    PG_PORT=${PG_PORT:-5433}
}

require_docker() {
    command -v docker >/dev/null 2>&1 || die "docker not found in PATH"
    docker info >/dev/null 2>&1 || die "Docker daemon is not running"
}

dc() { docker compose "$@"; }

is_running() { [[ -n $(dc ps --status running -q postgres 2>/dev/null) ]]; }

require_running() {
    is_running || die "database container is not running. Start it with: ./retaildw.sh up"
}

# psql_as <role> <database> [psql args...]; SQL comes from stdin unless -c/-f is given.
# Role passwords are not needed: inside the container local connections use trust authentication.
psql_as() {
    local role=$1 db=$2
    shift 2
    dc exec -T -e PGOPTIONS="-c client_min_messages=warning" postgres \
        psql -X -q -v ON_ERROR_STOP=1 -U "$role" -d "$db" "$@"
}

sha256() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
    else shasum -a 256 "$1" | cut -d' ' -f1
    fi
}

# Interactive sessions in Git Bash (mintty) need winpty to get a TTY.
tty_wrap() {
    if [[ ${OSTYPE:-} == msys* || ${OSTYPE:-} == cygwin* ]] && command -v winpty >/dev/null 2>&1; then
        winpty "$@"
    else
        "$@"
    fi
}

cmd_up() {
    info "starting container (127.0.0.1:$PG_PORT)"
    dc up -d --wait --wait-timeout 120 postgres
    cmd_baseline
    cmd_migrate
}

cmd_down() {
    dc down
}

cmd_baseline() {
    require_running
    info "baseline: roles, database, schemas, grants"
    psql_as postgres postgres < "$DB_DIR/baseline.sql"
}

cmd_migrate() {
    require_running
    local ledger
    ledger=$(psql_as "$OWNER" "$DB_NAME" -At -c \
        "SELECT filename || '|' || checksum FROM ops.schema_migrations ORDER BY filename") \
        || die "cannot read ops.schema_migrations - run: ./retaildw.sh baseline"

    local f name sum stored n c applied=0
    for f in "$DB_DIR"/migrations/V*.sql; do
        [[ -e $f ]] || continue
        name=$(basename "$f")
        [[ $name =~ ^V[0-9]{3,}__[A-Za-z0-9_.-]+\.sql$ ]] \
            || die "bad migration file name '$name' (expected V###__description.sql)"
        sum=$(sha256 "$f")

        stored=""
        while IFS='|' read -r n c; do
            if [[ $n == "$name" ]]; then stored=$c; break; fi
        done <<< "$ledger"

        if [[ -n $stored ]]; then
            if [[ $stored != "$sum" ]]; then
                echo "warning: $name was edited after it was applied (checksum mismatch). Add a new migration instead." >&2
            fi
            continue
        fi

        info "applying $name"
        { cat "$f"
          printf "\nINSERT INTO ops.schema_migrations (filename, checksum) VALUES ('%s', '%s');\n" "$name" "$sum"
        } | psql_as "$OWNER" "$DB_NAME" --single-transaction -f - \
            || die "migration $name failed and was rolled back"
        applied=$((applied + 1))
    done

    if (( applied == 0 )); then echo "migrate: nothing to apply"; else echo "migrate: $applied applied"; fi
}

cmd_seed() {
    require_running
    local f
    for f in "$DB_DIR"/seed/*.sql; do
        info "seed $(basename "$f")"
        psql_as "$OWNER" "$DB_NAME" --single-transaction -f - < "$f" \
            || die "seed $(basename "$f") failed and was rolled back (run migrate first?)"
    done
}

cmd_load() {
    require_running
    info "ETL: full reload of stg.* and dw.* from src.*"
    # No --single-transaction: the procedures commit their own audit rows.
    psql_as "$OWNER" "$DB_NAME" <<'SQL' || die "load failed - see etl.load_log"
CALL etl.load_sales();
CALL etl.load_inventory();
CALL etl.load_returns();
SELECT package_name, status, rows_read, rows_loaded, rows_rejected
FROM etl.load_log ORDER BY load_id DESC LIMIT 3;
SQL
}

cmd_setup() {
    cmd_up
    cmd_seed
    cmd_load
}

cmd_reset() {
    local answer=""
    if [[ ${1:-} != -y && ${1:-} != --yes ]]; then
        [[ -t 0 ]] || die "reset deletes all data; pass --yes when not running interactively"
        read -r -p "This DELETES the retaildw data volume and rebuilds it. Type 'yes' to continue: " answer
        [[ $answer == yes ]] || die "aborted"
    fi
    info "removing container and data volume"
    dc down -v --remove-orphans
    cmd_setup
}

cmd_status() {
    echo "project dir : $ROOT"
    echo "connect     : psql postgresql://$OWNER@127.0.0.1:$PG_PORT/$DB_NAME   (passwords are in .env)"
    if ! is_running; then
        echo "container   : not running (start with: ./retaildw.sh up)"
        return 0
    fi
    dc ps postgres
    local total applied
    total=$(ls "$DB_DIR"/migrations/V*.sql 2>/dev/null | wc -l | tr -d ' ')
    applied=$(psql_as "$OWNER" "$DB_NAME" -At -c "SELECT count(*) FROM ops.schema_migrations" 2>/dev/null || echo "?")
    echo "migrations  : $applied applied of $total files"
    psql_as "$OWNER" "$DB_NAME" <<'SQL' 2>/dev/null || echo "row counts  : (schema not migrated yet)"
SELECT 'src.sales_raw' AS object, count(*) AS row_count FROM src.sales_raw
UNION ALL SELECT 'src.inventory_raw', count(*) FROM src.inventory_raw
UNION ALL SELECT 'src.returns_raw', count(*) FROM src.returns_raw
UNION ALL SELECT 'dw.dim_date', count(*) FROM dw.dim_date
UNION ALL SELECT 'dw.dim_product', count(*) FROM dw.dim_product
UNION ALL SELECT 'dw.dim_store', count(*) FROM dw.dim_store
UNION ALL SELECT 'dw.fact_sales', count(*) FROM dw.fact_sales
UNION ALL SELECT 'dw.fact_inventory_daily', count(*) FROM dw.fact_inventory_daily
UNION ALL SELECT 'dw.fact_returns', count(*) FROM dw.fact_returns;
SQL
}

cmd_query() {
    local role=$OWNER csv="" file=""
    while (( $# )); do
        case $1 in
            --ro)      role=$RO_USER; shift ;;
            --csv)     csv=--csv; shift ;;
            -f|--file) file=${2:?-f needs a file}; shift 2 ;;
            --)        shift; break ;;
            -*)        die "unknown option: $1" ;;
            *)         break ;;
        esac
    done
    require_running
    if [[ -n $file ]]; then
        if [[ $file != /* && $file != ?:* ]]; then file=$CALLER_PWD/$file; fi
        [[ -r $file ]] || die "cannot read $file"
        psql_as "$role" "$DB_NAME" ${csv:+"$csv"} -f - < "$file"
    elif (( $# )); then
        psql_as "$role" "$DB_NAME" ${csv:+"$csv"} -c "$*"
    elif [[ ! -t 0 ]]; then
        psql_as "$role" "$DB_NAME" ${csv:+"$csv"} -f -
    else
        die "nothing to run. Usage: query [--ro] [--csv] \"SQL\" | query -f FILE | echo SQL | query"
    fi
}

cmd_psql() {
    local role=$OWNER
    if [[ ${1:-} == --ro ]]; then role=$RO_USER; shift; fi
    require_running
    tty_wrap docker compose exec postgres psql -X -U "$role" -d "$DB_NAME" "$@"
}

cmd_logs() {
    if (( $# )); then dc logs "$@" postgres; else dc logs --tail 100 postgres; fi
}

main() {
    local cmd=${1:-help}
    shift || true
    case $cmd in
        help|-h|--help) usage; return 0 ;;
    esac
    require_docker
    load_env
    case $cmd in
        up)       cmd_up ;;
        down)     cmd_down ;;
        baseline) cmd_baseline ;;
        migrate)  cmd_migrate ;;
        seed)     cmd_seed ;;
        load)     cmd_load ;;
        setup)    cmd_setup ;;
        reset)    cmd_reset "$@" ;;
        status)   cmd_status ;;
        query)    cmd_query "$@" ;;
        psql)     cmd_psql "$@" ;;
        logs)     cmd_logs "$@" ;;
        *)        usage >&2; die "unknown command: $cmd" ;;
    esac
}

main "$@"
