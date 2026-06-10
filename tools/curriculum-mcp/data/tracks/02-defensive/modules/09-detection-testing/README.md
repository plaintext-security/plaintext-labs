# Module 09 — Detection Testing & Tuning

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *an untested detection is a hope; fire the real technique and find out.*

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

## AI acceleration
A model helps interpret why a detection didn't fire and suggests tuning — useful. But it can't run the
test or see your environment's noise; it'll suggest a threshold that looks clean and silently drops
real detections. You run the atomic, read the result, and own the tuning.
