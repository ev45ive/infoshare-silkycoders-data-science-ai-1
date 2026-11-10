-- Schemat stanu usługi BC-09. Wykonywany rolą bc09_state_owner (właściciel); rola usługi bc09_svc dostaje tylko DML.
CREATE SCHEMA IF NOT EXISTS svc;

CREATE TABLE IF NOT EXISTS svc.users (
  user_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username      text NOT NULL UNIQUE CHECK (length(username) BETWEEN 3 AND 64),
  password_hash text NOT NULL,
  role          text NOT NULL CHECK (role IN ('requester', 'approver')),
  active        boolean NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS svc.threads (
  thread_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),   -- UUID: nie do zgadnięcia; własność i tak sprawdzana przy każdym odwołaniu
  owner_id   uuid NOT NULL REFERENCES svc.users(user_id),
  title      text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS threads_owner_idx ON svc.threads(owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS svc.messages (
  message_id bigserial PRIMARY KEY,
  thread_id  uuid NOT NULL REFERENCES svc.threads(thread_id) ON DELETE CASCADE,
  role       text NOT NULL CHECK (role IN ('user', 'assistant')),
  content    text NOT NULL,
  trace      jsonb,
  tokens     integer,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS svc.tasks (
  task_id      bigserial PRIMARY KEY,
  thread_id    uuid NOT NULL REFERENCES svc.threads(thread_id) ON DELETE CASCADE,
  requester_id uuid NOT NULL REFERENCES svc.users(user_id),
  idem_key     text NOT NULL UNIQUE,                       -- deterministyczny klucz: ponowne wykonanie węzła nie tworzy drugiego szkicu
  title        text NOT NULL CHECK (length(title) <= 200),
  description  text NOT NULL CHECK (length(description) <= 2000),
  owner        text NOT NULL CHECK (length(owner) <= 100),
  status       text NOT NULL DEFAULT 'szkic' CHECK (status IN ('szkic', 'oczekuje', 'zatwierdzone', 'odrzucone', 'wygasle')),
  approver_id  uuid REFERENCES svc.users(user_id),
  decided_at   timestamptz,
  edited       boolean NOT NULL DEFAULT false,
  expires_at   timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT four_eyes CHECK (approver_id IS NULL OR approver_id <> requester_id),            -- reguła czterech oczu także w bazie
  CONSTRAINT decided_has_approver CHECK (status NOT IN ('zatwierdzone', 'odrzucone') OR approver_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS tasks_status_idx ON svc.tasks(status, expires_at);

CREATE TABLE IF NOT EXISTS svc.audit_log (
  audit_id  bigserial PRIMARY KEY,
  at        timestamptz NOT NULL DEFAULT now(),
  actor_id  uuid,
  action    text NOT NULL,
  thread_id uuid,
  task_id   bigint,
  detail    jsonb
);
CREATE INDEX IF NOT EXISTS audit_actor_idx ON svc.audit_log(actor_id, at DESC);

CREATE TABLE IF NOT EXISTS svc.usage_daily (
  user_id uuid NOT NULL REFERENCES svc.users(user_id),
  day     date NOT NULL,
  tokens  bigint NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day)
);

-- Rola usługi: tylko DML w schemacie svc (w tym tabele punktów kontrolnych LangGraph, tworzone rolą właściciela), bez CREATE.
GRANT USAGE ON SCHEMA svc TO bc09_svc;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA svc TO bc09_svc;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA svc TO bc09_svc;
ALTER DEFAULT PRIVILEGES IN SCHEMA svc GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bc09_svc;
ALTER DEFAULT PRIVILEGES IN SCHEMA svc GRANT USAGE, SELECT ON SEQUENCES TO bc09_svc;
