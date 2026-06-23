# Lab 09 — Detection-as-Code: the Scored Regression Gate

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/09-detection-as-code-pipelines
make up         # sigma-cli + pytest in Docker
make demo       # stage 1: sigma check (lint) over data/rules/  +  stage 2: pytest intent table
make eval       # the eval harness: scorecard over the HELD-OUT corpus + the regression gate (GREEN)
make gate       # proves the gate goes RED on the planted regression (exits non-zero)
make shell
make down
```

`data/rules/` ships five Sigma rules: four valid, one deliberately broken (a misspelled `condition:`
key that `sigma check` rejects). `data/tests/` carries the `conftest.py` matcher (`match_rule(rule, event)`)
and the per-rule **tuning** events — the set you write the `pytest` table against.

`data/heldout/` is the eval-harness layer this module adds. `data/heldout/corpus.jsonl` is a **held-out,
labelled** event corpus the rules were *never tuned on* — known-malicious events (including variants like
the `-enc` short form *and* the long `-EncodedCommand`) and known-benign lookalikes (a signed updater
writing a Run key, a `certutil -decode` by an installer, an EDR sensor's allow-listed LSASS read).
`data/heldout/rules-regressed/` is a deliberately **degraded** copy of the ruleset for the gate proof.
`eval.py` scores a ruleset against the corpus, prints a scorecard, and — with `--gate` — exits non-zero
on a regression. It reuses the **same** in-process matcher the `pytest` suite uses, so `make eval` is
deterministic and offline — no SIEM, no network. In real use you point `--corpus` at events exported
from your own SIEM.

> Honor system: the gate is a regression guard for *you*, not a grader. There is no answer key being checked.

## Scenario
A detection-engineering team runs a Sigma rule repo. The rules are in git and they pass review — and they
still rot. A "cosmetic" refactor drops a CommandLine variant; an over-broad selection floods the queue;
nobody notices until the alert that mattered never fires. Your job: gate the repo so a syntactically valid
rule cannot merge *broken in intent*, then make that measurable — score every rule against a held-out
corpus and fail CI the day the numbers regress.

> These rules detect attacker techniques but attack nothing — no authorization note needed. The events are
> recorded/synthetic Sysmon-shaped records, replayed offline.

## Do
1. [ ] `make demo` — watch stage 1 fail on the broken rule. Read the `sigma check` error: which rule, what
   syntax error? Fix the condition key in `data/rules/` and rerun `sigma check data/rules/` — confirm exit 0.
2. [ ] Read `data/tests/conftest.py` — understand `match_rule(rule, event)` and how it returns `True`/`False`.
   Write `data/tests/test_detections.py` with `pytest.parametrize` rows for all five rules. For each rule:
   one `(rule, malicious_event, True)` and one `(rule, benign_event, False)`. Run `pytest data/tests/ -v` —
   all 10 rows green. **This is your tuning set — passing it is necessary but not sufficient.**
3. [ ] Write `ci-gate.sh`: `sigma check data/rules/ && pytest data/tests/ -q`. Confirm it exits 0 on clean
   rules and 1 when a rule is broken. (This is the Type-8 gate; steps 4–7 add the Type-13 eval harness.)
4. [ ] **Read the held-out corpus.** Open `data/heldout/corpus.jsonl`. Note it is *separate* from your
   `pytest` events and richer: it carries the *variants* of each technique and the *near-miss benigns* your
   rules must NOT fire on. That wall — tuned-on vs. graded-on — is what makes the score honest.
5. [ ] **Score it.** Run `make eval`. Read the scorecard: the confusion matrix, then **recall** (caught
   attacks / all attacks) and **FP-rate** (benign that fired). Note that *accuracy* looks high even when a
   variant is missed — that is exactly why you watch recall, not accuracy, on an imbalanced corpus.
6. [ ] **Plant and catch a regression.** Run `make gate` (or `python3 eval.py --rules data/heldout/rules-regressed
   --gate recall=0.90`). The regressed ruleset dropped a CommandLine variant and over-broadened one selection;
   watch recall drop (missed attacks listed) and/or FP-rate climb, the gate go **RED**, and the process exit
   non-zero. Confirm the *good* ruleset (`make eval`) is **GREEN** at the same threshold.
7. [ ] **Tune toward the gate.** Pick one rule, deliberately widen or narrow it, re-run `make eval`, and read
   the scorecard move: which events did you newly catch or newly mis-fire on? Find the knee of the
   recall/FP-rate tradeoff *deliberately*, from the numbers — not by feel.

## Success criteria — you're done when
- [ ] All five rules pass `sigma check`; all 10 `pytest` rows (5 match + 5 no-match) pass.
- [ ] `ci-gate.sh` exits 1 on a broken rule and 0 when everything is clean.
- [ ] You have a **scorecard** over the **held-out** corpus — recall + FP-rate, not just "it fired in the demo."
- [ ] Your regression gate is **GREEN** on the good ruleset and you have *seen it go RED* on the planted
      regression (exits non-zero) — a gate you've only watched pass isn't a gate.
- [ ] You can explain why each false-positive row and each held-out near-miss proves the rule is *precise*,
      and why you grade on recall, not accuracy.

## Deliverables
Fixed `data/rules/<broken-rule>.yml` + `data/tests/test_detections.py` + `ci-gate.sh`, **plus the eval
harness**: the **held-out corpus**, **`eval.py`** (scorecard), and the **regression gate** (`make eval` /
`make gate` targets) — committed so a detection cannot silently regress. Lab *artifacts* (raw event dumps)
stay out of commits; the curated held-out corpus is committed on purpose.

## Automate & own it
**Required.** Don't stop at the two-stage gate — turn the ruleset into a **scored regression gate** so it
can't silently rot. Wire `eval.py` to score the rules against your **held-out corpus** and **exit non-zero
when recall drops below your floor (or FP-rate climbs past your ceiling)** — exactly as a unit test fails on
a broken function. Then add it as a third CI stage and prove it both ways: GREEN on the good rules, RED on
`data/heldout/rules-regressed/`. A model drafts the metric arithmetic and the scorecard table; **you own the
metric choice (recall on the malicious class, not accuracy), the held-out wall, and the gate's fail-closed
direction** (a broken eval must fail the build, not silently pass). Commit `eval.py` + the corpus + the gate
alongside the rules.

Then make CI run it: a GitHub Actions workflow (`.github/workflows/sigma-ci.yml`) that runs `sigma check`,
`pytest`, and `python3 eval.py --gate recall=0.90 --gate fp_rate=0.10` on every push and PR. Have a model
draft it; review — does it pin the action SHAs and the container version (tie to the repo's Actions
hardening)? Does it fail the PR when recall regresses? Commit the workflow.

## AI acceleration
Ask a model to write the false-positive `pytest` rows and a batch of *adversarial* held-out events — benign
activity crafted to look malicious (a signed updater touching a Run key; a base64 string in a PowerShell
arg that isn't `-enc`). Then **label each one yourself** against the real technique it mimics and verify
the rule's behaviour on it: the model's "benign" events are often subtly matching, and a model labelling
its own test set is the contamination this whole module guards against. You own the labels, the metric, and
the gate.

## Connects forward
This is detection-as-code, complete: rules in git, syntax-checked, intent-tested, **and measured** — scored
against a held-out corpus with a regression gate. It is automation's worked example of the **Eval Harness**
type ([ai-augmented-ops 11](../../../12-ai-augmented-ops/modules/11-ai-evaluation/README.md) applies the
identical shape to an AI triage model and a RAG). Combined with module 08 (SOAR), it is the full defensive
automation stack — rules that detect, playbooks that respond, an eval that proves the rules still work.

## Marketable proof
> "I gate Sigma rule changes in CI with `sigma check` for syntax and a `pytest` intent table — then I
> *measure* the rules against a held-out, labelled corpus and gate on recall and FP-rate, so a refactor
> that silently stops catching a variant turns the scorecard red and fails the build. A broken detection
> can't merge; a regressed one can't either."

## Stretch
- Add `sigma convert -t splunk` as a stage that compiles each rule and fails on an empty query — catching
  rules that are syntactically valid but logically empty after compilation.
- Track the scorecard over time: append each run's recall/FP-rate to a CSV and plot the trend, so you can
  *see* a detection decaying across commits — the offline analog of production observability.
- Expand the held-out corpus with a genuinely novel variant (a technique phrased a way no current event
  uses) and watch which rules miss it — coverage is not effectiveness until the hard cases are in the set.
