# Module 17 — Reporting & Remediation

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *the report is the product; a shell nobody can act on is worthless.*

## Why this matters
Clients and defenders don't buy shells — they buy a clear, prioritised, reproducible account of
what's wrong and how to fix it. Reporting is the single most career-defining offensive skill: it
separates a "tool runner" from a professional, and it's the deliverable that gets you hired and
re-hired. This module turns everything you found across the track into a report a defender can
act on.

## Objective
Write a professional penetration-test report — executive summary, technical findings with risk
ratings and evidence, and prioritised remediation — modeled on real public reports.

## The core idea
The uncomfortable truth that separates a professional from a tool-runner: **nobody buys shells — they
buy the report.** A client or a defender pays for a clear, prioritised, reproducible account of what's
wrong and how to fix it. A brilliant exploit that produces a finding the defender can't understand,
reproduce, or act on is worth nothing. This is the single most career-defining offensive skill and the
deliverable that gets you re-hired — which is why the track *ends* here, turning everything you found
into something actionable.

The mental model is audience-driven: the same engagement is told twice. The **executive summary**
answers "how exposed are we, in business terms, and what do we do Monday?" — no jargon, just risk and
money. The **technical findings** answer "exactly what, where, proven how, fixed how?" — each with a
clear title, evidence, reproduction steps, impact, and a risk rating that blends CVSS with *business*
context (the KEV/EPSS prioritisation from module 03, applied to *this* client's reality). A finding you
can't reproduce is not a finding.

The judgment, and the sharpest AI line in the whole track: reporting is where AI shines *and* is most
dangerous. A model drafts clean report prose from your notes in seconds — a real time-saver — but it
will smooth over a finding you can't actually reproduce, or invent an impact that merely sounds right.
AI authors the prose; you verify every finding, every number, every CVE. **You sign it; you own it** —
your name is on a document the client makes real decisions from.

## Learn (~4 hrs)

**The standard & real examples**
- [PTES — Reporting](http://www.pentest-standard.org/index.php/Reporting) — the structure a professional report follows.
- [Public Pentesting Reports (curated collection)](https://github.com/juliocesarfort/public-pentesting-reports) — read two or three *real* reports from reputable firms to model tone, structure, and risk framing.

**Tooling**
- [Ghostwriter (GhostManager)](https://github.com/GhostManager/Ghostwriter) — open-source reporting / engagement management; optional, but see how teams operationalise it.

## Key concepts
- Audience: executive summary vs technical detail
- Findings: clear title, evidence, reproduction, impact, risk rating (CVSS + business context)
- Prioritisation by real risk (callback to KEV/EPSS, module 03)
- Actionable remediation a defender can actually implement
- Reproducibility — a finding that can't be reproduced isn't one

## AI acceleration
This is where AI shines *and* where it's most dangerous: a model drafts clean report prose from
your notes in seconds — but it will also smooth over a finding you can't reproduce or invent an
impact. AI authors the prose; you verify every finding, number, and CVE. You sign it; you own it.
