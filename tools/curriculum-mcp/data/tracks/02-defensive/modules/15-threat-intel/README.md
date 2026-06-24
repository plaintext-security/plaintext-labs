# Module 15 — Threat Intelligence

*Type 7 · Build-&-Operate — ingest real indicator feeds into a threat-intel platform (MISP), enrich an indicator and a detection with context, and judge what is worth acting on; you commit a running intel pipeline with aging and confidence applied. (Secondary: Misconception Reveal — intelligence is assessment, not collection.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Defensive Operations** — *context turns an indicator into a decision; CTI is how you get it.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
An IP in a log means nothing until you know it's a known C2 node. When Mandiant disclosed the
SolarWinds/SUNBURST supply-chain compromise in December 2020 — a trojanised Orion update that
backdoored thousands of organisations — they didn't just publish a report; they pushed YARA rules,
Snort signatures, and IOCs to a public GitHub repo so every defender could immediately hunt for the
SUNBURST DLL and its C2 in their own telemetry. That hand-off — *here are the indicators, go look* —
is threat intelligence doing its job. Threat intelligence — managing indicators, enriching them with
context, and sharing them — is what lets a SOC prioritise and a detection stay current. MISP is the
open standard for storing and sharing CTI, and real, free indicator feeds (abuse.ch, CISA) let you
work with genuine threat data.

## Objective
Ingest real indicator feeds into a threat-intel platform, enrich an indicator and a detection with
context, and understand what intelligence is worth acting on.

## The core idea
An IP in a log is *data*; "that IP is a known Cobalt Strike C2 node seen hitting your sector this
week" is *intelligence*. The difference — context and assessment layered onto a raw indicator — is
what lets a SOC prioritise and keeps detections current. CTI is the practice of collecting indicators,
enriching them into decisions, and sharing them so the whole community isn't independently
rediscovering the same attacker. MISP is the open standard for storing and exchanging it; abuse.ch and
CISA give you real, free, high-quality feeds to work with genuine threat data rather than toy IOCs.

The recurring **Pyramid of Pain** pays off again here: not all indicators are equal. Hashes and IPs
are cheap for an attacker to change — so they age fast and false-positive — while TTPs are expensive.
Good intel programmes weight toward the durable, behavioural end, which is exactly why *intelligence*
beats a firehose of IOCs. STIX/TAXII are the format and transport that make all this machine-readable
and shareable at scale.

The judgment: intelligence is **assessment, not collection** — the hard part is confidence and aging,
not ingest. A stale indicator (the C2 box got cleaned up and is now a shared CDN) manufactures false
positives; an over-trusted feed quietly poisons your detections. A model summarises a threat report
into structured IOCs quickly, but it will hallucinate an attribution or over-trust a dead indicator —
verify against the source and judge confidence yourself. Garbage intel, automated, is worse than none.

## Learn (~4 hrs)

**The platform & feeds**
- [How to Use Threat Intelligence Feeds With MISP (video)](https://www.youtube.com/watch?v=tu86szd5jYU) — ingesting and using real feeds.
- [MISP Project](https://www.misp-project.org/) and its [documentation](https://www.misp-project.org/documentation/) — events, attributes, feeds, and sharing.

**Real feeds**
- [abuse.ch](https://abuse.ch/) (URLhaus, ThreatFox, MalwareBazaar) — free, real, high-quality indicator feeds you can ingest.

**Intelligence in action**
- [Highly Evasive Attacker Leverages SolarWinds Supply Chain... (Mandiant/FireEye)](https://cloud.google.com/blog/topics/threat-intelligence/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor/) — the original SUNBURST disclosure; note how the report pairs the analysis with published detection signatures and IOCs — intelligence shared so defenders can act, not just read.

## Key concepts
- Indicators (IOCs) vs intelligence (context + assessment)
- The Pyramid of Pain (which indicators actually cost the attacker)
- STIX/TAXII and sharing standards
- Enrichment: turning an IOC into a decision
- Feed quality, aging, and false positives

## AI acceleration
A model summarises a threat report into structured indicators quickly — useful for ingest. But it'll
hallucinate an attribution or over-trust a stale indicator; intelligence is about *assessment*, not
just collection. Verify indicators against the source and judge confidence yourself.
