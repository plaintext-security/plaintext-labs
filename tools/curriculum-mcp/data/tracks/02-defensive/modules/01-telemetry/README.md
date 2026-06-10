# Module 01 — Telemetry & Log Centralisation

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *you can't detect what you don't collect; this is the data plane everything else runs on.*

## Why this matters
Detection, hunting, and response all start with data. Before you can write a single detection you
need the right telemetry — host, network, identity — shipped reliably into one searchable place.
Getting collection right (and complete) is the unglamorous foundation that decides whether you can
see an attacker at all. This module builds that pipeline.

## Objective
Stand up a central log store, ship real log data into it, and reason about what telemetry actually
matters for detection.

## The core idea
Detection is a data problem before it's a logic problem. Every detection, every hunt, every
investigation is ultimately a *query* — and a query can only return what you collected. So the
first question of a SOC isn't "what rules do we have," it's "what can we actually see?" — and the
honest answer is almost always *less than you think*. Anyone who has run firewalls knows the shape
of this: logging "permit/deny" is not the same as logging the session, and you cannot investigate
what you never recorded — telemetry can't be turned on retroactively after the incident starts.

The architecture is the same three moves regardless of vendor: a shipper/agent on the source
(fluent-bit, Vector, Beats) → a transport → a central, indexed store you can search
(Elasticsearch/OpenSearch, Splunk, Loki). The product is interchangeable; the actual skill is
deciding *what is worth shipping*. This is where ATT&CK Data Sources earns its keep: rather than
"collect everything" — which bankrupts you on storage and buries the signal — you work backward
from the techniques you care about to the minimum telemetry that reveals them.

The gotcha that bites everyone: a pipeline that *runs* is not a pipeline that *works*. Configs
silently drop fields, mangle timestamps (so events sort wrong and correlation quietly breaks), or
parse the wrong format — and you discover it mid-incident, when the field you need is null. Treat
timestamps and field mappings as first-class, verify what actually lands in the index against what
the source emitted, and accept that retention vs. volume vs. cost is a *security* decision, not just
an ops one.

## Learn (~4 hrs)

**The data plane**
- [Elastic Stack — Create a Free SIEM (video, part 1)](https://www.youtube.com/watch?v=GvzosoaOaIQ) — a hands-on build of Elasticsearch + Kibana as a SIEM.
- [Elastic — Elasticsearch & Kibana docs](https://www.elastic.co/guide/index.html) — the reference; read the "Getting Started" for ingest, index, and search.

**What to collect**
- [MITRE ATT&CK — Data Sources](https://attack.mitre.org/datasources/) — what telemetry maps to which techniques, so you collect with detection in mind.

## Key concepts
- Log sources: host, network, identity, cloud
- Shippers/agents (fluent-bit, vector, beats)
- Centralisation and indexing
- What "good" telemetry looks like — and the gaps that blind you
- Retention and volume tradeoffs

## AI acceleration
A model drafts your shipper config and an ingest pipeline in seconds — and just as easily produces
one that silently drops fields or mis-parses timestamps. Verify what actually lands in the index,
not what the config claims.
