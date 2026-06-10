# Lab 01 — The Automation Mindset

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
No container for this module — it's a structured thinking exercise.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/01-automation-mindset
make demo      # prints the assessment framework and the example task list
```

The `data/` directory contains `automation-assessment.md` — a pre-populated worksheet with 10
Meridian Financial security tasks, a blank ROI calculation table, and the decision framework.

## Scenario
Meridian's security operations team has a new mandate: reduce manual toil by 40% in the next
quarter. Before the team writes a single line of code, you've been asked to produce a structured
automation roadmap: which tasks to automate first, which to automate with a human-in-the-loop
gate, and which to leave manual because the determinism requirement isn't met.

> No containers, no credentials, no external systems — this is a thinking exercise.

## Do
1. [ ] `make demo` — read the framework printout. Understand the two axes (repeatability,
   determinism) and the three-zone model (full automation / human-in-the-loop / keep manual).
2. [ ] Open `data/automation-assessment.md`. For each of the 10 Meridian tasks:
   - Rate repeatability: how often does this happen? (daily / weekly / ad-hoc)
   - Rate determinism: given the same inputs, is the correct action always the same? (high / medium / low)
   - Estimate maintenance burden: what could change that would break this automation?
   - Place it in one of the three zones.
3. [ ] For the top 3 "full automation" candidates, draft the automation approach:
   - What tool or language? What triggers it? What does it log? How is it stopped?
   - What is the kill-switch mechanism?
4. [ ] For the top 2 "human-in-the-loop" candidates, define exactly where the human decision
   point is: what information does the human see, what choices do they have, and what does
   the automation do after the human responds?
5. [ ] Write a one-page `automation-roadmap.md` that summarizes your analysis and prioritized
   roadmap, starting with "start here" (highest ROI, lowest risk).

## Success criteria — you're done when
- [ ] All 10 tasks are assessed and placed in a zone with reasoning.
- [ ] Three automation designs and two human-in-the-loop designs are drafted (not implemented).
- [ ] `automation-roadmap.md` exists and could be presented to a non-technical manager.
- [ ] Each design includes a kill-switch mechanism.

## Deliverables
`data/automation-assessment.md` (filled in) + `automation-roadmap.md`. Commit both.

## Automate & own it
**Required.** This module's automation is the meta-task: use an AI assistant to help rate all
10 tasks. Give it the task list and the decision framework; accept its ratings as a first draft;
then review and override where you disagree. Document every override and the reason in the
assessment. Commit the assessment with both the AI's initial rating and your final rating for
each task — the deltas are the interesting part.

## AI acceleration
The assessment is the kind of structured analysis AI is genuinely useful for: it can rate all
10 tasks quickly and explain its reasoning. Test it: after it rates them, pick the two you
disagree with most and argue for a different placement. Does it update? Is its reasoning sound?
The skill here is adversarial engagement with the AI's output, not passive acceptance.

## Connects forward
The automation roadmap you produce here becomes the project brief for the rest of the track.
Modules 02-10 implement the automations on your "full automation" and "human-in-the-loop" lists.
You'll return to this document in module 10 and assess whether AI-generated automation introduced
risks you didn't anticipate.

## Marketable proof
> "Before I write automation, I can assess which tasks are good candidates, which need a human
> in the loop, and which should stay manual — and I can explain the ROI calculation to leadership."

## Stretch
- Research one real-world automation failure in security operations (hint: Google for "SOAR
  false positive storm" or "automation outage") and add a brief write-up to your roadmap:
  what went wrong, and which of the three failure modes did it represent?
