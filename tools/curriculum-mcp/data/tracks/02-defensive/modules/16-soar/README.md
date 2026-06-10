# Module 16 — Response Automation (SOAR)

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *automate the boring 80% of response — with a human on the trigger.*

## Why this matters
A SOC drowns in repetitive response: enrich the alert, check the intel, open a ticket, maybe contain.
SOAR automates that toil so analysts spend their judgment where it matters — and it's the natural home
for AI-augmented triage. This is the capstone of defensive operations: tie your telemetry, detections,
intel, and IR process into an automated, human-in-the-loop workflow. *Automation is assumed now; the
skill is designing it well and keeping the human in command.*

## Objective
Build a SOAR playbook that takes a real alert, enriches it, decides (with optional AI triage), and
tickets/contains it — with a human approval gate.

## The core idea
A SOC drowns in repetitive response — enrich the alert, look up the intel, open a ticket, maybe
contain — and most of it is the same keystrokes every time. **SOAR** automates that toil so analysts
spend judgment where judgment is actually needed. The mental model is a *playbook*: trigger → enrich →
decide → act, wiring together everything this track built (telemetry, detections, intel, the IR
process) into one workflow. It's the capstone of defensive operations precisely because it
*integrates* the rest — and it's the natural home for AI-augmented triage: a small local model for
high-volume "is this even interesting?", a frontier model for the genuinely hard call.

The distinction that drives every design decision: orchestration (connecting tools), automation
(doing steps without a human), and response (the action) are not the same thing — and the art is
deciding *which steps are safe to fully automate and which need a human gate*. Enrichment is safe
(read-only, reversible). *Containment* is not (it acts on production, hard to undo). Shuffle gives you
an OSS platform to build the whole loop for free.

The judgment, and the sharpest form of the standing rule: this is where automation stops being
advisory and *becomes the deliverable*, so **AI authors → you review → you own it** bites hardest. An
AI triage step that auto-closes alerts will eventually auto-close a real one; an auto-contain action
on a false positive takes down production *at machine speed*, before any human can intervene.
Automation multiplies whatever judgment you encoded — including the bad judgment — so the entire skill
is placing the human gate exactly where a wrong machine decision would hurt, and owning that design.

## Learn (~4 hrs)

**The platform**
- [Automate Everything with Shuffle! (video)](https://www.youtube.com/watch?v=_riaZjLnoXo) — building SOAR workflows in the OSS platform.
- [Shuffle documentation](https://shuffler.io/docs) — apps, workflows, and triggers.

**What to automate**
- [MITRE ATT&CK](https://attack.mitre.org/) — automate response mapped to the techniques you detect; and the Pyramid of Pain for what's worth containing.

## Key concepts
- SOAR: orchestration vs automation vs response
- Playbooks: trigger → enrich → decide → act
- Human-in-the-loop (and when to require approval)
- Where AI fits: triage/summarisation as a step (local model for volume, frontier for hard calls)
- The danger of automating a wrong decision at machine speed

## AI acceleration
This is the module where AI/automation stops being advisory and becomes the deliverable — and where
the standing rule bites hardest: **AI authors → you review → you own it**. An AI triage step that
auto-closes alerts will eventually auto-close a real one; an auto-contain action on a false positive
takes down production. Put the human gate where a wrong machine decision would hurt, and own that
design.
