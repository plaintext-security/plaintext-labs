# Module 15 — Threat Intelligence

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *context turns an indicator into a decision; CTI is how you get it.*

## Why this matters
An IP in a log means nothing until you know it's a known C2 node. Threat intelligence — managing
indicators, enriching them with context, and sharing them — is what lets a SOC prioritise and a
detection stay current. MISP is the open standard for storing and sharing CTI, and real, free
indicator feeds (abuse.ch, CISA) let you work with genuine threat data.

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
