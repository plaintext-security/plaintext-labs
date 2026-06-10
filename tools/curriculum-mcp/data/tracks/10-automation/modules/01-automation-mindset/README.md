# Module 01 — The Automation Mindset

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *automate the repeatable so humans can own the judgment.*

## Why this matters
Automation is not about removing people from security — it is about removing people from the
parts of security where humans are slowest and least reliable: repetitive lookups, format
conversions, status checks, and alert routing. The judgment calls — what is an incident,
whether to block a customer's IP, how to communicate a breach — stay with humans. Getting this
boundary right is the first skill in automation; drawing it in the wrong place causes either
human burnout (everything manual) or serious mistakes (everything automated without review).

## Objective
Assess ten real manual security tasks for automation ROI, apply a structured decision framework
to prioritize them, and produce a written automation roadmap — before writing a single line of
code.

## The core idea
Not every manual security task is a good automation candidate. The two criteria that matter most
are **repeatability** (does this exact sequence of steps happen more than a few times a month?)
and **determinism** (given the same inputs, does the right answer always look the same?). A task
that is highly repetitive and highly deterministic — "look up this IP in three threat-intel
feeds and log the result" — is an excellent automation target. A task that is highly repetitive
but requires human judgment on every instance — "is this alert a real incident or a false
positive?" — is an automation-assist target: automate the data gathering, but keep a human in
the decision loop.

The ROI calculation is simple but frequently skipped: how many minutes does this take manually,
times how often it happens per week, minus the maintenance burden of the automation? A script
that saves 30 minutes per week but requires 4 hours of maintenance every time the upstream API
changes is not a net positive. The maintenance burden is systematically underestimated, especially
for automations that call external APIs, parse web pages, or depend on undocumented tool output
formats — all of which change without notice.

Two failure modes define bad automation. **Automation that runs silently without any human
visibility** is the first: it operates, but when it does something wrong nobody notices until
the damage is done. Every automated action should produce a log entry, ideally a human-readable
one that a junior analyst can understand. **Automation without a kill switch** is the second: if
the automation starts behaving unexpectedly, can you stop it in 60 seconds? A playbook that can
be paused by flipping a feature flag is a safe playbook; one that requires a code change and a
deployment to stop is not.

The posture this track builds toward: **AI authors → you review → scanners gate → you own it.**
The automation handles the mechanics; the engineer understands every step and can defend every
decision the automation makes. "I don't know what that script does" is not an acceptable answer
for a security tool running in production.

## Learn (~2 hrs)

**Where automation pays off (~1 hr)**
- [The Security Chaos Engineering Book — O'Reilly (Ch. 1 sample)](https://www.oreilly.com/library/view/security-chaos-engineering/9781492080350/) — the context for why reliability thinking applies to security operations; read the introduction on the cost of manual processes.

**Automation failure modes (~1 hr)**
- [SRE Book — Google — "Toil" chapter](https://sre.google/sre-book/eliminating-toil/) — the SRE definition of "toil" maps perfectly onto security operations; understand the criteria for toil elimination. Free online.
- [NIST SP 800-137A — Assessing Information Security Continuous Monitoring](https://csrc.nist.gov/pubs/sp/800/137/a/final) — skim sections 2 and 3 for the policy framework around automated monitoring; not a how-to, but the regulatory context that shapes what you're allowed to automate.

## Key concepts
- Repeatability + determinism = automation target; judgment calls stay human
- ROI = (time saved × frequency) - maintenance burden — skipping the maintenance term is a mistake
- Silent automation without logs is dangerous automation
- Kill-switch requirement: every automation must be stoppable in 60 seconds
- "AI authors → you review → scanners gate → you own it" — the track posture

## AI acceleration
This is the module where AI's role is analysis, not authoring. Give a model your list of manual
security tasks and ask it to rate each for automation ROI using the repeatability and
determinism criteria. Then push back on its rankings — where does it overestimate determinism?
Where does it underestimate maintenance burden? The model is fast at the first-pass sort; the
judgment is yours.
