#!/usr/bin/env bash
# Configure Vault's DATABASE secrets engine so it mints short-TTL, per-request
# Postgres credentials — the "operate" upgrade over a static stored password.
# Runs in the lab container (VAULT_ADDR / VAULT_TOKEN come from the environment).
set -euo pipefail

echo "== Enabling the database secrets engine =="
vault secrets enable -path=database database 2>/dev/null || echo "  (already enabled)"

echo "== Pointing Vault at Postgres (Vault holds the admin cred, apps never do) =="
vault write database/config/meridian-postgres \
    plugin_name=postgresql-database-plugin \
    allowed_roles="app-role" \
    connection_url="postgresql://{{username}}:{{password}}@db:5432/meridian?sslmode=disable" \
    username="vaultadmin" \
    password="vaultadminpass"

echo "== Creating a role that mints 5-minute, read-only DB users on demand =="
vault write database/roles/app-role \
    db_name=meridian-postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    revocation_statements="DROP ROLE IF EXISTS \"{{name}}\";" \
    default_ttl="5m" \
    max_ttl="1h"

echo "== Done. 'vault read database/creds/app-role' now mints a unique, expiring login. =="
