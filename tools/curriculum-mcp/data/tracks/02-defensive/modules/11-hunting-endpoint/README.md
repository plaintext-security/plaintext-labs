# Module 11 — Threat Hunting: Endpoint

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *don't wait for an alert — go looking for what your detections missed.*

## Why this matters
Detections catch the known; hunting finds the unknown. Threat hunting is hypothesis-driven: you assume
a breach, form a testable idea ("an attacker would persist via a Run key"), and go look across your
endpoint data. It's how teams find the dwell-time attacker that slipped past every rule — and
Velociraptor makes enterprise-scale endpoint hunting free.

## Objective
Run a hypothesis-driven hunt across real endpoint data with Velociraptor/osquery, and either find the
activity or rule it out.

## The core idea
Detection and hunting are opposite stances. Detection *waits* — it encodes known-bad and fires when
it appears. Hunting *goes looking* — it assumes a breach already happened and asks, "if an attacker
were here, what would I see, and is it there?" That flip from reactive to proactive is the whole
discipline: you're hunting precisely the thing your rules didn't have a signature for. And it's
*hypothesis-driven* — you form a specific, testable idea ("an attacker would persist via a Run key,"
"they'd do discovery with built-in tools") and then interrogate your endpoint data to confirm or
refute it. A hunt that ends in "ruled out" is a result, not a failure.

The organising principle is the **Pyramid of Pain**: hunt *behaviours*, not atomic indicators. A hash
or IP is trivial for an attacker to change (bottom of the pyramid); their techniques cost real effort
to alter (top). So "any Office app spawning a script interpreter" outlives any single hash —
hunt the TTP, not the IOC. Velociraptor and osquery let you ask that question across thousands of
endpoints at once (host-as-database, VQL/SQL), which is what makes hunting an enterprise activity
rather than a one-box exercise.

The judgment, and the payoff loop: hunting is judgment under ambiguity, and a model will happily
"confirm" a pattern that's just normal-for-you — treat its hypotheses and draft VQL as leads to test
against the data, never as conclusions. And the move that makes hunting *compound*: a successful hunt
becomes a new detection (module 08), so you only ever have to hunt that thing by hand once.

## Learn (~4 hrs)

**The method & the tool**
- [Hunt for Hackers with Velociraptor (video)](https://www.youtube.com/watch?v=S8POUZv7pT8) — endpoint hunting with the OSS platform.
- [Velociraptor documentation](https://docs.velociraptor.app/) — VQL, artifacts, and hunts; read "Getting Started."

**Method**
- [The ThreatHunting Project](https://www.threathunting.net/) — hunting methodology and concrete hunt ideas.

## Key concepts
- Hypothesis-driven hunting (assume breach)
- Endpoint hunt data: processes, persistence, auth, file
- VQL / osquery for hunting at scale
- The Pyramid of Pain (hunt for behaviours, not just IOCs)
- Turning a successful hunt into a detection

## AI acceleration
A model is great for generating hunt hypotheses and drafting VQL/osquery — but hunting is judgment
under ambiguity, and the model will happily "confirm" a pattern that's just normal-for-you. Treat its
leads as hypotheses to test against the data, never conclusions.
