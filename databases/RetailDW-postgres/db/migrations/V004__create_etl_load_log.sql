-- Audit trail: one row per run of an etl.load_* procedure.
CREATE TABLE etl.load_log (
    load_id       integer       GENERATED ALWAYS AS IDENTITY,
    package_name  varchar(100)  NOT NULL,
    started_at    timestamptz(3) NOT NULL DEFAULT now(),
    finished_at   timestamptz(3),
    status        varchar(20)   NOT NULL DEFAULT 'RUNNING',
    rows_read     integer,
    rows_loaded   integer,
    rows_rejected integer,
    error_message text,
    CONSTRAINT pk_load_log PRIMARY KEY (load_id),
    CONSTRAINT ck_load_log_status CHECK (status IN ('RUNNING', 'SUCCEEDED', 'FAILED'))
);
