# Lab 05 — Endpoint Telemetry & EDR

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/05-endpoint-telemetry
make up        # build the container with osquery daemon running
make demo      # run the five security-focused queries, show output
make shell     # drop into the container for interactive osqueryi
make down      # stop when done
```

> Everything runs locally in a container you own. No external targets.

## Scenario

Meridian Financial suspects that a compromised developer workstation may have been used for
lateral movement after a phishing email. You have access to the host via the osquery daemon.
Your job: query the host's telemetry to understand the current state — what is running, what
has network connections, who has scheduled tasks, and what SUID binaries exist — and write a
detection query for the persistence technique the threat model identified.

## Do

1. [ ] `make demo` to see the five pre-built security queries run. For each query, note:
   what it finds, which ATT&CK technique it would surface, and whether any result looks
   suspicious in the sample container.

2. [ ] `make shell` then launch `osqueryi`:
   ```bash
   osqueryi
   ```
   Run these queries manually and inspect the output:
   ```sql
   SELECT pid, name, path, cmdline, parent FROM processes;
   SELECT pid, local_address, remote_address, remote_port FROM process_open_sockets;
   SELECT command, path FROM cron_tabs;
   SELECT username, uid, gid, shell FROM users WHERE shell NOT LIKE '%nologin%';
   ```
   For each: what does the result tell you about this host's security state?

3. [ ] Write a new query that finds all processes with an active outbound connection to a
   remote port > 1024 (possible C2 beaconing). Use a JOIN between `processes` and
   `process_open_sockets`. Save it in `data/queries.sql` alongside the existing five queries.

4. [ ] Use the `file` table to find SUID binaries:
   ```sql
   SELECT path, permissions, uid FROM file
   WHERE path LIKE '/usr/%'
   AND permissions LIKE '%s%';
   ```
   List what you find. Are any unexpected for a hardened server?

5. [ ] Review `data/queries.sql` — the pre-built pack. Convert it to an osquery scheduled
   pack JSON format (the `schedule` key in `osquery.conf`). The format is:
   ```json
   {"schedule": {"query_name": {"query": "SELECT ...", "interval": 300}}}
   ```
   Write a `pack.json` that runs all five queries every 5 minutes.

## Success criteria — you're done when

- [ ] You ran all five pre-built queries and noted what each detects.
- [ ] You wrote a C2-detection query using a JOIN and saved it to `queries.sql`.
- [ ] You identified SUID binaries with the `file` table.
- [ ] You produced a `pack.json` that schedules all queries at 5-minute intervals.

## Deliverables

`queries.sql` (all six queries with a comment above each explaining what ATT&CK technique it
detects) + `pack.json` (the osquery scheduled pack). Commit both.

## Automate & own it

**Required.** Write a Python script `run-queries.py` that connects to the osquery daemon socket
(`/var/osquery/osquery.em` or via `osquery.thrift`), runs each query from `queries.sql`, and
writes the results as JSONL to stdout (one line per query result row). Have an AI draft the
socket client code; you verify the output format is valid JSONL before committing. This is the
pipeline that feeds a SIEM.

## AI acceleration

Tell an AI: "Write an osquery SQL query that detects a process running from a /tmp directory
with an outbound network connection, mapped to ATT&CK T1059 (Command and Scripting
Interpreter)." Check the table and column names by running `osqueryi` with `.tables` and `.schema <table>` commands,
run it in `osqueryi`, and confirm it produces the expected result. The model is good at the
SQL shape; the schema validation and test run are yours.

## Connects forward

The osquery queries you write here become the data source for module 10 (detecting host
compromise) — where Wazuh ingests osquery pack results as real-time telemetry and fires
alerts on suspicious query output. Module 08 (patch and vulnerability management) also uses
osquery to enumerate installed packages and versions.

## Marketable proof

> "I deployed osquery, wrote security-focused detection queries mapped to ATT&CK techniques,
> and packaged them as a scheduled pack that feeds a SIEM pipeline."

## Stretch

- Install and configure the Wazuh agent alongside osquery in the container (use the `make shell`
  environment), point the osquery pack output to Wazuh's log collector, and confirm a query
  result appears in the Wazuh manager's alert stream.
- Use osquery's `differential` mode: run a query, make a change (add a user, create a cron job),
  run again, and observe that only the delta is reported. This is how continuous monitoring
  catches changes rather than emitting the full state every interval.
