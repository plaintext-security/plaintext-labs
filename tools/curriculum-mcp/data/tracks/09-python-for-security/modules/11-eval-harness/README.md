# Module 11 — Eval Harness for Security Tools

*Type 13 · Eval Harness — build a labelled test corpus, a precision/recall scorecard, and a CI regression gate for the log parser/classifier you wrote earlier in the track, so its quality is *measured* and a future edit cannot silently break it. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Python for Security** — *a tool that works on the log you tested it against is an anecdote; a tool with a scorecard is software.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3.5–4.5 hrs (study + lab) &nbsp;·&nbsp; **Type:** Eval Harness &nbsp;·&nbsp; **Prerequisites:** [02 — Files, Regex & Log Parsing](../02-files-regex-parsing/README.md), [10 — Packaging, Testing & Owning AI Code](../10-packaging-testing/README.md)
{ .module-meta }

## Why this matters
You built a log parser back in Module 02 — it pulled failed-login IPs out of an SSH auth log and
flagged the brute-force offenders. It worked on the sample log. Module 10 taught you to pin its
behaviour with `pytest`. But a unit test answers *"does this function do what I coded?"* — it does
not answer the question that actually matters for a detection tool: *"does it catch the attacks, and
how often does it cry wolf?"* Those are different questions, and the second one has a number. A regex
that flags `Failed password` will quietly miss the attacker who pivoted to valid-credential
spraying, and will quietly fire on the cron job that mistypes its own password twice a night — and
your unit tests, all green, will tell you nothing about either. The day a teammate "improves" the
regex and silently drops recall from 0.95 to 0.60, the demo still looks fine and nothing turns red.
This module is the discipline that makes a security tool *trustworthy*: a labelled corpus of real and
malformed log lines, a precision/recall scorecard instead of a vibe, and a CI gate that fails the
build the day a change degrades it. It is the same skill the AI-ops track applies to models — applied
here to the deterministic tools this whole track produces.

## Objective
Build an eval harness for a security tool you already wrote: assemble a **labelled, held-out** corpus
of log lines (true detections + benign near-misses + malformed input), choose and justify a
**metric**, score the tool into a **scorecard**, find the precision/recall knee deliberately, and
wire a **CI regression gate** that fails the build when a planted change degrades the score.

## The core idea

> **Your log parser flags brute-force attempts. Is it any *good*? Prove it.**
> Before reading on, write down how you would convince a skeptical SOC lead — with evidence, not
> adjectives — that your Module-02 parser catches the attacks that matter and doesn't drown them in
> false alarms. If your honest answer is "it worked on the sample log," you've just named the trap.

A detection tool is **not deterministic in the way that matters.** The *code* is deterministic, yes —
but the *space of inputs it will face* is not, and that is the thing you cannot eyeball. You tested it
on one log; production hands it a thousand variants you never saw. The move that makes the tool
trustworthy is not a cleverer regex — it is **measurement against a corpus the tool was never tuned
on, reported as a number, gated in CI.** That is the entire module, and it is the construct the rest
of this build-track has been doing by accident ("verify on positive *and* negative cases") without
ever naming.

**A labelled corpus is the spec your unit tests aren't.** A `pytest` assertion says "this input
yields this output." A *corpus* is a graded exam: dozens of log lines, each tagged `attack` or
`benign`, including the cases that *break* naive tools — the benign `cron` double-failure, the
Unicode-mangled line, the truncated entry, the slow-and-low spray that never trips a per-minute
threshold. You run the tool over the whole corpus and compare its verdicts to the answer key. The
corpus is **held out** from whatever sample you tuned the regex against — score on the data you
tuned on and the number is inflated by the same memorisation that makes the demo lie. (This is the
machine-learning train/dev/test split, and it transfers intact to a rule-based tool: tune the regex
against the dev log, *grade* it against a test corpus it has never seen.)

**Metric choice is a judgment, and accuracy is usually the wrong one.** Your corpus is imbalanced —
most log lines are benign — so a tool that flags *nothing* scores 95%+ "accuracy" while catching zero
attacks. The vocabulary you need is the confusion matrix — true/false positives and negatives — and
the two ratios built from it: **precision** (of the lines you flagged, how many were real attacks?)
and **recall** (of the real attacks, how many did you catch?). For a detection tool the load-bearing
number is usually **recall** — a missed intrusion costs a breach; a false positive costs an analyst a
few minutes — but recall bought at the price of a flooded alert queue is its own failure, which is why
you watch **precision** (and the false-positive rate) as the cost. The eval is what lets you find the
*knee* of that tradeoff on purpose instead of by feel: tighten the rule and recall drops; loosen it
and precision drops; the scorecard shows you exactly where.

**Coverage ≠ effectiveness.** A 500-line corpus is not better than a 40-line one if all 500 are easy
`Failed password` lines. Counting items is vanity; the corpus earns its keep by deliberately sampling
the *hard* cases — the near-misses that look like the other class, the malformed input that crashes a
brittle parser, the novel attack phrased unusually. The hand-built 40-line corpus that includes the
cases you *know* trip naive tools is worth more than a thousand auto-generated easy ones.

**The regression gate is what makes this engineering, not a one-off study.** The deliverable is a
**gate**: the eval runs in CI, and a change that drops recall below a declared floor **fails the
build** — exactly as a unit test fails on a broken function. The proof that the gate works is a
*planted regression*: you deliberately weaken the rule (so it under-detects), and the gate must turn
red and exit non-zero. A gate you have only ever seen pass is not a gate — you haven't shown it can
catch anything. The green-on-good / red-on-regressed contrast *is* the lesson; it's what lets a
teammate refactor the parser on a Friday without praying. Unit tests prove the code didn't *break*;
the eval gate proves the tool didn't get *worse*.

## Learn (~2.5 hrs)

**The confusion matrix & the metrics (~50 min)**
- [Wikipedia — "Precision and recall"](https://en.wikipedia.org/wiki/Precision_and_recall) — the canonical definitions with the 2×2 contingency table (TP/FP/FN/TN) and the worked classifier example; read down to the F-score section so the vocabulary your scorecard prints is precise. ~15 min.
- [Jason Brownlee — "Failure of Classification Accuracy for Imbalanced Class Distributions"](https://machinelearningmastery.com/failure-of-accuracy-for-imbalanced-class-distributions/) — *why* you don't gate on accuracy: the "accuracy paradox" where a do-nothing detector scores 99% on skewed data. Short and concrete; this is the single most important misconception this module fixes. ~15 min.
- [scikit-learn — "Metrics and scoring"](https://scikit-learn.org/stable/modules/model_evaluation.html) — the Python reference: read §3.4.4.6 (confusion matrix) and §3.4.4.9 (precision/recall/F-measure). You can reimplement these by hand in the lab (it's just counting), but this shows the `precision_score`/`recall_score`/`confusion_matrix` calls you'd reach for in a real harness. ~20 min.

**The harness mechanism in Python (~50 min)**
- [pytest — "How to parametrize fixtures and test functions"](https://docs.pytest.org/en/stable/how-to/parametrize.html) — `@pytest.mark.parametrize` is how you turn a labelled corpus into one test per item, so each corpus line is its own pass/fail; this is the bridge from the Module-10 test suite to a corpus-driven eval. ~20 min.
- [coverage.py docs](https://coverage.readthedocs.io/en/latest/) — read the intro and "Quick start": coverage measures *which lines ran*, which is the perfect foil for the "coverage ≠ effectiveness" idea — high line-coverage on easy inputs tells you nothing about detection quality. Use it to find untested branches, never as your quality metric. ~15 min.

**Wiring the regression gate (~30 min)**
- [GitHub Docs — "Building and testing Python"](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python) — how to run a Python script/pytest in GitHub Actions so a non-zero exit fails the PR; read the pytest section. This is the CI half of the gate — the part that makes the eval *block a merge* rather than sit in a notebook. ~15 min.

## Key concepts
- A unit test asks "does the code do what I wrote?"; an eval asks "does the tool catch the attacks, and how often does it cry wolf?" — different questions, and only the second has precision/recall.
- Labelled corpus vs. the sample you tuned on: grade on held-out data or every number is inflated by memorisation.
- Metric is a judgment: recall is load-bearing for detection (a miss is a breach), precision/FP-rate is the cost you pay for it; accuracy lies on an imbalanced corpus.
- The precision/recall knee: tighten the rule → recall drops; loosen it → precision drops. The eval finds the operating point deliberately.
- Coverage ≠ effectiveness — sample the hard near-miss and malformed cases, not just *more* easy lines.
- The regression gate: a planted weakening of the rule must fail the build — a gate you've only seen pass isn't a gate.

## AI acceleration
Have a model draft the mechanical parts — the confusion-matrix counting, the precision/recall/F1
arithmetic, the scorecard table, the argument parsing, the GitHub Actions YAML. That's boilerplate
and a model writes it well. **What you must own is everything a model will quietly get wrong here:**
the choice of metric (a model defaults to accuracy — you override it to recall and justify it against
the cost of a missed alert), the held-out discipline (a model will happily grade on the same lines it
"tested," and on the lines it *generated*; you enforce the wall), and the gate's direction and
fail-closed behaviour (does a missing metric or an erroring eval *fail* the build, or silently pass?).
Use a model to **expand the corpus with adversarial near-misses** — benign lines crafted to look like
attacks, attacks phrased to dodge the obvious regex — then **label every one yourself** and verify it,
because a model labelling its own test set is the contamination this whole module warns against. You
generate candidates; you own the ground truth.
