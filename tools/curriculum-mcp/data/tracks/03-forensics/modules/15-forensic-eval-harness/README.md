# Module 15 — Forensic Eval Harness

*Type 13 · Eval Harness — take the timestomp/YARA detector you wrote in Modules 11–12 and prove it on a held-out, labelled corpus of benign and malicious files, producing a precision/recall scorecard and a CI regression gate that goes red when a rule change silently degrades detection; the deliverable is the reusable eval harness, not a one-off "it caught my sample." [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Digital Forensics & IR** — *a detection rule tested only against the sample that inspired it is a vibe; tested against a corpus you didn't author, it's a measured tool.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Type:** Eval Harness &nbsp;·&nbsp; **Prerequisites:** [11 — Anti-Forensics & Detecting It](../11-anti-forensics/README.md), [12 — Malware Artifacts in IR](../12-malware-artifacts-ir/README.md)
{ .module-meta }

## Why this matters

In Module 11 you wrote a Python detector that flags timestomping by comparing NTFS `$STANDARD_INFORMATION`
against `$FILE_NAME` timestamps. In Module 12 you authored a YARA rule that matched the Latrodectus loader.
Both worked — on the one file that prompted them. That is exactly the trap. A detection rule validated
only against the sample it was written from tells you nothing about how it behaves on the next thousand
files an investigation hands you: the benign installer that also touches file times, the packed-but-legitimate
binary, the attacker variant that shifted two bytes. You have an *anecdote* that the rule fired once, not
*evidence* that it discriminates malicious from benign. The day someone tweaks the rule to catch one more
sample and silently doubles the false-positive rate, nothing tells you — because you never had a number to
watch. In DFIR the cost is not abstract: a noisy rule buries a real finding under benign hits and an analyst
stops trusting it; a brittle rule declares a compromised host clean. This module is the discipline that turns
"I wrote a rule" into "I proved a rule," and it is the type the whole track was missing.

## Objective

Build an eval harness for a forensic detector: assemble a **labelled, held-out** corpus of benign and
malicious artifacts (timestomped vs. legitimately-modified files, and/or malicious vs. benign PE samples),
choose and justify a metric, score your Module 11/12 detector against it into a **scorecard**, and wire a
**CI regression gate** that fails the build when a rule change degrades precision or recall.

## The core idea

> **Your timestomp detector and your YARA rule both fired on the loader sample. Are they actually *good*?
> Prove it.** Before reading on, write down how you would convince a skeptical lead — with evidence, not
> adjectives — that your Module 11 detector is safe to run unattended across an enterprise disk image of
> 200,000 files.

If your honest answer is "it caught the timestomped file in the lab" or "the YARA rule matched the dropper,"
you have just named the trap. **You cannot prove it — not without a held-out corpus — and the sample that
inspired the rule actively lies to you.** Of course the rule matches the file you wrote it from; you tuned
it to. The reveal of this module is that the move which makes a detection rule trustworthy is not a cleverer
condition or a tighter byte string — it is *measurement against files the rule has never seen*, reported as a
number, gated in CI.

**Held-out set vs. the sample you authored from.** The single most important wall in any eval is between the
data you build the rule on and the data you grade it on. You write the YARA condition, pick the timestamp-divergence
threshold, and choose which `$SI`/`$FN` deltas count as suspicious against a *development* set; you report the
score against a *held-out* corpus the rule has never touched. Score on the file that inspired the rule and the
number is inflated by the same overfitting that makes a demo always succeed — you are grading the open-book
answer. A held-out corpus is the only honest estimate of how the detector behaves on the next disk you image.
(This is the train/dev/test split from machine learning, applied to a hand-written rule rather than a trained
model — the discipline transfers intact, and forensic tool validation has demanded it for decades under the
banner of *known-answer testing*.)

**Metric choice, and *why*.** A scorecard is only as honest as its metric, and "did it catch the bad file" is
the wrong one. The vocabulary you need is the confusion matrix — true/false positives and negatives — and the
ratios built from it: **precision** (of the files the rule flagged, how many were truly malicious?) and **recall**
(of the truly malicious files, how many did the rule catch?). For a *detection* rule the costs are asymmetric in
a way you must decide deliberately. A missed timestomp (a false negative) means a responder declares a host clean
when an attacker hid there — expensive. But a flood of false positives is also expensive in a way beginners
underestimate: a YARA rule that fires on every UPX-packed binary turns a triage queue into noise, and a rule
nobody trusts is a rule nobody runs. So the load-bearing judgment is naming which error you can least afford for
*this* rule and gating on it — high recall for a "find every variant" hunting rule, high precision for an
"auto-quarantine" rule — and watching the other number as the cost you pay. Accuracy alone is a liar here: on a
corpus that is 95% benign, a rule that flags nothing scores 95% "accurate" and catches zero attacks.

**Coverage ≠ effectiveness.** A 500-file corpus is not better than a 40-file one if all 500 are easy. Counting
files is vanity; the corpus earns its keep by including the cases that *break* the rule: the benign file that
legitimately has its timestamps rewritten (a software installer, a `touch -r` in a backup script), the malicious
sample that was repacked, the near-miss where `$SI` and `$FN` differ for an innocent reason. Coverage of the hard,
adversarial, near-miss cases — not just *more* cases — is what a real held-out corpus is for, and it is the work.

**The regression gate.** What makes this engineering rather than a one-off study is the **gate**: the eval runs
in CI, and a rule change that drops precision or recall below a declared threshold **fails the build** — exactly
as a unit test fails on a broken function. The proof that the gate works is a *planted regression*: a deliberately
loosened rule (one that now matches a benign string, or a divergence threshold set so low everything trips it)
that must turn the scorecard red and exit non-zero. A gate you have only ever seen pass is not a gate; you have
not shown it can catch anything. The green-on-good, red-on-regressed contrast *is* the lesson — it is what lets a
team improve a rule on a Friday without praying they didn't just blind it.

This module upgrades Modules 11 and 12 in place: 11's `$SI`/`$FN` detector and 12's YARA rule stop at "wrote the
rule" and now gain "proved the rule on a corpus I didn't author, with a gate that won't let it silently regress."
A detection without an eval is not done — it is a liability with good demo luck.

## Learn (~2.5 hrs)

**Confusion matrix & the metrics (~45 min)**
- [Google ML Crash Course — "Accuracy, recall, precision, and related metrics"](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall) — the precise definitions of precision/recall and, crucially, *when accuracy misleads on imbalanced data* (your corpus is mostly benign); short and visual, this is the vocabulary your scorecard prints.
- [Google ML Crash Course — "Thresholding and the confusion matrix"](https://developers.google.com/machine-learning/crash-course/classification/thresholding) — how moving a decision threshold (here, your timestamp-divergence cutoff) trades recall against false positives; this is the curve you tune in the lab.

**Detection-rule quality & false positives (~1 hr)**
- [YARA docs — "Writing YARA rules"](https://yara.readthedocs.io/en/stable/writingrules.html) — the rule syntax you'll be scoring: strings, conditions, the `of`/`for..in` operators. Read enough to read and edit the rule whose precision/recall you measure.
- [Florian Roth — "YARA Style Guide" (Neo23x0)](https://github.com/Neo23x0/YARA-Style-Guide) — practitioner conventions for *maintainable* rules, including the dedicated **false-positive filter (`$fp*`)** pattern — the manual analog of what your eval measures automatically. Read the FP-filter and metadata sections.
- [Florian Roth — `yarGen`](https://github.com/Neo23x0/yarGen) — a YARA generator that strips strings present in *goodware* before building a rule. Skim the README: the goodware-subtraction idea is exactly why you need a benign half in your corpus, and a cautionary note that auto-generated rules especially need a held-out FP check.

**Why held-out evaluation is non-negotiable (~30 min)**
- [Anthropic — "Define success criteria and build evaluations"](https://platform.claude.com/docs/en/docs/test-and-evaluate/develop-tests) — first-party guidance on measurable success criteria and **held-out test sets**; vendor-neutral on the principle ("an F1 of at least 0.85 on a held-out set," not "it works"). The framing transfers directly to a detection rule.
- [promptfoo docs — "Assertions & metrics"](https://www.promptfoo.dev/docs/configuration/expected-outputs/) — a config-driven eval/regression-gate runner; read how a test case declares an expected outcome and how a suite gates a change. This is the shape your `eval.py` mimics, and the tool you'd reach for in a shop that also evals AI output.

## Key concepts
- Held-out corpus vs. the sample you authored from: tune on one, grade on the other, or every number lies.
- Confusion matrix → precision and recall; for detection, *name which error you can least afford* and gate on it.
- Accuracy is a liar on imbalanced (mostly-benign) corpora — a rule that flags nothing scores 95% and catches zero attacks.
- The precision/recall tradeoff: loosen the rule and recall rises while precision (and analyst trust) falls; the eval finds the knee deliberately.
- Coverage ≠ effectiveness — the corpus must carry the benign-but-timestomped and repacked-malicious near-misses, not just *more* files.
- The regression gate: a planted regression (a loosened rule) must fail the build — a gate you've only seen pass isn't a gate.
- This is the decades-old forensic discipline of *known-answer / tool validation*, applied to your own rules as code.

## AI acceleration

Have a model draft the mechanical parts — the confusion-matrix arithmetic, the precision/recall computation, the
scorecard table, the harness that walks a directory and runs the rule over each file. That code is boilerplate and
a model writes it well. **What you must own is everything a model will quietly get wrong here:** the choice of
metric and its *direction* (a model defaults to accuracy — you override it to precision-or-recall and justify which,
for this rule's job), the held-out discipline (a model will happily score on the file the rule was written from; you
enforce the wall), and the gate's fail-closed behaviour (does the build fail when the eval errors or a file won't
parse, or does a broken eval silently "pass"?). Use a model to **expand the corpus with adversarial benign files** —
installers and backup scripts that legitimately rewrite timestamps, packed-but-legitimate binaries — then **label
each one yourself and verify it against what it actually does**, because a model labelling its own test corpus is the
contamination this entire module warns against. You generate candidates; you own the ground truth.
