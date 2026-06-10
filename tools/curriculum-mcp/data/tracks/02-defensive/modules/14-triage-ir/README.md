# Module 14 — Alert Triage & Incident Response

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *an alert is a question; triage and IR are how you answer it without panic.*

## Why this matters
Detections fire; now what? A SOC lives or dies on a repeatable process: triage the alert (real or
noise?), and when it's real, run a disciplined incident response — contain, eradicate, recover,
learn — without missing steps under pressure. The NIST lifecycle is the backbone, and TheHive gives
you a free, real case-management platform to run it in.

## Objective
Triage a real alert through a structured process, and run a lab incident end to end (NIST lifecycle)
in a case-management platform, to a documented verdict.

## The core idea
An alert is a question, not a verdict: "is this real, and if so, how bad?" **Triage** is the fast
filter — true/false positive, severity, scope — and **incident response** is what you run when triage
says "real": a disciplined sequence so you don't improvise under pressure and skip a step that matters.
The backbone is the **NIST lifecycle** (prep → detection/analysis → containment/eradication/recovery →
post-incident), the same shape as SANS's PICERL mnemonic. The order isn't bureaucracy — it exists so
that mid-crisis you contain *before* you eradicate, and you actually capture the lesson *after*.

The point of a process is precisely that it holds when you're stressed and the clock is running. The
classic failures here are emotional, not technical: eradicating before you understand scope (so the
attacker simply walks back in), or containing so abruptly that you destroy the evidence you needed to
answer "how did they get in?" A case-management platform like TheHive exists to externalise the
discipline — observables, timeline, and verdict in one place, so nothing critical lives only in one
analyst's head.

The judgment: the most undervalued phase is the **post-incident review** — it's where an incident
turns into a new detection, a hardening change, or a hunt, which is the only way a SOC gets better
instead of just busier. A model drafts timelines and summaries from your notes fast (a genuine
time-saver under pressure), but it will state a conclusion your evidence doesn't support, and in IR a
wrong verdict has consequences. AI drafts the narrative; you verify every step against the evidence
and own the call.

## Learn (~4 hrs)

**The process & platform**
- [How to: TheHive — a free, open-source incident response platform (video)](https://www.youtube.com/watch?v=cuR8qIfV11k) — case management for IR.
- [TheHive documentation](https://docs.strangebee.com/thehive/) — alerts, cases, observables, and the analyst workflow.

**The method**
- [NIST SP 800-61r2 — Computer Security Incident Handling Guide](https://csrc.nist.gov/pubs/sp/800/61/r2/final) — the IR lifecycle; read the phases (prep, detection/analysis, containment/eradication/recovery, post-incident).

## Key concepts
- Triage: alert → true/false positive → severity
- The NIST IR lifecycle (and SANS PICERL)
- Cases, observables, and timelines
- Containment vs eradication vs recovery
- The post-incident review (where the learning is)

## AI acceleration
A model drafts incident timelines and summaries from your notes fast — a real time-saver under
pressure. But it'll also state a conclusion your evidence doesn't support; in IR a wrong verdict has
consequences. AI drafts the narrative; you verify every step against the evidence and own the call.
