# Module 09 — Detection-as-Code Pipelines

*Variant D · build-first, eval-harness ("measure the detection, don't trust the demo"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *a detection that isn't measured isn't a detection — it's a guess with a YAML file and good demo luck.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Type:** Gate + Eval Harness &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 03 — IaC Security Scanning](../03-iac-security-scanning/README.md)
{ .module-meta }


## Why this matters
Track 02 (Defensive) taught you to write a Sigma rule and purple-team it: fire the technique, confirm
it catches it, tune out the false positives. This module is the engineering layer that keeps it caught.
A detection is not a static artifact — it is a non-deterministic classifier that you ship, refactor, and
re-tune for years, and it **rots silently**. Someone widens one selection to catch a new variant and
quietly floods the queue; someone refactors the rule "cosmetically" and drops the `-enc` short form;
someone upgrades the pipeline and a field rename means the rule now matches nothing. Nothing tells you,
because a rule that fired in last quarter's demo still *looks* fine in git — and the day it stops firing
is the day the one alert that mattered never arrives.

The fix is the same discipline the AI tracks call **"eval gates, not vibes"**: you cannot trust — or
improve — a detection you do not measure. This module turns detection-as-code from "rules are in git"
(version-control theater) into a **measured** system: every rule scored against a held-out corpus, a
scorecard you can read, and a CI gate that fails the build the day the numbers drop. It is automation's
worked example of the Eval Harness type — the same shape an AI triage model or a RAG needs.

## Objective
Build a two-stage CI gate for a Sigma ruleset — `sigma check` (syntax) plus a `pytest` intent table —
then **make it an eval harness**: score the rules against a **held-out, labelled** event corpus distinct
from the tuning set, print a **scorecard** (precision / recall / FP-rate over a confusion matrix), and
wire a **regression gate** that fails the build on a degraded or over-broad rule. The proof is the
contrast: GREEN on the good ruleset, RED on a planted regression.

## The core idea

A Sigma rule CI pipeline starts with two gates, and most teams stop there. **Stage one is syntax
validation** (`sigma check`): malformed YAML, unknown fields, an invalid condition expression — caught
before the rule is ever compiled to a SIEM query. **Stage two is intent testing**: a `pytest` table
where each `(rule, event, expected)` triple asserts that the rule fires on a specific attack event and is
quiet on a specific benign one. `pytest.parametrize` makes the table the contract — it documents exactly
what each rule is supposed to detect and ignore, and any change that breaks a row needs explicit
re-approval. The false-positive rows ("should NOT match") are the part most pipelines skip and the part
that matters most: proving a rule *fires* is easy; proving it doesn't fire on a legitimate PowerShell
module install or a signed updater writing a Run key is what separates a precise detection from alert
fatigue. Those FP rows are scar tissue — each documents a false positive you already investigated and
refuse to see again. The CI gate `&&`-chains the two stages so either failure blocks the merge.

But the `pytest` table has a quiet flaw, and naming it is the whole reason this module exists: **it grades
the rules on the same handful of events you tuned them against.** That is a memorised exam. A rule passes
its own test table the way a model "passes" on the five demo alerts it was prompted with — of course it
does; those are the cases you built it for. Pass that table and you have an *anecdote* that the rule works,
not a *measurement*. The move that makes a detection trustworthy is the same one that makes an AI system
trustworthy: **score it against data it was never tuned on.**

**Held-out corpus vs. tuning set.** The single load-bearing line in detection eval is the wall between the
events you tune on (the `pytest` table, your atomics) and the events you *grade* on. The held-out corpus is
a separate, labelled set — known-malicious events the rule MUST catch, and known-benign lookalikes it must
NOT fire on — that the rule has never seen. It deliberately includes the **variants** (the `-enc` short
form *and* the long `-EncodedCommand`; the technique spawned by `cmd`, `wscript`, and an Office child) and
the **near-misses** (a base64 string in an argument that isn't `-enc`; a backup agent opening its own
handle; an EDR sensor's allow-listed LSASS read). It is the only honest estimate of how the rule behaves on
the *next* event it has never seen. This is the standard train/dev/test split from machine learning, applied
to a rule that was never "trained" in the gradient sense — the discipline transfers intact.

**The scorecard, and why not accuracy.** Run the ruleset over the held-out corpus and you get a confusion
matrix — true/false positives and negatives — and the ratios built from it. The positive class is
*malicious*, and the load-bearing metric is **recall**: of the truly malicious events, how many did the
rule catch? A miss is a false "all clear" that can cost a breach. Its cost twin is the **false-positive
rate**: benign events that fired, each one an analyst's time. **Accuracy is the trap** — a corpus is wildly
imbalanced and the costs are asymmetric, so a rule that ignores the rare attack can still post 90%+ accuracy
while missing every intrusion. Watch recall first; then push the FP-rate down without losing recall. (Precision
and F1 are reported too, but recall + FP-rate are the pair a detection engineer actually defends.)

**Coverage ≠ effectiveness.** A 200-event corpus is not better than a 22-event one if all 200 are easy. What
earns the corpus its keep is the hard cases — the benign event crafted to look malicious, the malicious
variant phrased unusually. Counting events is vanity; deliberately sampling the failure modes is the work.

**The regression gate is the deliverable.** The thing that makes this engineering rather than a one-off study
is a gate: `eval.py` runs in CI, and a rule change that drops recall below a floor (or pushes FP-rate above a
ceiling) **fails the build** — exactly as a unit test fails on a broken function. The proof a gate works is a
*planted regression*: a deliberately degraded ruleset (a refactor that dropped the `-enc` short form, an
over-broad selection that now fires on benign traffic) that must turn the scorecard red and exit non-zero. A
gate you have only ever watched pass is not a gate — you have not shown it can catch anything. The contrast —
GREEN on the good rules, RED on the regressed ones — *is* the lesson, and it is what lets a team refactor a
detection on a Friday without praying.

## Learn (~2.5 hrs)

**sigma-cli & the rule spec (~45 min)**
- [sigma-cli — SigmaHQ (README through "Usage")](https://github.com/SigmaHQ/sigma-cli) — understand `sigma check`, `sigma convert`, and pointing it at a rules directory; this is stage one of the gate.
- [Sigma rule specification — SigmaHQ (the "Detection" section)](https://github.com/SigmaHQ/sigma-specification) — skim what a valid `detection`/`condition` block looks like; knowing what `sigma check` validates helps you write rules that pass it.

**pytest as the intent contract (~45 min)**
- [pytest — "How to parametrize fixtures and test functions"](https://docs.pytest.org/en/stable/how-to/parametrize.html) — the parametrize pattern *is* the detection test table; read the full section.
- [sigma-test — a test-case runner for Sigma rules (bradleyjkemp)](https://github.com/bradleyjkemp/sigma-test) — a compact tool that embodies this exact pattern: drop example events beside each rule and assert `match: true/false`. Read its examples to see the rule + event + assert contract before you wire it into pytest.

**The eval-harness layer — held-out sets, the metrics, the gate (~1 hr)**
- [Google ML Crash Course — "Accuracy, recall, precision"](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall) — the precise definitions your scorecard prints, and *why accuracy misleads on imbalanced classes* — exactly a detection corpus. Short and visual.
- [Google ML Crash Course — "Thresholding & the confusion matrix"](https://developers.google.com/machine-learning/crash-course/classification/thresholding) — how widening a rule trades recall against false positives; this is the curve you tune.
- [Sigma rule testing & quality — SigmaHQ rule-creation guide](https://github.com/SigmaHQ/sigma/wiki/Rule-Creation-High%E2%80%90Level-Guide) — SigmaHQ's own take on false positives and rule quality, from the project that maintains thousands of community rules.

> *Cross-track note:* this is the **Eval Harness** type ([ai-augmented-ops 11 — AI Evaluation](../../../12-ai-augmented-ops/modules/11-ai-evaluation/README.md) is its sibling): a triage model, a RAG, and a detection are all non-deterministic systems improved by *a held-out set + a metric + a regression gate*, not by vibes. Same shape, different classifier.

## Key concepts
- Two-stage gate first: `sigma check` (syntax) `&&` `pytest` (intent) — either failure blocks the merge.
- The `pytest` table is the tuning set; passing it is an anecdote, not a measurement — it grades the rules on the events they were built for.
- Held-out corpus vs. tuning set: you tune on one and *grade* on the other, or every number lies. Include the variants and the near-miss benigns.
- The scorecard: recall (caught attacks / all attacks) is the metric that matters; FP-rate is its cost. **Accuracy is deceptive** on an imbalanced corpus.
- Coverage ≠ effectiveness — test the events that *break* the rule, not just *more* events.
- The regression gate is the deliverable: a planted regression must turn the scorecard RED and exit non-zero. A gate you've only seen pass isn't a gate.

## AI acceleration
A model writes Sigma rules and the mechanical eval parts well — the syntax, the `pytest` table skeleton,
the confusion-matrix arithmetic, the scorecard formatting. **What you must own is everything a model
quietly gets wrong here.** First, the false-positive test rows: ask for them and the model routinely
hands back a "benign" event that *still matches the rule's condition* (it is subtly malicious), which
makes the test wrong — correct it with a genuinely benign event and document why the model's version
failed. Second, the metric: a model defaults to **accuracy**; you override it to **recall on the malicious
class** and justify it against the imbalance. Third, the held-out wall: a model will happily score the
rules on the same events it tuned them against — you enforce the separation, because *a model labelling
its own test set is the contamination this whole module warns against*. Fourth, the gate direction: does
it fail *closed* when the score is missing or `eval.py` errors, or does a broken eval silently "pass"?
Ask the model for *adversarial* held-out events — benign activity crafted to look malicious — then label
each one yourself against the technique it mimics.
