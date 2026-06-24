# Module 18 — Detection & Telemetry Drift

*Type 16 · Drift / Steady-State — declare your telemetry sources and detections as a baseline, introduce realistic drift (a log source silently stops, a rule rots against a renamed field), detect the delta with a heartbeat + rule-decay monitor, and reconcile back to baseline; you commit the drift detector plus a reconciliation runbook. (Secondary: Eval Harness — drift is measured by re-scoring detections against a held-out corpus over time.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Defensive Operations** — *the system is green at t=0 and blind at t=30; the skill is noticing.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md), and ideally [08 Detection-as-Code](../08-detection-as-code/README.md)
{ .module-meta }

!!! abstract "In 60 seconds"
    A detection programme is never *done* — it decays. A Windows update renames a field and a rule
    silently stops matching; an agent's cert expires and a log source goes dark with no alarm; an
    analyst tunes a rule in the console and the git copy rots. The SIEM keeps drawing dashboards from
    the data it still has, so everything *looks* healthy while you go blind. **Drift work** is the
    steady-state discipline: declare the baseline (sources + detections as code), watch observed
    state against it (source heartbeat, rule-execution health, periodic re-scoring), and reconcile
    the delta before an attacker finds it for you.

## Why this matters
Every other module in this track gets you to *green*: the pipeline ingests, the rule fires, the
coverage map fills in. None of them keep you green. Coverage is not a state you reach; it is a
state you *maintain against constant decay*. A log source that stopped sending data three weeks ago
won't raise an alarm — your SIEM cheerfully keeps generating dashboards from the data it still has,
while an attacker moves freely through the systems that went dark. A Sigma rule that was perfect in
module 08 quietly stops matching the day a vendor renames `ParentImage` or splits an event into two.
"Set and forget" is the failure mode, and it fails *silently* — which is why it's the hardest kind
of gap to find. This module is the operational habit that the whole detection track depends on but
never builds: the steady-state loop that proves your t=0 coverage is still your t=30 coverage.

## Objective
Establish a declared baseline of telemetry sources and detections; introduce realistic drift (a
source that stops, a rule that rots against a renamed field); build a detector that diffs observed
state against the baseline and reports the delta; and reconcile back to a proven steady state.

## The core idea

**Declared state vs. observed state — the whole game.** Borrow the mental model straight from
infrastructure-as-code: you have a *declared* state (the sources you expect to be logging, the
detections you expect to be firing) and an *observed* state (what's actually arriving and matching
right now). Health is not "the SIEM is up" — it's "observed == declared." Drift is the gap between
them, and the steady-state loop is the same four beats config management uses: **detect → diff →
report → reconcile**, run on a schedule forever. The reason this is a *defensive* skill and not just
ops hygiene is that the gap is an attacker's window: the interval between a source going dark and you
noticing is exactly the interval in which something can happen in the dark.

**Telemetry drift is a heartbeat problem; detection drift is a re-scoring problem.** They decay
differently, so you watch them differently. A *source* drifts by **volume and recency**: the clean
signal is a heartbeat — "endpoint X last logged at HH:MM, expected every N minutes" — plus a volume
baseline so you catch the half-failures (an agent still alive but emitting a tenth of its events,
which a binary up/down check sails right past). Half of all SIEM detection failures trace back to a
log-collection problem, not a bad rule, which is why source health is the first thing to instrument.
A *detection* drifts by **effectiveness**: the rule still executes without error, but it no longer
matches the behaviour it was written for — because a field got renamed, an event schema changed, or
(Gary Katz's framing) the adversary adapted their procedure just past the edge of your logic. You
can't see that from "did the rule run"; you can only see it by re-firing the rule against telemetry
where you *know* the answer and watching the hit drop to zero. That is why this module leans on the
held-out corpus from detection-testing: **the corpus is your drift instrument** — re-score against it
on a schedule and a rule that silently stopped catching its technique shows up as a recall regression.

!!! note "The mental model"
    Two clocks tick against you. The **source clock** (is data still arriving, at the expected
    volume?) and the **detection clock** (does the rule still catch what it was written for?). A green
    SIEM tells you neither — you have to ask both, on a schedule, forever.

**Reconciliation is the deliverable, not the detection.** Finding drift is half the job; the
practitioner artifact is the *runbook* that closes it. When the heartbeat goes quiet, the reconcile
step is a decision tree, not a panic: is the host decommissioned (update the baseline), the agent
dead (restart/redeploy), or the collector choking (fix ingestion)? When a rule's recall drops, you
diff the rule against the current event schema, fix the field, re-score, and prove it's back. The
honest version of this loop *also reconciles the baseline itself* — a decommissioned host should
leave the expected-sources list, or it becomes a permanent false alarm that trains everyone to
ignore the one that matters. Steady-state isn't "no drift ever"; it's "drift is detected fast and
reconciled deliberately, every time."

!!! warning "The gotcha"
    A binary up/down heartbeat misses the most dangerous failure: the source that's *still alive but
    degraded*. The agent answers pings while emitting a fraction of its events — your dashboard is
    green, your coverage is gutted. Baseline the **volume**, not just the pulse.

## Learn (~3 hrs)

**Why coverage decays (~1 hr)**
- [Tracking Detection Drift — Gary Katz (Medium, 2023)](https://medium.com/@gary.j.katz/tracking-detection-drift-7ab29dcd3fbc) — the article that names the concept: detection drift is the gap between the detections that *should* have fired and those that *did*, as adversaries adapt past your logic. ~15 min; read it for the "minimum detection" idea and why you measure drift continuously, not once.
- [Detection Engineering Metrics Building Blocks — Gary Katz (Medium, 2023)](https://medium.com/@gary.j.katz/detection-engineering-metrics-building-blocks-97be4bccf27b) — the prerequisite from the same series: TP/FP/TN/FN, precision and recall as the building blocks you'll re-compute over time. ~15 min; this is the maths the drift loop runs on.

**Telemetry source health (~1 hr)**
- [Guidance for SIEM and SOAR Implementation — CISA et al. (2025)](https://www.cisa.gov/resources-tools/resources/guidance-siem-and-soar-implementation) — joint guidance whose *Priority logs for SIEM ingestion* sheet pins down which sources matter and why visibility/coverage is an operational requirement, not a one-time setup. Read the priority-logs practitioner section. (cisa.gov may block non-browser clients; the page is the canonical reference.)
- [One More Time on SIEM Telemetry / Log Sources — Anton Chuvakin (Medium)](https://medium.com/anton-on-security/one-more-time-on-siem-telemetry-log-sources-b0a88572dac9) — the "output-driven SIEM" argument and, crucially for this module, the line that you must *monitor telemetry arrival*, not assume it. ~10 min; the judgment on which sources are worth a heartbeat.

**Detection health in practice (~1 hr)**
- [Monitor rule executions — Elastic Security docs](https://www.elastic.co/docs/solutions/security/detect-and-alert/monitor-rule-executions) — a real product's take on rule health: execution status (Succeeded/Failed/Warning) and **rule-execution gaps** (windows where a rule didn't run). Read it to see what "detection health" looks like as a first-class feature — and note it tracks *did the rule run*, not *is the rule still effective*, which is the gap this module fills.
- [Detection Rules (Elastic) — validation & schema](https://github.com/elastic/detection-rules) — skim the README: rules validated against a schema in CI is the upstream defence against the "renamed field silently breaks the rule" decay you'll induce in the lab.

## Key concepts
- Coverage is a *maintained* state, not a reached one — controls rot, and they rot silently
- Declared state vs. observed state; the steady-state loop: detect → diff → report → reconcile
- Two decay clocks: source health (heartbeat + **volume** baseline) vs. detection effectiveness (re-score)
- The half-failure: a degraded-but-alive source that a binary up/down check misses
- Detection drift = the gap between what should have fired and what did; re-score against a held-out corpus to see it
- Reconciliation as the deliverable: a decision-tree runbook that also prunes the baseline (decommissioned ≠ alarm)

## AI acceleration
A model is good at the scaffolding here — draft the heartbeat checker, the volume-baseline query, the
diff-and-report logic, the runbook skeleton. Push it: "write a check that flags a source emitting <50%
of its 7-day average," "given expected vs. observed source lists, output the delta as a table." But the
*thresholds* are yours to own — an AI will happily pick a heartbeat interval or a volume floor that
either screams every night or never fires, and it can't know that your nightly batch job legitimately
goes quiet at 2 a.m. Worse, asked to "summarise what drifted," a model will confidently narrate a
plausible cause it has no evidence for. The model drafts the loop; you set the thresholds against your
real baseline, and every "this source is fine / this is the cause" verdict is yours to verify, not its.

!!! question "Check yourself"
    - Your SIEM dashboard is green. Name two ways your detection coverage could still be gutted right now.
    - Why is a degraded-but-alive source more dangerous than one that's cleanly down?
    - You have a rule that runs without error every day. How do you know it still *catches* anything?
    - When a heartbeat goes quiet, why is updating the baseline sometimes the correct reconciliation?
