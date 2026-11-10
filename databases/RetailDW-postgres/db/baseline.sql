-- Idempotent environment baseline: roles, database, schemas, migration ledger, grants.
-- Run as superuser "postgres" against database "postgres" (retaildw.sh baseline).
-- Passwords are read from the container environment (compose passes them from .env),
-- so they never appear on a command line or in a .sql file.
\set ON_ERROR_STOP on

\getenv pg_password POSTGRES_PASSWORD
\getenv owner_password RETAILDW_PASSWORD
\getenv ro_password RETAILDW_RO_PASSWORD

SELECT format('CREATE ROLE retaildw LOGIN PASSWORD %L', :'owner_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'retaildw') \gexec
SELECT format('CREATE ROLE retaildw_ro LOGIN PASSWORD %L', :'ro_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'retaildw_ro') \gexec

-- .env is the source of truth: re-sync passwords on every run.
ALTER ROLE postgres PASSWORD :'pg_password';
ALTER ROLE retaildw LOGIN PASSWORD :'owner_password';
ALTER ROLE retaildw_ro LOGIN PASSWORD :'ro_password';

SELECT 'CREATE DATABASE retaildw OWNER retaildw'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'retaildw') \gexec

REVOKE ALL ON DATABASE retaildw FROM PUBLIC;
GRANT CONNECT ON DATABASE retaildw TO retaildw, retaildw_ro;

\connect retaildw

CREATE SCHEMA IF NOT EXISTS src       AUTHORIZATION retaildw;
CREATE SCHEMA IF NOT EXISTS stg       AUTHORIZATION retaildw;
CREATE SCHEMA IF NOT EXISTS etl       AUTHORIZATION retaildw;
CREATE SCHEMA IF NOT EXISTS dw        AUTHORIZATION retaildw;
CREATE SCHEMA IF NOT EXISTS reporting AUTHORIZATION retaildw;
CREATE SCHEMA IF NOT EXISTS ops       AUTHORIZATION retaildw;

SET ROLE retaildw;

CREATE TABLE IF NOT EXISTS ops.schema_migrations (
    filename   text        PRIMARY KEY,
    checksum   text        NOT NULL,
    applied_at timestamptz NOT NULL DEFAULT now()
);

RESET ROLE;

GRANT USAGE ON SCHEMA src, stg, etl, dw, reporting TO retaildw_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA src, stg, etl, dw, reporting TO retaildw_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE retaildw IN SCHEMA src, stg, etl, dw, reporting
    GRANT SELECT ON TABLES TO retaildw_ro;
