# Lab 19 — Review the Robot: Catching Subtly-Wrong AI Detections

*Hands-on lab · [← Back to the module concept](README.md)*

!!! warning "Lab environment status — to be built & validated (Phase 2)"
    The Docker environment for this lab is **not yet built or validated**. The `plaintext-labs/defensive/19-reviewing-ai-detections/`
    directory currently holds this `lab.md` and the build spec below; the `docker-compose.yml`, `Makefile`,
    seed data (the flawed AI-drafted artifacts + the labelled corpus), and `demo` target are **Phase 2 work**.
    Until `make up && make demo && make down` is green on a clean Linux runner, treat the commands below as the
    intended shape, not a tested path. (No `.ci-demo` marker is added until then — see the honor-system note in
    the repo's `CLAUDE.md`.)

## Setup
This will be a **reference lab** — a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Planned shape:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/19-reviewing-ai-detections
make up        # container with sigma-cli + the teaching matcher + the labelled corpus
make demo      # runs one flawed rule through fire-test (it doesn't fire) and shows the tell
make shell     # work inside the container
make down      # stop it
```

Planned contents:

- `ai-drafts/` — a batch of AI-drafted detection artifacts seeded with **N planted, realistic errors**:
  a few **Sigma rules** (one matching the wrong field; one whose modifier is wrong, e.g. `contains` where
  it needed `endswith`; one tagged with a **hallucinated ATT&CK ID**), one **log parser**
  (regex/VRL whose pattern silently drops a slice of real-world variant lines), and a set of **triage
  verdicts** in markdown (one that closes a ticket by over-trusting a year-stale IOC).
- `corpus/` — the labelled known-bad + known-good telemetry from the module-08/09 lineage, so every fix is
  *fired*, not just re-read. The malicious events have known ground-truth labels.
- The `sigma-cli` converter, the teaching matcher (`detect.py`), and `parse_check.py` (reports a parser's
  true line-coverage against the corpus, exposing silent drops).
- An **answer key** (`solution/findings.md`) sealed behind `make reveal` — don't open it until your own
  review is committed.

> Everything runs locally against bundled artifacts you own. No external targets, no authorization needed.

## Scenario
Meridian's SOC has started using an AI assistant to draft detections and triage tickets at volume — and
the backlog cleared overnight, which made everyone happy and nobody suspicious. Your lead, uneasy, hands
you the last batch the assistant produced and asks for a proper review *before* any of it goes live or any
of those tickets stay closed. Find what's wrong, prove it, fix it, and write the policy that decides what
gets re-verified next time — because the AI isn't going away.

## Do
1. [ ] `make demo` — watch one drafted rule get *fired* at the labelled corpus and **not** match the
   malicious event it claims to catch. That gap is the tell. Note that the rule converted and ran cleanly.
2. [ ] **Manual review pass.** Read every artifact in `ai-drafts/` and list each bug you find *before*
   firing anything. For each Sigma rule, check its field and modifier against the
   [Sigma spec](https://github.com/SigmaHQ/sigma-specification) and a real rule in
   [SigmaHQ/sigma](https://github.com/SigmaHQ/sigma); check every ATT&CK tag against
   [attack.mitre.org](https://attack.mitre.org). For the parser, eyeball the pattern for variant lines it
   won't handle. For the triage verdicts, check whether the deciding IOC is actually current.
3. [ ] **Fire-test every rule.** Run each Sigma rule against `corpus/` with the matcher. The wrong-field
   and wrong-modifier rules will fail to fire on their malicious target; that's the empirical tell that a
   clean read might miss.
4. [ ] **Coverage-test the parser.** Run `parse_check.py` — it reports the parser's real line-coverage.
   Confirm it's below 100% and identify which variant lines it silently drops.
5. [ ] **Verify the verdicts.** For the triage decision built on a stale IOC, check the indicator's age
   and confidence against the bundled intel; decide whether the AI's close/escalate call was right.
6. [ ] **Record each finding with the triad:** the **tell** (how you knew), the **primary-source proof**
   (what you checked it against), and the **fire-proof** (the rule now fires / the parser now covers 100% /
   the verdict is corrected). Then fix each artifact and re-run to prove the fix.
7. [ ] `make reveal` — compare your findings to the answer key. Did you catch them all? Did you flag a
   false positive (something that was actually fine)? Both are findings about *your* review.

## Success criteria — you're done when
- [ ] You found every planted error (cross-checked against `make reveal`), with the **tell** named for each.
- [ ] Each Sigma fix **fires** on its malicious target in `corpus/` and stays quiet on the benign events.
- [ ] The fixed parser reaches 100% line-coverage on the corpus (no silent drops).
- [ ] Every ATT&CK tag in your corrected rules resolves to a real technique on attack.mitre.org.
- [ ] The over-trusted triage verdict is corrected with the intel-age reasoning written out.
- [ ] You can articulate, in one sentence each, why each error was dangerous *and survived a casual read*.

## Deliverables
The **corrected artifacts** (`fixed/`), a **`review-findings.md`** (one entry per finding: tell →
primary-source proof → fire-proof), and a **`trust-checklist.md`** — the reusable policy stating what must
*always* be re-verified before AI-generated detection output ships (every field fired, every ID resolved,
every parser coverage-tested, every IOC age-checked). **Commit all three.** Do not commit the original
`ai-drafts/` edits or the corpus dumps.

## Automate & own it
**Required.** Turn the checklist into a **review gate**: a script (`review-gate.py`) that, given a Sigma
rule, mechanically enforces the parts that *can* be automated — convert + lint, fire it against the corpus
and fail if it doesn't match its tagged technique's known-bad sample, and resolve every ATT&CK tag against
a local ATT&CK ID list (fail on an unresolvable one). Wire it as a CI check so an AI-drafted rule can't
merge until it clears the gate. Have a model draft the gate; **you read every line**, confirm it actually
fails on the planted-bad fixtures and passes on the fixed ones, and own the thresholds. The gate encodes
*your* verdict so the next batch of AI rules can't regress past it.

## AI acceleration
Use a model to *review the model*: ask one to critique each `ai-drafts/` artifact for correctness. Then run
the three-way comparison — your manual findings vs. the reviewer-model's vs. what *firing it* revealed. Score
each: what did the model catch that you missed, what did you catch that it missed, what did the fire-test
catch that neither read found, and did the model invent a "bug" that wasn't real? That table is the honest,
empirical answer to "when can I trust AI to review detections" — and it usually shows that the fire-test, not
any reader, is the one that never lies.

## Connects forward
This is the track's `AI authors → you review → you own it` thread made into a whole lab — it backs the
"AI acceleration" box in every other defensive module. It reuses the labelled corpus from **module 09** and
the Sigma discipline from **module 08**, and the review gate is the same shape as **module 16 (SOAR)**'s
human-decision gate. The adversarial-review skill generalises straight into the AI-augmented-ops track,
where reviewing AI triage and RAG output is the daily job.

## Marketable proof
> "I don't ship AI-generated detections on faith — I fire every rule against labelled data, resolve every
> ATT&CK ID and field against the primary source, coverage-test every parser, and enforce it all in a CI
> review gate. The AI drafts; I prove it's correct before it goes live."

## Stretch
- Add a **regression corpus** to the review gate: a held-out set of previously-caught AI mistakes, so the
  gate fails if a new draft reintroduces an old failure mode (ties to the eval-harness type).
- Run the same batch through two different models and diff their drafts — measure which failure modes are
  model-specific vs. universal, and fold the universal ones into the trust checklist as "always check."
