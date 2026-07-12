# Lab 09 — Measure `sift`: Eval Harness, Property Tests & a Supply-Chain Gate

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/09-eval-property-supplychain/`: the hardened `sift` from Module 08,
plus a **held-out labelled corpus** (`evals/holdout.jsonl` — alerts with ground-truth benign/malicious
labels, generated separately from your tuning data), `pydantic-evals`, `hypothesis`, and `pip-audit`
pinned in the lockfile.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/09-eval-property-supplychain
make up       # build the container with the pinned eval + audit toolchain
make shell    # drop into sift with the held-out corpus mounted
make demo     # runs the full gate: eval scorecard + property tests + pip-audit + hash-locked install
make down     # stop when done
```

The lab **builds on the shipped `sift`** and adds a held-out corpus and three gates; it is reproducible at
zero cost. The corpus is deliberately kept in `evals/` and out of the tuning path so you can enforce the
held-out discipline yourself.

## Scenario

`sift` now makes judgments you can't eyeball at scale: a triage score per alert and an LLM verdict. Your
tests prove it *runs*; nothing proves it's *good*, and nothing stops a prompt or model swap from quietly
degrading it. You'll build the eval harness that measures triage quality against a held-out corpus and
gate it in CI, fuzz the M2 validator until it provably rejects all malformed input, and turn the M1
lockfile from a file into an enforced supply-chain control.

> Only test systems you own or have explicit written permission to test. Everything here runs locally in
> the lab container against the bundled corpus; the eval calls no external service unless you wire your own
> keys for the LLM verdict.

## Do

1. [ ] **Write the spec first.** Per the track workflow, spec this increment: the metric you'll optimize
   (precision/recall) and *why*, the pass thresholds, the validator property, and the two supply-chain
   gates. Name the held-out rule explicitly: the eval corpus is never used to tune.
2. [ ] **Load the held-out corpus as a `pydantic-evals` `Dataset`.** Turn `holdout.jsonl` into `Case`s
   (input alert → expected label). Confirm — in code or a comment — that nothing in your tuning/threshold
   path reads this file. Held-out means held out.
3. [ ] **Write a scorer and run the scorecard.** Add an evaluator that compares `sift`'s triage verdict to
   the expected label and reports **precision and recall** (not accuracy). Run it; read the number *after*
   you committed to which metric matters.
4. [ ] **Gate the eval in CI, then plant a regression.** Assert your justified thresholds (e.g.
   `precision >= 0.80`, `recall >= 0.90`) as a CI-failing check. Then deliberately break triage (loosen a
   rule, or swap in a worse prompt), watch the gate go **red**, and revert to green. You must demonstrate
   both.
5. [ ] **Fuzz the M2 validator with `hypothesis`.** Write a `@given` property that generates arbitrary
   input and asserts the validator *either* yields a well-formed `Alert` *or* raises `ValidationError` —
   never a half-parsed object, never any other exception. Let it find a case your example tests missed;
   fix the validator; keep the shrunk case as a regression test.
6. [ ] **Add the supply-chain gate.** Wire `pip-audit` over the **lockfile** into CI, and enforce a
   hash-locked install (`uv.lock` / `--require-hashes`). Prove it: introduce a known-vulnerable pinned
   version (or drift the lock) and watch the build fail; restore and confirm green.
7. [ ] **Automate & own it.** Commit `sift` v9 — the eval harness, the held-out corpus wiring, the property
   test, and both supply-chain gates, all in CI. In the PR, record the metric you chose and why, the bug
   `hypothesis` found, and one thing the copilot defaulted to that you had to correct (tuned on the
   held-out set, picked accuracy, or ran the audit against a loose `requirements.txt`).

## Success criteria — you're done when
- [ ] A held-out `pydantic-evals` `Dataset` scores `sift`'s triage on **precision and recall**, and the repo states the corpus is never tuned against.
- [ ] A CI regression gate asserts your justified thresholds and **fails on a planted regression** — you demonstrated red *and* green.
- [ ] A `hypothesis` property fuzzes the M2 validator; it found (or provably can't find) a malformed input the validator mishandles, and the shrunk case is a committed regression test.
- [ ] `pip-audit` runs over the lockfile in CI and a **hash-locked** install is enforced; both fail on a deliberate vulnerable/drifted dependency and pass when fixed.
- [ ] The metric choice (precision vs recall) is written down *with its rationale*, decided before the number was read.

## Deliverables
The `sift` v9 repository: `evals/` with the held-out corpus and the `pydantic-evals` `Dataset`/scorer, the
`hypothesis` property test and its shrunk regression case, the `pip-audit` + hash-locked CI gate, and the
increment spec noting the metric rationale and the held-out rule. Commit all of it. Do **not** commit any
real API keys, LLM outputs, or eval run artifacts beyond the curated corpus — reference them, don't check
them in.

## AI acceleration
Have the copilot draft the `Dataset`, the scorer, the `hypothesis` property, and the `pip-audit` CI step
from your spec — then review for what it skips. The high-value catches: did it tune thresholds against the
held-out corpus? did it default to accuracy where recall protects you? did the property carry an
`assume()` that swallows the interesting inputs? did the audit run against the lockfile or a loose file?
The copilot writes tests that pass; your job is to certify the eval measures the right thing and can't be
gamed.

## Connects forward
This is the eval framework **shared with Track 12 (AI Ops)**: here you eval *the tool* (`sift`'s triage);
there you eval *the AI system* — same held-out corpus → scorer → CI-gate shape, applied to prompts,
retrieval, and agent behavior. The supply-chain gate is the M1 lockfile finally enforced, and the property
test extends the *parse, don't trust* discipline from M2 and M7 onto the parser itself. `sift` is now the
capstone artifact: typed, validated, async, served three ways, red-teamed, and — as of this module —
measured, fuzzed, and pinned.

## Marketable proof
> "I build eval-as-code for non-deterministic security tooling: a held-out labelled corpus, a metric
> chosen on purpose, and a CI regression gate — plus `hypothesis` property tests fuzzing the input
> validator and a `pip-audit`/hash-locked supply-chain gate. My tools ship measured, not just passing."

## Stretch (optional)
- Add **model/prompt drift detection**: run the eval against two model versions and gate on the *delta*,
  not just the absolute threshold — catch degradation the day a provider updates.
- Reproduce the `torchtriton` class end-to-end: stand up a tiny private index, show an unpinned install
  resolving the public shadowing package, then show `pip-audit` + the hash-locked install refusing it.
