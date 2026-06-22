#!/usr/bin/env python3
"""A minimal 'app' that holds NO static database secret.

At startup it asks Vault for a *dynamic* Postgres credential (minted on demand,
auto-expiring), connects with it, runs one query, and prints the ephemeral
username — proving the credential lives for minutes and was never committed,
env-var'd, or baked into the image. This is the runtime-fetch pattern that
replaces "paste the password in config.py".

Run inside the lab container:  python3 data/app_runtime.py
"""
import os
import sys

import hvac
import psycopg2


def main() -> int:
    vault = hvac.Client(
        url=os.environ["VAULT_ADDR"],
        token=os.environ["VAULT_TOKEN"],
    )
    if not vault.is_authenticated():
        print("ERROR: could not authenticate to Vault", file=sys.stderr)
        return 1

    # Ask Vault for a fresh, short-lived Postgres credential.
    lease = vault.read("database/creds/app-role")
    creds = lease["data"]
    username, password = creds["username"], creds["password"]
    print(f"[app] Vault minted a dynamic DB user: {username}")
    print(f"[app] lease_id={lease['lease_id']}  ttl={lease['lease_duration']}s "
          f"(it self-destructs when the lease expires)")

    # Connect with the ephemeral credential the app never stored.
    conn = psycopg2.connect(
        host=os.environ.get("PGHOST", "db"),
        dbname=os.environ.get("PGDATABASE", "meridian"),
        user=username,
        password=password,
    )
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM payments;")
        (count,) = cur.fetchone()
    conn.close()
    print(f"[app] queried Postgres as {username}: {count} payment rows.")
    print("[app] No static secret was read from code, env, or disk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
