# Lab 13 — Incident Response Process: Mapping the Meridian Incident to NIST SP 800-61

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **concept and exercise module** — no container required. The exercise works from the
incident brief in the companion [`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/13-ir-process
make demo    # prints the incident brief and the exercise prompts
```

Open `data/meridian-incident-brief.md` — a two-page fictional incident scenario. The brief
contains a partial timeline with intentional gaps, a list of response actions taken, and several
decision points where the team's choices had downstream consequences. Your task is to analyse
the response against NIST SP 800-61.

> This exercise uses a fictional scenario. Any resemblance to real incidents is coincidental.
> Chain of custody and legal considerations are simulated for educational purposes.

## Scenario

Meridian Financial has completed the containment and recovery phase of the incident documented
across modules 08–12. You are the IR team lead, presenting a post-incident analysis to the
security steering committee. The committee wants to know: what happened, what worked, what
failed, and what Meridian should do differently. You have the incident brief and the findings
from the previous modules.

## Do

1. [ ] **Read `data/meridian-incident-brief.md` in full.** Identify the four NIST SP 800-61
   phases in the brief. For each phase, find at least one action the team took and at least
   one action that was missing or delayed.

2. [ ] **Complete the timeline gaps.** The brief has three [UNKNOWN] entries — moments where
   the brief doesn't say what the team did. Based on NIST guidance and the context, write
   what the team *should* have done at each gap. Cite the specific NIST section that informs
   your recommendation.

3. [ ] **Evaluate the containment decision.** The brief notes that the team waited 4 hours
   after the initial SIEM alert before isolating WORKSTATION-04. Using the detection-to-action
   timeline from the brief, argue either that this delay was justified or that it was too long.
   Use the NIST 800-61 "Containment" decision factors (section 3.2.4) as your framework.

4. [ ] **Identify eradication gaps.** The brief lists the eradication steps the team took.
   Cross-reference them against the attack chain from modules 08–12. Which step was missed?
   (Hint: what cloud artifact from module 10 is not mentioned in the eradication list?)

5. [ ] **Write the lessons learned** (post-incident section). Answer two questions:
   - What was the *earliest* point this incident could have been detected by an existing or
     achievable control? What would that control be?
   - What single control addition or improvement would have the highest probability of stopping
     or accelerating detection of a similar incident in the future?

6. [ ] **NIST phase scorecard.** Create a simple table: four phases, each scored Adequate /
   Partial / Inadequate for the Meridian response, with one sentence of evidence for each score.

## Success criteria — you're done when

- [ ] All four NIST phases are identified and evidenced from the incident brief.
- [ ] All three timeline gaps are filled with NIST-cited recommendations.
- [ ] The containment decision is argued with specific reference to NIST 800-61 section 3.2.4.
- [ ] The eradication gap is identified and the missing step is named.
- [ ] The lessons-learned section answers both questions concisely.
- [ ] The NIST phase scorecard is complete.

## Deliverables

Commit to your portfolio repo:
- `ir-analysis.md` — your complete NIST phase analysis, timeline gaps filled, containment
  argument, eradication gap finding, lessons learned, and scorecard.

## Automate & own it

**Required.** Write a Python script `ir_timeline_checker.py` that:
1. Reads a structured incident timeline as a CSV (columns: `timestamp`, `phase`, `action`, `actor`).
2. Validates that all four NIST phases are represented.
3. Flags any gap between consecutive timestamps that exceeds a configurable threshold
   (default: 2 hours) and labels it as a "response delay."
4. Prints a summary: phases represented, total timeline duration, number of delays flagged.

A sample timeline CSV matching the Meridian incident is in `data/meridian-timeline.csv`.
Have a model draft the script; **test it against the sample CSV** and confirm the output
makes sense before using it in a real post-incident review. Commit `ir_timeline_checker.py`.

## AI acceleration

Feed the incident brief to a model and ask: "Map this incident to the four NIST SP 800-61
phases and identify what's missing from each phase." Compare the model's mapping to your own.
The model is likely to correctly identify the major phase activities but may miss nuances like
the eradication gap (because it requires cross-referencing module 10's CloudTrail findings,
which you've read but the model hasn't — unless you include that context). The exercise teaches
you where model analysis needs human contextual input.

## Connects forward

Module 14 (Reporting) takes your `ir-analysis.md` and the timeline from this module and formats
them into a defensible incident report. The lessons-learned section is the direct input to the
Executive Summary in that report.

## Marketable proof

> "I map IR engagement findings to NIST SP 800-61, identify phase-level gaps in response
> quality, and produce post-incident analyses that drive remediation roadmaps — not just
> timelines."

## Stretch

- Research the PICERL model (Preparation, Identification, Containment, Eradication, Recovery,
  Lessons Learned) and compare it to NIST 800-61. Where do they diverge? Write a half-page
  comparison and note which phase breakdown you'd argue for in a regulated financial services
  environment and why.
- Draft a one-page IR runbook for the specific attack pattern in the Meridian incident (phishing
  → endpoint compromise → credential extraction → cloud pivot). Format it as a decision tree
  with detection → containment → eradication steps. This becomes a portfolio artifact demonstrating
  you can operationalise an incident into repeatable procedure.
