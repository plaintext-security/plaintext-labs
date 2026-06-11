-- Seed data for the Postgres instance Vault mints dynamic credentials against.
-- Runs once at first container start (docker-entrypoint-initdb.d).
CREATE TABLE IF NOT EXISTS payments (
    id          SERIAL PRIMARY KEY,
    account_id  TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO payments (account_id, amount) VALUES
    ('ACC-001', 100.00),
    ('ACC-002', 250.50),
    ('ACC-003', 999.99);

-- A dynamic role minted by Vault needs to read this table. Vault's role
-- creation_statements GRANT SELECT on it; ensure future tables are covered too.
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO PUBLIC;
