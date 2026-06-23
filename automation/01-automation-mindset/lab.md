# Lab 01 — The Automation Mindset

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
No container for this module — it's a structured decision exercise that ends in a written ADR.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/01-automation-mindset
make demo      # prints the assessment framework and the example task list
```

The `data/` directory contains `automation-assessment.md` — a worksheet with 10 real security-ops
tasks, a blank ROI table, and the three-zone framework. It also contains `ADR-TEMPLATE.md`, the
Nygard-format skeleton your deliverable fills in.

## Scenario
A security operations team has a mandate to reduce manual toil next quarter. Before anyone writes a
line of code, you've been asked to draw the **cut line**: which tasks to automate outright, which to
automate only up to a human decision point, and which to leave manual — and to *defend that line in
writing* so the team can disagree with the reasoning, not just the verdict. The disasters in the
module are your warning label: a wrong cut line, or an automated task with no gate, is how a
time-saver becomes a $440-million afternoon.

> No containers, no credentials, no external systems — this is a decision exercise. The artifact is
> the judgment, written down.

## Do
1. [ ] `make demo` — read the framework printout: the two axes (repeatability, determinism) and the
   three zones (**automate** / **assist** (human-in-the-loop) / **leave manual**).
2. [ ] Open `data/automation-assessment.md`. For each of the 10 tasks, fill the row:
   - Repeatability: how often does this exact sequence happen? (daily / weekly / ad-hoc)
   - Determinism: given the same inputs, is the correct action always the same? (high / medium / low)
   - Maintenance burden: what could change upstream and break the automation? (low / medium / high)
   - Zone: place it — and write the one-line reason.
3. [ ] Run the **ROI** sanity check on your top automation candidates: (minutes saved × times/week)
   minus maintenance. Demote any candidate the maintenance term turns negative — and say so.
4. [ ] For your "automate" picks, specify the three controls Knight Capital lacked, per task:
   the **gate** (what check must pass before it runs / proceeds), the **log** (what human-readable
   line it emits on every action), and the **kill-switch** (how it's stopped in under 60 seconds with
   no code change).
5. [ ] For your "assist" picks, pin the human decision point exactly: what the automation gathers,
   what the human sees, what choices they have, and what the automation does after they answer.
6. [ ] **Write the ADR** (the deliverable). Copy `data/ADR-TEMPLATE.md` to `ADR-001-automation-cut-line.md`
   and fill all four sections:
   - **Context** — the forces: the toil to cut, the team's tolerance for a wrong automated action,
     the two axes, the ROI/maintenance reality.
   - **Options** — the cut line is a choice; lay out 2–4 *different places you could draw it*
     (e.g. "automate aggressively," "assist-only / human gates everything," "automate only the
     high-determinism third"), each with pros and cons.
   - **Decision** — your cut line, in one or two sentences: which tasks land in which zone.
   - **Consequences** — the honest downsides you accept by choosing it (what stays slow, where you've
     added a thing to maintain, what could go wrong) **and a one-paragraph Knight Capital autopsy**
     that maps the 2012 loss to **no gate, no kill-switch, no review** — and states which of those
     your decision now guarantees for every "automate" task.

## Success criteria — you're done when
- [ ] All 10 tasks are assessed (both axes + maintenance + zone) with a one-line reason each.
- [ ] Your "automate" tasks each name a gate, a log line, and a 60-second kill-switch.
- [ ] `ADR-001-automation-cut-line.md` exists with all four Nygard sections filled — Options lists
      2+ real alternative cut lines, Decision is one defensible sentence, Consequences is honest.
- [ ] The Consequences section contains the Knight Capital autopsy paragraph mapping the loss to the
      three missing controls and tying it to your decision.
- [ ] A colleague could read the ADR and disagree with your *reasoning*, not just guess your verdict.

## Deliverables
`data/automation-assessment.md` (filled in) **+** `ADR-001-automation-cut-line.md`. Commit both. The
ADR is the portfolio artifact — it's the construct (Context · Options · Decision · Consequences) the
rest of this track and the ZTNA/AI tracks lean on.

## Automate & own it
**Required.** The "automation" here is the meta-task: use an AI assistant to produce the *first-pass*
assessment. Give it the 10 tasks and the framework, accept its ratings as a draft, then review every
row and **override where you disagree — documenting the delta and the reason**. Models reliably
over-rate determinism and under-rate maintenance burden; the overrides are the interesting part.
Commit the assessment showing both the AI's initial rating and your final rating per task. The ADR is
*yours* — written by you, defending the line — not the model's.

## AI acceleration
The first-pass sort is exactly what AI is good at: it rates all 10 tasks fast and explains itself.
Test it adversarially — pick the two placements you most disagree with and argue the other side. Does
it update? Is the reasoning sound, or confident-but-wrong? The skill is the adversarial engagement,
not passive acceptance: you own the cut line, so you have to be able to break its argument.

## Connects forward
This ADR is the project brief for the rest of the track. Modules 02–10 *implement* the lines you drew:
IaC and CI/CD build the **gates**; config management adds **drift detection**; SOAR builds the
**assist** (human-in-the-loop) playbooks; and module 10 hands you AI-written automation to **review**
— you'll return to this ADR and check whether the cut line held up once real code existed.

## Marketable proof
> "Before I write any automation, I can draw the automate / assist / leave-manual cut line for a set
> of security tasks and defend it in an ADR — including the gate, kill-switch, and review each
> automated task needs, and the ROI/maintenance reasoning behind the line."

## Stretch
- Pick a *third* real automation failure — the [2012 Knight Capital](https://www.sec.gov/litigation/admin/2013/34-70694.pdf) <!-- VALIDATE --> and [2017 AWS S3](https://aws.amazon.com/message/41926/) <!-- VALIDATE --> cases are in the module; find a different one (e.g. a "SOAR false-positive storm," a runaway auto-remediation, or a CI/CD auto-deploy that shipped a bad config) — and add a short paragraph to your ADR's Consequences: what control was missing, and which of *your* "automate" tasks would have the same gap if you're not careful.
