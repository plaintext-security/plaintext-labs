# Module 06 — SIEM Fundamentals

*Type 7 · Build-&-Operate — stand up an open-source SIEM (Wazuh), ingest real security telemetry, and build a correlation rule plus a dashboard that surface an attack; you commit the running SIEM config, rule, and dashboard. (Secondary: Detonate & Detect — test every rule against data where you already know the answer.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Defensive Operations** — *where all your telemetry meets: search, correlate, alert.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
Telemetry scattered across hosts and sensors is useless until it's centralised, correlated, and
alertable. In the 2017 Equifax breach, attackers sat in the network slowly extracting data for **76
days** before anyone noticed — they queried 51 databases and exfiltrated in small increments
specifically to stay under the radar (US GAO, GAO-18-559). The telemetry to catch that almost
certainly existed; what was missing was the centralised correlation and alerting that turns scattered,
low-value events into one high-value "this is exfiltration" alert. A SIEM is the analyst's workbench —
it ingests everything (modules 01–05), lets you search and pivot across sources, correlates events
into alerts, and drives the SOC workflow. Wazuh gives you a complete open-source SIEM/XDR to learn on
for free.

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
- [Data Protection: Actions Taken by Equifax... (US GAO, GAO-18-559)](https://www.gao.gov/products/gao-18-559) — read the Highlights page and "Attackers Exploited Vulnerabilities" section; the 76-day undetected exfiltration is the case for correlation and alerting, not just log storage.

## Key concepts
- Ingest → parse → index → search → alert
- Correlation: turning many events into one alert
- Dashboards and the analyst workflow
- SIEM rules/decoders (Wazuh) vs raw queries (Elastic)
- Alert fatigue and why tuning matters
- Equifax 2017: 76 days of slow exfiltration that correlation should have surfaced

## AI acceleration
A model writes SIEM queries and correlation logic fast — and a generated rule with subtly wrong logic
ships confident false alerts or, worse, silently misses the real one. Test every rule against data
where you know the answer.
