# Module 12 — Threat Modeling

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *judgment before tools: what are we protecting, from whom, and where can it go wrong?*

## Why this matters
Tools come later; judgment comes first. The durable ideas — CIA, authentication vs
authorization, defense in depth — and the habit of threat modeling are what turn a pile of
techniques into security thinking. Every later track is an answer to a threat; this module
teaches you to ask the question first, so you attack and defend on purpose rather than by
reflex.

## Objective
Frame a system in terms of assets, trust boundaries, and threats, and produce a STRIDE
threat model with mitigations.

## The core idea
This is the module that turns a pile of techniques into *security thinking* — judgment before tools.
Threat modeling is just four questions asked in order: what are we building, what can go wrong, what
are we doing about it, did we do a good job? The mental shift is from reflex ("scan it, patch it") to
*intent*: reason about what you're protecting (assets), where trust changes hands (**trust
boundaries** — the moments data crosses from less-trusted to more-trusted are where most bugs live),
and what an attacker actually wants. Every later track is an *answer* to a threat; this module teaches
you to ask the question first, so you attack and defend on purpose rather than by reflex.

**STRIDE** is the lens that makes "what can go wrong" systematic instead of vibes — Spoofing,
Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege — walked
against each trust boundary. And it maps cleanly back to the first-principles module
(spoofing↔authentication, tampering↔integrity, information disclosure↔confidentiality, EoP↔authorization),
which is the whole point: the principles and the method are the same idea, one stated and one applied.

The judgment: a model is a strong brainstorming partner — feed it a data-flow description and it
enumerates plausible STRIDE threats fast. But the skill is **pruning**: discard the irrelevant, add the
context-specific threats it can't know (your business logic, your real trust boundaries), and own the
final model. An unpruned threat list is just noise; judgment is what turns it into a model.

## Learn (~3 hrs)

**The mindset**
- [The Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/) — the four questions and the values, in two pages; foundational.
- [Adam Shostack — Threat Modeling resources & the 4-Question Framework](https://shostack.org/resources/threat-modeling) — from the person who wrote the book; practical and free.

**STRIDE, hands-on**
- [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) — a working method you can apply today.
- [Elevation of Privilege (free card game)](https://shostack.org/games/elevation-of-privilege) — learn STRIDE by playing it against a design; genuinely the fastest way it clicks.

**Reference**
- [Microsoft — STRIDE threat categories](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats) — a clean catalog to map against.

## Key concepts
- The CIA triad and AAA (authentication, authorization, accounting)
- Trust boundaries and data-flow thinking
- STRIDE as a threat-enumeration lens
- Attack surface and attacker goals
- Defense in depth and least privilege

## AI acceleration
A model is a strong brainstorming partner — feed it a data-flow description and it
enumerates plausible STRIDE threats fast. The skill is *pruning*: discard the irrelevant,
add the context-specific threats it can't know, and own the final model.
