-- Airflow metadata database and the write role for forecast.* results.
-- Run after migrate (needs schema forecast). Password is passed as psql variable airflow_password via stdin.
\set ON_ERROR_STOP on

SELECT format('CREATE ROLE airflow LOGIN PASSWORD %L', :'airflow_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'airflow') \gexec
SELECT format('ALTER ROLE airflow LOGIN PASSWORD %L', :'airflow_password') \gexec

SELECT 'CREATE DATABASE airflow OWNER airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow') \gexec

\connect retaildw

GRANT CONNECT ON DATABASE retaildw TO airflow;
GRANT USAGE ON SCHEMA forecast TO airflow;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA forecast TO airflow;
ALTER DEFAULT PRIVILEGES FOR ROLE retaildw IN SCHEMA forecast
    GRANT SELECT, INSERT, UPDATE ON TABLES TO airflow;
