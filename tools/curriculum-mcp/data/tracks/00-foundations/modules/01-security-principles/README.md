# Module 01 — Security First Principles

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *the vocabulary and mental models the whole field is built on.*

## Why this matters
Before tools, before tracks, you need the shared language: what security is actually trying
to achieve, who the players are, and the handful of principles every later decision traces
back to. This is the lens you'll carry into all twelve tracks — when you harden a host or
write a detection, you're applying these ideas whether you name them or not.

## Objective
Explain the core security models — CIA, AAA, defense in depth, least privilege — and use
them to reason about a real system's risks.

## The core idea
These "principles" read like vocabulary to memorise, but the point is that they're a **lens you reason
with**, not terms you recite. The **CIA triad** is the *what are we protecting*: confidentiality (who
can read it), integrity (can it be trusted/unaltered), availability (can you use it when you need it) —
and very nearly every attack and defense maps to degrading or protecting one of those three. **AAA** is
the *how we control access*: authentication (who are you), authorization (what may you do), accounting
(what did you do). Getting authn vs. authz straight is not pedantry — a huge share of real-world bugs
(the broken access control you'll meet in the offensive track) is an authorization failure wearing a
successful authentication as a disguise.

Two principles actually drive design decisions. **Defense in depth**: trust no single control; layer
them so one failure isn't fatal — the same instinct as "don't rely on the perimeter firewall alone."
**Least privilege**: give every user, process, and key the minimum access it needs, so a compromise is
*contained* rather than total. And the framing that makes risk usable — risk ≈ threat × vulnerability ×
impact — is why you never "fix everything": you fix what's both exploitable and impactful (the
prioritisation instinct the offensive vuln module formalises as KEV/EPSS).

The through-line for the whole curriculum: the attacker and defender mindsets are the *same knowledge
pointed in opposite directions* — offense informs defense — which is exactly why we teach both. Use a
model as a Socratic tutor (have it quiz you on authn vs. authz, or whether a control protects
confidentiality or integrity), but first principles is precisely where a confident wrong answer slips
by — check it against NIST.

## Learn (~2 hrs)

**The concepts**
- [Professor Messer — The CIA Triad (Security+ SY0-701, ~8 min)](https://www.youtube.com/watch?v=SBcDGb9l6yo) — a crisp, free explainer of the core triad; follow it with his adjacent 1.2 videos on AAA and security controls.
- [NIST SP 800-12 Rev. 1 — An Introduction to Information Security](https://csrc.nist.gov/pubs/sp/800/12/r1/final) — the authoritative grounding; skim chapters 1–3.

**The practical baseline**
- [CISA — Cybersecurity Best Practices](https://www.cisa.gov/topics/cybersecurity-best-practices) — what the principles look like as real-world defaults.

## Key concepts
- The CIA triad — confidentiality, integrity, availability
- AAA — authentication, authorization, accounting
- Defense in depth and least privilege
- Risk = threat × vulnerability × impact
- The attacker vs defender mindset (offense informs defense)

## AI acceleration
Use a model as a Socratic tutor — have it quiz you on authentication vs authorization, or
whether a control protects confidentiality or integrity. Then check its claims against NIST;
first principles is exactly where a confident wrong answer slips by.
