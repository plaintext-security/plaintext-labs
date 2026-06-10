# Module 05 — Endpoint Telemetry & EDR

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 07 — Endpoint & Host Hardening]** — *Hardening reduces the attack surface; telemetry tells you when an attacker found the part you missed.*

## Why this matters

A hardened host without telemetry is a vault with no security camera. You've reduced the odds of a breach, but if it happens you'll find out from a third party weeks later. Endpoint telemetry — the structured, continuous collection of process events, network connections, file changes, and authentication activity from each host — is the data layer that turns "we think we're secure" into "we'll know within minutes if something changes." osquery and Wazuh are the two open-source tools most deployed in production for this purpose: osquery for ad-hoc and scheduled SQL-query-based host interrogation, Wazuh for real-time event collection, alerting, and SIEM integration.

## Objective

Run osquery against a Linux host, execute security-focused queries against the process table, network connections, users, and scheduled tasks, and understand the telemetry schema well enough to write a detection query for a specific attack behaviour.

## The core idea

osquery treats the operating system as a relational database. Every aspect of system state — running processes, open files, listening sockets, kernel modules, user accounts, browser history — is a table you query with SQL. This is a genuinely useful abstraction because it makes host interrogation programmable, composable, and auditable in the same language analysts already know. A query that finds all processes with a network connection and no corresponding installed package is a one-line SQL join that would require a bespoke script in any other approach.

The telemetry architecture has two modes. Interactive queries (via `osqueryi`) are the analyst's tool — you connect to the daemon and run ad-hoc queries to investigate a specific host or hypothesis. Scheduled queries (in `osquery.conf` or via osquery's `packs` system) run continuously and log results to a file or a centralized logging service. The scheduled query output is what feeds a SIEM or detection pipeline; the interactive mode is what you use when you're on a host and need to understand its state quickly. Both modes share the same SQL interface.

Wazuh extends the telemetry model from query-based polling to real-time event streaming. The Wazuh agent collects system logs, audit events (via `auditd`), file integrity monitoring (FIM) events, and osquery results, then forwards them to the Wazuh manager for alerting and correlation. The combined osquery + Wazuh stack covers both the "what is the state right now" query use case and the "alert me when something changes" real-time use case. For Meridian Financial's endpoint programme, this means every process creation, privileged command, and configuration change is visible and searchable in near-real-time.

The practitioner discipline in endpoint telemetry is knowing which tables matter for security and which queries produce signal without excessive noise. Process creation queries (`SELECT pid, name, path, cmdline, parent FROM processes`) are universally useful — they reveal what is running and what spawned it. Network connection queries (`SELECT pid, local_address, remote_address, remote_port FROM process_open_sockets`) catch C2 beaconing. Crontab queries (`SELECT command, path FROM cron_tabs`) catch persistence mechanisms. SUID binary queries (`SELECT path, permissions FROM file WHERE ... permissions LIKE '%s%'`) catch the privesc paths module 09 addresses. Each query maps to a specific adversary technique.

## Learn (~4 hrs)

**osquery**
- [osquery documentation — Introduction and SQL queries](https://osquery.readthedocs.io/en/stable/introduction/sql/) — read the Introduction and the SQL section to understand the table model (~30 min).
- [osquery schema reference](https://osquery.readthedocs.io/en/stable/introduction/sql/) — bookmark this; it is the reference for every table and column. Scan the process, socket, and file tables.

**Wazuh**
- [Wazuh documentation — Getting Started](https://documentation.wazuh.com/current/getting-started/index.html) — read the architecture overview and the agent installation section to understand the data flow.
- [Wazuh osquery integration guide](https://osquery.readthedocs.io/en/stable/) — how Wazuh collects osquery results; skim for the configuration pattern.

**EDR concepts**
- [What is an EDR? (CrowdStrike explainer)](https://www.crowdstrike.com/en-us/cybersecurity-101/endpoint-security/endpoint-detection-and-response-edr/) — industry context for what commercial EDRs do that osquery alone doesn't; understand the gap before the stretch section.

## Key concepts

- osquery exposes OS state as SQL tables: processes, sockets, files, users, kernel modules, and more.
- Interactive mode (`osqueryi`) for ad-hoc investigation; scheduled packs for continuous telemetry.
- Key security tables: `processes`, `process_open_sockets`, `cron_tabs`, `sudoers`, `listening_ports`, `file`.
- Wazuh agent collects osquery results, auditd events, and FIM events for real-time alerting.
- Telemetry without alerting is archaeology; alerting without telemetry is guesswork. Both are required.

## AI acceleration

Give an AI a specific attack technique (e.g. "persistence via cron") and ask it to write an osquery SQL query that would detect it. Check the query against the osquery schema to confirm the table and column names are real, then run it against a live host. The model drafts the query; you validate the schema and test the output before treating the result as signal.
