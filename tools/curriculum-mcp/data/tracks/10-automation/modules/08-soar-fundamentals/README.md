# Module 08 — SOAR Fundamentals

*Type 7 · Build-&-Operate — ship a working SOAR playbook and run it; the deliverable is the operating playbook plus its four-scenario test, not an essay. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *a playbook is repeatable; an analyst running the same triage for the fifth time this week is not.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3.5–4.5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md), and Module 04 (you'll wire HTTP/REST calls between services)
{ .module-meta }

## Why this matters

A SOC analyst's first five minutes on most alerts are the same five minutes, every time: copy the
source IP, paste it into a threat-intel lookup, check the asset inventory, open a ticket, fill in the
fields, decide whether it's worth waking someone up. It is mechanical, it is repetitive, and it is
exactly the work that erodes people. **Alert fatigue is not a metaphor** — it is the documented
condition where a flood of low-context alerts trains analysts to dismiss them, and the one that
mattered gets dismissed with the rest. The 2013 Target breach is the canonical example: the
intrusion *did* generate alerts from the deployed tooling, and they were not acted on in time — the
signal was there, buried in the volume and the manual toil of triaging it (the U.S. Senate Commerce Committee's [*A "Kill Chain" Analysis of the 2013 Target Data Breach*](https://www.commerce.senate.gov/wp-content/uploads/media/doc/2014%200325%20Target%20Kill%20Chain%20Analysis.pdf), March 26, 2014, documents how the deployed FireEye and Symantec tooling flagged the intrusion and the warnings went un-actioned).

SOAR — Security Orchestration, Automation, and Response — attacks that toil directly. It connects
the tools a SOC already runs (SIEM, threat-intel APIs, ticketing, firewalls) into **playbooks** that
execute the repetitive first-response steps automatically. The analyst no longer arrives to a raw
alert and a list of tabs to open; they arrive to a pre-enriched, pre-triaged event with a
recommended action attached. The work that's left is the *judgment* — which is the work you actually
want a human doing. The point of this module is not the concept; it's that **you build a working
playbook and operate it**, and the one design decision that makes it good (or dangerous) is where you
put the human.

## The core idea

**The playbook architecture is four stages: trigger → enrich → decide → respond.** The *trigger* is
usually a webhook the SIEM fires when an alert crosses a threshold. *Enrichment* queries the things a
human would query — threat intel for the IP, the asset DB for the host — and attaches the answers to
the event. The *decision* logic checks whether the enriched event meets the escalation bar. The
*response* creates a ticket, sends a notification, or (with the right authority) takes a containment
action. You will build exactly this, as a real workflow in **n8n**, and run real alerts through it.

**The one load-bearing judgment is the human-in-the-loop gate: what auto-contains versus what waits
for a human.** This is the whole design, and it's a blast-radius-versus-speed tradeoff. Fully
automated response is *fast* — auto-block any IP whose abuse score is over 90 and the attacker is cut
off in seconds — but it is *brittle*: a false positive now means your playbook took a containment
action against legitimate traffic, and an automated mistake executes at machine speed and scale, the
exact failure class this whole track turns on (*automation makes you faster, including at being
wrong*). Fully human-gated response is *safe* but *slow* — and slow is how the alert that mattered
sits in a queue. The practical resolution most teams land on, and the one you'll build: **automate
everything up to the containment action, then stop.** The playbook enriches, decides, and creates a
ticket that records *what action is recommended and why* — turning a fifteen-step manual procedure
into a one-click human decision. The reversible, low-blast-radius steps (look things up, write a
ticket, notify) auto-execute; the irreversible, high-blast-radius step (block, isolate, disable)
waits for a human. That line — drawn by reversibility and blast radius, not by what's technically
possible to automate — is the design judgment you're committing to.

**A playbook is only as good as its failure handling, which is why you operate it against four
scenarios, not one.** A workflow that handles a clean, well-formed alert and crashes on a null field
will fail *precisely when you need it* — during a live incident, when payloads are malformed and
upstream APIs are flaky. So you test it against (1) a well-formed alert, (2) an alert with a missing
field, (3) an alert where the enrichment API is down, and (4) an alert whose verdict comes back
`unknown`. The playbook must produce a sensible ticket for **all four** — never silently drop the
event, never crash. Getting the happy path working is the easy 80%; the error branches are where the
real engineering — and the real reliability — live.

> **Where this goes next.** This module ships an *operating* playbook tested against four hand-picked
> scenarios — enough to prove it doesn't crash, *not* enough to prove it's accurate. A playbook makes
> verdict-shaped decisions, and "does it decide correctly across a labelled set of alerts?" is a
> *measurement* question, not a build question. Scoring the playbook against a held-out, labelled
> corpus of alerts (precision/recall on its escalate-vs-monitor calls, a regression gate that fails a
> degraded version) is a **Type 13 Eval Harness** — the natural stretch once the thing runs. Module 09
> builds exactly that discipline for detections; the same shape applies here.

n8n is the right learning platform because its workflow is **human-readable JSON**: nodes map
directly onto the REST calls you already understand from Module 04, the file is version-controllable
and diffable (a playbook *is* an artifact, not a screenshot), and it runs locally in Docker at zero
cost. The production platforms — Splunk SOAR, Palo Alto XSOAR, Tines, Shuffle (open-source), Torq —
share the identical mental model: triggers, nodes, conditions, actions. Learn the model here and only
the editor changes.

## Learn (~2.5 hrs)

**SOAR concepts — the category and the gate decision (~1 hr)**
- [What is SOAR? — IBM](https://www.ibm.com/think/topics/security-orchestration-automation-response) (~20 min) — a vendor-neutral overview of the category. Read the "How SOAR works" and "SOAR vs SIEM" sections; the rest is marketing.
- [Fortinet — "How to Automate Security Operations With SOAR Playbooks"](https://www.fortinet.com/resources/articles/automate-security-operations-with-soar) (~15 min) — read for the **playbook anatomy** (trigger, tasks, conditional branches) and, crucially, the framing of *automated vs. analyst-gated tasks* — approval gates before disruptive actions like account deactivation or network isolation — that's the human-in-the-loop judgment this module is built on. Skim past the product pitch.

**n8n — enough to build the four nodes (~1.5 hrs)**
- [n8n — Quickstart](https://docs.n8n.io/try-it-out/quickstart/) (~40 min) — work through it once; you need *workflow*, *node*, and *connection* as working concepts, not mastery.
- [n8n — Webhook node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) (~15 min) — the trigger. Understand how to get the webhook URL and how n8n passes the incoming payload to downstream nodes (the `{{$json...}}` expression syntax).
- [n8n — HTTP Request node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/) (~15 min) — the node that calls the threat-intel API and posts the ticket. Note how it handles a non-2xx response — that's your "API is down" branch.
- [n8n — IF node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/) (~10 min) — the decision stage; routes on the enrichment verdict. This is where the escalate-vs-monitor (and, after you extend it, the `unknown`) logic lives.

## Key concepts
- **The playbook architecture: trigger → enrich → decide → respond** — a workflow engine wired to security tools.
- **The human-in-the-loop gate is *the* design judgment** — what auto-contains vs. what waits, drawn by **blast radius and reversibility**, not by what's automatable.
- **The middle ground:** automate up to the containment action; create a ticket with a recommended action; leave the irreversible step as a one-click human decision.
- **Webhook trigger** = the interface between the SIEM and the playbook; the payload flows node to node.
- **Workflow JSON is the artifact** — human-readable, diffable, version-controlled (the playbook *is* code).
- **Four-scenario test** — happy path, missing field, API down, unknown verdict; a ticket for all four, a crash for none.
- **Operate ≠ evaluate** — four scenarios prove it runs; *scoring* it against a labelled corpus is a Type-13 eval (the stretch).

## AI acceleration

n8n workflow JSON is verbose and tedious to author by hand — a natural thing to ask a model to draft.
Describe the four-stage playbook (webhook → enrich → IF → ticket) and have it generate the workflow
JSON; import it into n8n and run your four scenarios against it. **A model-generated workflow almost
always handles the happy path and misses the failure branches** — there will be no "enrichment API is
down" path, no handling for the missing `source_ip`, no `unknown`-verdict route. The standing posture
holds — **AI authors → you review every line → you own it** — and here the review has a sharp,
testable shape: the gaps in the model's workflow *are* the gaps in its model of how things fail in
production, and closing them (the error branches you add and test) is the actual learning. The model
gets you the 80% that was tedious; you supply the 20% that makes it reliable, and you prove it by
running the four scenarios.
