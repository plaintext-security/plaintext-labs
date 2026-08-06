# Lab 09 — Measure `sift`: Eval Harness, Property Tests & a Supply-Chain Gate

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/09-eval-property-supplychain` (the
> hardened `sift` from Module 08, plus a **held-out labelled corpus** `evals/holdout.jsonl` — real Suricata
> `alert` events from the anchor capture, each hand-labelled true-positive / false-positive — with
> `pydantic-evals`, `hypothesis`, and `pip-audit` pinned in the lockfile).
> This is the **final** module: it adds no new stage — it **measures and hardens the whole `sift`** and
> locks the measurement into CI. Objective: **wrap `sift` in a held-out eval + regression gate, fuzz the M2
> validator, and enforce the M1 supply-chain gate — landing `sift` v9, the fully-measured capstone.**
> Target: **~2–3 hrs.** *Intermediate-plus: the steps state objectives; you derive the harness, property,
> and CI wiring (with the copilot).*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **This is the final module — it *measures* the whole `sift`.** | No new pipeline stage; the third edge of *parse, don't trust* — M2 typed input, M7 hardened the tool, M9 proves the system stays good. |
| 2 | **Held-out corpus, held out twice.** | Never tune against the eval set. Optimize against the thing measuring you and the score is a mirror, not an instrument. |
| 3 | **Metric on purpose: recall for triage.** | A missed true positive is a missed intrusion. "Accuracy" scores 98% by calling everything benign — it lies on imbalanced alert data. |
| 4 | **Eval gates, not vibes.** | "It felt fine" is not a merge criterion. A held-out number over a CI threshold is — and it catches drift the day a prompt/model/rule change lands. |
| 5 | **Property tests fuzz the boundary.** | `hypothesis` *generates* adversarial EVE and *shrinks* failures to a minimal counterexample — totality, not just the bad inputs you imagined. |
| 6 | **Supply-chain gate = the M1 loop, enforced.** | `pip-audit` + a hash-locked install fail the build on a vulnerable or drifted graph — the `torchtriton` tamper M1 named, finally refused. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea), the `pydantic-evals` docs for your pinned version, and the
> `torchtriton` primary source.

---

## Warm-up — answer before you build (2 min)

1. Why does tuning your thresholds against the eval corpus make the eval worthless — and how would you
   structure the repo so it *can't* happen by accident?
2. For alert triage where 98% of alerts are benign, why is "accuracy" the wrong metric, and when would you
   optimize recall over precision (and vice versa)?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/09-eval-property-supplychain
make up       # build the container with the pinned eval + audit toolchain
make shell    # drop into sift with the held-out corpus mounted
make demo     # the full gate: eval scorecard + regression gate + property tests + supply-chain hash
make test     # just the hypothesis/property tests
make down     # stop when done
```

> **Authorization note.** Everything runs locally in the lab container against the bundled corpus — the
> eval calls no external service unless you wire your own keys for the LLM verdict. Only test systems you
> own or have explicit written permission to test.

---

## Build it — objective, then a signal (intermediate-plus: you drive the commands)

### Step 1 — Write the spec first

**Concept (30 sec):** Flight-card #4. The spec is the contract you review the copilot's harness *against* —
and it's where you commit to the metric *before* the number can flatter you.

**Do:** spec this increment — the metric you'll gate on (recall) and *why*, the pass thresholds, the
validator property, and the two supply-chain gates. Name the held-out rule explicitly: **the eval corpus is
never used to tune.**

> **▸ On track if:** the spec names recall as the *gated* metric with its rationale, the thresholds, the
> totality property, and both supply-chain gates — not just "add tests."

### Step 2 — Load the held-out corpus as a `pydantic-evals` `Dataset`

**Concept (30 sec):** Flight-card #2. Each line of `evals/holdout.jsonl` is a real `alert` event + its
ground-truth label. Held out means held out — nothing on the tuning path may read this file.

**Do:** parse each held-out line through the **M2 boundary** (`AlertEvent` / union) into a typed `Case`
(input EVE alert → expected true-positive/false-positive label). Confirm — in code or a comment — that the
threshold/rule path never opens `holdout.jsonl`.

> **▸ On track if:** every held-out line parses to a typed `AlertEvent`, and the *only* reader of
> `holdout.jsonl` is the scorer — the classifier can't see its own answer key.

### Step 3 — Write a scorer and run the scorecard

**Concept (30 sec):** Flight-card #3. Read the number *after* you committed to which metric matters.

**Do:** add an evaluator that compares `sift`'s triage verdict to the expected label and reports
**precision and recall** (not accuracy). Run the scorecard.

> **▸ On track if:** `make demo` reports the scorecard over the ~21 held-out alerts — roughly
> **precision ≈ 1.00, recall ≈ 0.93** — and you can point to where you fixed recall as the gated metric
> before you read it.

### Step 4 — Gate the eval in CI, then plant a regression

**Concept (30 sec):** Flight-card #4. A scorecard you glance at once is a vanity metric; a *gate* bites.

**Do:** assert your justified thresholds (e.g. `recall >= 0.90`, `precision >= 0.80`) as a CI-failing check.
Then deliberately break triage (loosen a rule, or swap in a worse prompt), watch the gate go **red**, and
revert to green.

> **▸ On track if:** the CI gate **exits non-zero on a regressed `sift`** (recall drops below 0.90) and
> **zero on the good one** — you demonstrated both red and green.

### Step 5 — Fuzz the M2 EVE validator with `hypothesis`

**Concept (30 sec):** Flight-card #5. Your M2 example tests encode *your* imagination of bad input; the
adversary finds the input you didn't imagine.

**Do:** write a `@given` property that generates arbitrary EVE-shaped input and asserts the
`AlertEvent`/union validator *either* yields a well-formed event *or* raises `ValidationError` — never a
half-parsed object, never any other exception. Keep the canon malformed fixtures as regression tests.

> **▸ On track if:** the property survives thousands of generated inputs; a half-parse or stray exception
> **shrinks to a minimal counterexample** you can read, and the ~10 property/fixture tests stay green
> (`make test`).

### Step 6 — Add the supply-chain gate (close the M1 loop)

**Concept (30 sec):** Flight-card #6. The lockfile is only a control if CI fails when the graph drifts or a
known-vulnerable version slips in.

**Do:** wire `pip-audit` over the **lockfile** into CI, and enforce a hash-locked install (`uv.lock` /
`--require-hashes`; the reference stands in with a `sha256` digest gate on `requirements.lock`). Prove it:
introduce a known-vulnerable pinned version, or mutate the lock, and watch the build fail; restore and
confirm green.

> **▸ On track if:** `pip-audit` **fails the vulnerable pin**, and the hash-locked install **refuses
> drifted bytes** (the digest gate reports `✗ TAMPERED` on a mutated lock) — both green once restored.

---

## Prove the control (your finish line)

Commit **`sift` v9** and confirm every gate holds — a **regressed `sift` FAILS, the good one PASSES**:

- [ ] A held-out `pydantic-evals` `Dataset` scores `sift`'s triage on **precision and recall**, and the repo
  states the corpus is never tuned against.
- [ ] The CI regression gate asserts your justified thresholds and **fails on a planted regression** — you
  demonstrated red *and* green.
- [ ] A `hypothesis` property fuzzes the M2 `AlertEvent`/union validator; it found (or provably can't find)
  a malformed EVE input the validator mishandles, and the shrunk case is a committed regression test.
- [ ] `pip-audit` runs over the lockfile in CI and a **hash-locked** install is enforced; both fail on a
  deliberate vulnerable/drifted dependency and pass when fixed.
- [ ] The metric choice (precision vs recall) is written down *with its rationale*, decided before the
  number was read.

---

## Recall check — close the doc, answer from memory (3 min)

1. What does holding the corpus out actually protect — and how does a tuned-against eval become a mirror?
2. Why does the gate defend **recall** for triage, and what does accuracy hide on imbalanced alert data?
3. What does a `hypothesis` property catch about the validator that ten hand-written bad-payload tests
   cannot?

---

## Deliverables

The **`sift` v9** repository — `sift`, now fully measured: `evals/` with the held-out corpus and the
`pydantic-evals` `Dataset`/scorer, the CI **regression gate**, the `hypothesis` property test and its
shrunk regression case, the `pip-audit` + hash-locked supply-chain gate, and the increment spec noting the
metric rationale and the held-out rule. Commit all of it. Do **not** commit real API keys, LLM outputs, or
eval run artifacts beyond the curated corpus — reference them, don't check them in.

## Automate & own it

**Required — the gate *is* the automation.** Commit `sift` v9 with all three gates wired in CI, so a
regressed triage, an unhandled EVE input, or a vulnerable/drifted dependency turns the build red *without
you looking*. In the PR, record the metric you chose and why, the bug `hypothesis` found (and the shrunk
case), and one thing the copilot defaulted to that you had to correct — tuned on the held-out set, picked
accuracy, gave the property an `assume()` that swallowed the interesting inputs, or ran the audit against a
loose `requirements.txt` instead of the lockfile. The copilot writes tests that pass; your job is to
certify the eval measures the right thing and can't be gamed.

## Definition of done (`eval-property-supplychain` ✅)

- [ ] `sift` v9 is committed with a green CI gate over the held-out eval, the property tests, and the
  supply-chain checks.
- [ ] You demonstrated the regression gate **red on a regressed `sift`, green on the good one**, and the
  hash gate refusing a tampered lock.
- [ ] You can explain all six flight-card facts cold — especially why the eval is a *gate*, not a dashboard.

## Connects forward

This is the eval framework **shared with Track 12 (AI Ops)**: here you eval *the tool* (`sift`'s triage);
there you eval *the AI system* — same held-out corpus → scorer → CI-gate shape, applied to prompts,
retrieval, and agent behavior. The supply-chain gate is the M1 lockfile finally enforced, and the property
test extends the *parse, don't trust* discipline from M2 and M7 onto the parser itself. `sift` is now the
capstone artifact: typed, validated, async, served three ways, red-teamed, and — as of this module —
**measured, fuzzed, and pinned.**

## Marketable proof

> "I build eval-as-code for non-deterministic security tooling: a held-out labelled corpus, a metric chosen
> on purpose, and a CI regression gate — plus `hypothesis` property tests fuzzing the input validator and a
> `pip-audit`/hash-locked supply-chain gate. My tools ship measured, not just passing."

## Stretch (optional)

- Add **model/prompt drift detection**: run the eval against two model versions and gate on the *delta*,
  not just the absolute threshold — catch degradation the day a provider updates.
- Reproduce the `torchtriton` class end-to-end: stand up a tiny private index, show an unpinned install
  resolving the public shadowing package, then show `pip-audit` + the hash-locked install refusing it.
- **Dissector finale — prove the whole union is *total* (the thread's capstone rung).** The dissector
  thread has grown the EVE union stretch by stretch — `dns` (M2), `http` (M3), `tls`/`ja3` (M4),
  `flow`/`fileinfo` (M5). Now turn *this* module's skill back on the whole thing: write a `hypothesis`
  property asserting the dissector is **total over every EVE line** — each generated/real line either
  parses to a *known* event type **or** is quarantined, and it *never* crashes with an unhandled
  exception. Then add **drift detection over the event-type mix**: snapshot the distribution of dissected
  `event_type`s over the anchor `eve.json` and fail the build when a run surfaces a *new* or newly-frequent
  type your union doesn't model — the same regression-gate shape you built for triage, pointed at coverage.
  *Acceptance:* the property survives thousands of generated EVE-shaped inputs (partial dissection = a
  bug), the quarantine path is exercised by an unmodelled `event_type`, and the drift gate goes red when
  you feed it an `event_type` outside the snapshot and green once the union (or the snapshot) accounts for
  it. This closes the growing union the dissector thread opened in M2. *(Objective only — derive the
  property and the snapshot yourself; no transcribed solution.)*
