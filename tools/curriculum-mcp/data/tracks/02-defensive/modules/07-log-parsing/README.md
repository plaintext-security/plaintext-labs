# Module 07 — Log Parsing & Normalisation

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *raw logs are chaos; a common schema is what makes detection scale.*

## Why this matters
Every source logs differently — Apache, sshd, Sysmon, and a firewall each describe a "source IP" in
their own way. Until logs are *parsed* into fields and *normalised* to a common schema, you can't
write one detection that works across sources, or correlate them. Normalisation (e.g. to the Elastic
Common Schema) is the unglamorous plumbing that makes everything downstream possible — and it's
exactly where AI both helps most and breaks things silently.

## Objective
Parse a real, messy log into structured fields and normalise it to a common schema, handling the
malformed lines.

## The core idea
This is the plumbing that makes everything else possible, and it's invisible until it breaks. Every
source describes the world differently — Apache, sshd, Sysmon, and a firewall each have their own
name and format for something as basic as "source IP." Until you **parse** raw text into typed fields
and **normalise** those fields to a common schema (like the Elastic Common Schema), you cannot write
one detection that works across sources, and you cannot correlate them: a "suspicious source IP" rule
would need rewriting for every vendor. Normalisation is what lets one rule mean the same thing
everywhere.

The mental model is two steps: *parse* (unstructured text → fields, via grok/regex/VRL), then
*normalise* (rename those fields into a shared vocabulary). For the network engineer it's the exact
reason you map every vendor's syslog into a common field set before building one dashboard across a
mixed fleet — the detection logic should never have to care which box emitted the line.

This module exists because parsing is **AI's home turf *and* where it fails most silently.** A model
writes a grok or VRL parser for an unfamiliar format in seconds — genuinely useful. But a parser that
drops 5% of lines, mislabels a field, or mangles a timestamp looks completely fine until a detection
quietly misses the one event that mattered. The single discipline that saves you: always check the
*parse rate* and the actual field values against the raw log. A green pipeline is not a correct
pipeline — the same lesson as module 01, one layer down.

## Learn (~4 hrs)

**Pipelines**
- [Vector documentation](https://vector.dev/docs/) — a modern, fast log pipeline; read the "Quickstart" and the VRL (transform language) intro.
- [Elastic Common Schema (ECS)](https://www.elastic.co/docs/reference/ecs) — the normalisation target: a shared field set so detections work across sources.

**What good logs contain**
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) — what parseable, useful logs should include.

## Key concepts
- Parsing: unstructured text → fields (grok / regex / VRL)
- Normalisation to a common schema (ECS)
- Enrichment (geoIP, asset/user context)
- Handling malformed / multiline logs
- Why normalisation makes one detection work across many sources

## AI acceleration
This is AI's home turf — a model writes a grok/VRL parser for an unfamiliar format in seconds. It's
also where it fails *silently*: a parser that drops 5% of lines or mislabels a field looks fine until
a detection misses. Always check the parse rate and the field values against the raw log.
