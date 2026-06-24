# Module 09 — Detection Testing & Tuning

*Type 5 · Detonate & Detect — run a real ATT&CK technique with Atomic Red Team, validate your detection catches it, and tune away the false positives; you commit a purple-team loop that emits FIRED/MISSED/FP and a coverage summary. (Secondary: Eval Harness — extend the loop toward a held-out corpus and a gate that fails on regression.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Defensive Operations** — *an untested detection is a hope; fire the real technique and find out.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
Detections rot. The only way to know yours actually work is to *fire the technique* and watch —
purple teaming. Atomic Red Team runs real ATT&CK techniques safely and repeatably, so you can
validate that your detection catches the behaviour, measure your false-positive rate, and tune. This
closes the loop: attack → detect → tune, the daily reality of detection engineering.

## Objective
Run a real ATT&CK technique with Atomic Red Team, validate your detection catches it, and tune for
false positives.

## The core idea
A detection you haven't fired the technique against is a hope, not a control. Detections rot
constantly — a Windows update renames a field, a log source quietly drops, an attacker shifts to a
variant — and the only way to know yours still works is to *execute the behaviour and watch*. That's
purple teaming, and **Atomic Red Team** makes it cheap: a library of small, ATT&CK-mapped tests that
run a real technique safely and repeatably, so you can prove a detection catches it — or discover it
doesn't — on demand rather than during the breach.

The mental model is the confusion matrix made operational: a **true positive** fires on the real
thing (good), a **false positive** fires on benign activity (the fatigue-maker from module 06), and a
**false negative** is the technique running while you're blind (the one that ends careers). Detection
engineering is the loop of *attack → detect → tune*, pushing false negatives and false positives down
together while knowing they trade against each other. This is also where module 08's Sigma rule
finally gets tested under fire: write the rule, run the atomic, confirm it fires.

The judgment: **coverage is a moving target, not a milestone.** "We detect T1059" is true only until
the next variant or config change, so testing is a continuous practice, not a one-time audit. A model
can help interpret *why* a detection didn't fire and suggest a tweak — but it can't run the atomic or
see your environment's real noise, and a threshold it proposes may look clean while silently dropping
real detections. You run the test, read the result, and own the tuning.

The deeper reframe is that **a detection is a hypothesis scored on a ~99.99%-benign stream** — and
"it fired in the demo" is the same trap as a model that aced the examples you tuned it on.
*Coverage ≠ effectiveness*: that you wrote a rule for T1059 says nothing about whether it catches
the *next* T1059 variant or how often it screams on benign noise. The honest move is the eval
harness — the same discipline an ML team uses on a classifier, applied to a rule. Build a **held-out
corpus**: labelled known-malicious and known-benign events the rule was *never tuned on* (include
variants it must catch and benign lookalikes it must not fire on). Score the rule against it for the
metrics that matter — **recall** on the malicious class (caught attacks / all attacks; a miss can be
a breach) and **false-positive rate** (the analyst-time cost) — not accuracy, which a 95%-benign
stream makes meaningless. Then **gate it**: wire the eval so a change that drops recall below your
floor *fails the build*, and prove it by watching it go red on a deliberately-regressed copy of the
rule. A detection without a held-out eval and a regression gate is a hope with good demo luck; with
them, it's a measured control that can't silently rot.

## Learn (~4 hrs)

**Adversary emulation**
- [Atomic Red Team explained — Red Canary (video)](https://www.youtube.com/watch?v=eAtlwqXDZYc) — a crash course from the project's own team.
- [Atomic Red Team (project + atomics)](https://github.com/redcanaryco/atomic-red-team) — the library of real, ATT&CK-mapped tests you'll run.

**Method**
- [MITRE ATT&CK](https://attack.mitre.org/) — pick the technique; the atomic maps to it directly.

## Key concepts
- Purple teaming: attack → detect → tune
- Detection validation (does it actually fire?)
- True/false positives and negatives
- Tuning for signal without losing coverage
- Coverage as a moving target
- A detection is a hypothesis scored on a ~99.99%-benign stream — coverage ≠ effectiveness
- The eval harness: score a rule against a **held-out** corpus (recall + FP-rate, not accuracy) and
  **gate** it so it can't silently regress; prove the gate by watching it go red on a planted regression

## AI acceleration
A model helps interpret why a detection didn't fire and suggests tuning — useful. But it can't run the
test or see your environment's noise; it'll suggest a threshold that looks clean and silently drops
real detections. You run the atomic, read the result, and own the tuning.
