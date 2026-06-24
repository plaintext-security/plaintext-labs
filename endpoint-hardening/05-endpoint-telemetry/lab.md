# Lab 05 — Endpoint Telemetry & EDR

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/05-endpoint-telemetry
make up        # build the osquery container AND detonate a real ATT&CK technique in it
make demo      # run the security-focused queries, show output (incl. the seeded artifact)
make shell     # drop into the container for interactive osqueryi
make down      # stop when done
```

> Everything runs locally in a container you own. No external targets.

**Real artifact (not a toy).** `make up` runs `make seed`, which detonates the **Atomic Red Team
T1053.003 (Scheduled Task/Job: Cron)** test inside the container — Red Canary's open, ATT&CK-mapped
test library, staged from the shared dataset cache (`data/atomic/T1053.003.{md,yaml}`). The result is
a *genuine, documented* persistence technique live on the host: a payload running from `/tmp`,
invoked by a crontab entry. Your osquery hunt surfaces the real thing, not an invented compromise.

## Scenario

A developer workstation in the organization's fleet has been flagged after a phishing email, and
you have access to the host via the osquery daemon. Unknown to you at the start, an adversary has
already established persistence on it using a **real, in-the-wild technique** — ATT&CK
**T1053.003 (Cron)**, the same scheduled-task/cron persistence catalogued by Red Canary's Atomic Red
Team and used by commodity Linux malware. Your job: query the host's telemetry to understand the
current state — what is running, what has network connections, who has scheduled tasks, and what
SUID binaries exist — find the seeded T1053.003 artifact, and write a detection query for it.

## Do

1. [ ] `make demo` to see the pre-built security queries run, including **Query 5** which
   surfaces the seeded Atomic Red Team T1053.003 cron-persistence artifact. For each query, note:
   what it finds, which ATT&CK technique it surfaces, and which result is the real planted
   compromise. Read `data/atomic/T1053.003.md` for the upstream technique definition.

2. [ ] `make shell` then launch `osqueryi`:
   ```bash
   osqueryi
   ```
   Run these queries manually and inspect the output (note: the cron table is `crontab`, and it
   parses `/etc/cron.d/` and user crontabs):
   ```sql
   SELECT pid, name, path, cmdline FROM processes WHERE path LIKE '/tmp/%';
   SELECT pid, local_address, remote_address, remote_port FROM process_open_sockets;
   SELECT command, path FROM crontab;
   SELECT username, uid, gid, shell FROM users WHERE shell NOT LIKE '%nologin%';
   ```
   For each: what does the result tell you about this host's security state? Confirm you can see
   the T1053.003 payload running from `/tmp` and its `/etc/cron.d/` entry.

3. [ ] Write a new query that finds the persistence the seed planted: a `crontab` row whose
   `command` references a path under `/tmp`. Then write a second query that finds all processes
   with an active outbound connection to a remote port > 1024 (possible C2 beaconing) using a JOIN
   between `processes` and `process_open_sockets`. Save both in `data/queries.sql` alongside the
   existing queries, each with an ATT&CK-technique comment (the cron one is T1053.003).

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

- [ ] You ran the pre-built queries and identified the seeded T1053.003 cron-persistence artifact.
- [ ] You wrote a cron-persistence query (T1053.003) and a C2-detection JOIN query, both saved to `queries.sql`.
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
