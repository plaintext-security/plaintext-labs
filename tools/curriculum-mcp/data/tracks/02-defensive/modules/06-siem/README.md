# Module 06 — SIEM Fundamentals

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *where all your telemetry meets: search, correlate, alert.*

## Why this matters
Telemetry scattered across hosts and sensors is useless until it's centralised, correlated, and
alertable. A SIEM is the analyst's workbench — it ingests everything (modules 01–05), lets you search
and pivot across sources, correlates events into alerts, and drives the SOC workflow. Wazuh gives you
a complete open-source SIEM/XDR to learn on for free.

## Objective
Stand up an open-source SIEM, ingest real security telemetry, and build a correlation rule and a
dashboard that surface an attack.

## The core idea
Every prior module produced a stream of telemetry sitting in its own silo. The **SIEM** is where they
converge into one searchable, correlatable place — and, more than a store, it's the analyst's
*workbench* and the engine of the SOC workflow: ingest → parse → index → search → alert → triage. The
leap beyond a log store is **correlation**: turning many low-value events into one high-value alert.
Fifty failed logons across the fleet from one source, then a success, is an alert; each individual
logon is noise. The SIEM is where "events" become "a story."

The practitioner reality is that a SIEM is less a product than a workflow. The query language differs
by vendor (SPL, KQL, Lucene) and you learn whichever your shop runs — but the durable skill is
knowing *what behaviour is worth alerting on* and expressing it so it fires on the real thing without
burying the analyst. Wazuh gives you a complete open-source SIEM/XDR — decoders, rules, dashboards,
alerting — to learn the whole loop for free, no licence.

The defining failure mode, and the thing that separates a working SOC from a dashboard nobody reads:
**alert fatigue.** A SIEM that fires 500 alerts a day is functionally *off* — analysts triage it by
ignoring it. Every rule you add is a claim on someone's finite attention, so tuning and
prioritisation aren't housekeeping, they're the job. Test every correlation rule against data where
you already know the answer before it earns a place in the pipeline.

## Learn (~4 hrs)

**The platform**
- [Wazuh Practical Training for Beginners (video)](https://www.youtube.com/watch?v=UGYmG_hy3qQ) — install and use an open-source SIEM from scratch.
- [Wazuh documentation](https://documentation.wazuh.com/current/index.html) — read "Getting Started" and the ruleset/decoders overview.

**What to surface**
- [MITRE ATT&CK](https://attack.mitre.org/) — the behaviours your correlation rules should turn into alerts.

## Key concepts
- Ingest → parse → index → search → alert
- Correlation: turning many events into one alert
- Dashboards and the analyst workflow
- SIEM rules/decoders (Wazuh) vs raw queries (Elastic)
- Alert fatigue and why tuning matters

## AI acceleration
A model writes SIEM queries and correlation logic fast — and a generated rule with subtly wrong logic
ships confident false alerts or, worse, silently misses the real one. Test every rule against data
where you know the answer.
