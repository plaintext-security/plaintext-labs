# Lab 19 — Review the Robot: Catching Subtly-Wrong AI Detections

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/19-reviewing-ai-detections
make up        # container with sigma-cli + the teaching matcher + the labelled corpus
make demo      # one drafted rule converts cleanly, then fails to fire — the tell
make reveal    # unseal the answer key — only AFTER your own review is committed
make shell     # work inside the container
make down      # stop it
```

What ships:

- `ai-drafts/01..05_*.yml` — **five** AI-drafted Sigma rules. **Four carry a planted,
  realistic error; one (`05`) is correct** — the control. The planted errors are: a
  **wrong field** (`ProcessCommandLine` where this estate emits `CommandLine`), an
  **over-broad condition** (matches all `rundll32.exe`), a **fabricated ATT&CK ID**
  (`T1047.002`, which doesn't exist), and a **wrong logsource** (declares
  `process_creation` for an LSASS-access detection that is Sysmon EID 10
  `process_access`).
- `corpus/corpus.jsonl` — labelled known-bad + known-good telemetry (ground truth in
  `_label` / `_technique`), same lineage as modules 08/09, so every fix is *fired*,
  not just re-read.
- `attack/attack_ids.txt` — a local ATT&CK ID list so tag resolution is offline and
  deterministic.
- `review.py` — the teaching fire-test + ATT&CK-tag-resolution gate (wraps `sigma-cli`
  conversion + the matcher). `make review RULES="..."` fires your rules at the corpus.
- `solution/findings.md` — the **answer key**, sealed behind `make reveal`; don't open
  it until your own review is committed.

> Everything runs locally against bundled artifacts you own. No external targets, no authorization needed.

## Scenario
The SOC has started using an AI assistant to draft detections and triage tickets at volume — and
the backlog cleared overnight, which made everyone happy and nobody suspicious. Your lead, uneasy, hands
you the last batch the assistant produced and asks for a proper review *before* any of it goes live or any
of those tickets stay closed. Find what's wrong, prove it, fix it, and write the policy that decides what
gets re-verified next time — because the AI isn't going away.

## Do
1. [ ] `make demo` — watch draft `01` *convert to SPL with no error*, then get *fired*
   at the labelled corpus and **not** match the malicious events it claims to catch.
   Conversion passing is not correctness; that gap is the tell. The demo then reviews
   the whole batch.
2. [ ] **Manual review pass.** Read all five rules in `ai-drafts/` and list each bug
   you find *before* firing anything — and decide which one is the **control** (no
   bug). For each rule, check its field, modifier, and logsource against the
   [Sigma spec](https://github.com/SigmaHQ/sigma-specification) and a real rule in
   [SigmaHQ/sigma](https://github.com/SigmaHQ/sigma); check every ATT&CK tag against
   [attack.mitre.org](https://attack.mitre.org).
3. [ ] **Fire-test every rule.** Run the batch through the gate:
   `make review RULES="ai-drafts/*.yml"`. The wrong-field and wrong-logsource rules
   fail to fire on their malicious target; the over-broad rule false-positives on a
   benign event; the fabricated ATT&CK tag fails to resolve. Confirm each empirical
   tell a clean read might miss.
4. [ ] **Don't "fix" the control.** Confirm `05_encoded_powershell_correct.yml` fires
   2/2 malicious, 0 FPs, and its tag resolves — flagging the good rule is a false
   positive in *your* review.
5. [ ] **Record each finding with the triad:** the **tell** (how you knew), the
   **primary-source proof** (what you checked it against), and the **fire-proof** (the
   rule now fires / no longer FPs / the tag now resolves). Then fix each artifact into
   `fixed/` and re-run `make review RULES="fixed/*.yml"` to prove every fix.
6. [ ] `make reveal` — compare your findings to the answer key (`solution/findings.md`).
   Did you catch all four? Did you flag the control as broken? Both are findings about
   *your* review.

## Success criteria — you're done when
- [ ] You found all four planted errors (cross-checked against `make reveal`), with the **tell** named for each.
- [ ] You correctly left the control (`05`) alone — no false-positive "fix."
- [ ] Each fixed rule **fires** on its malicious target in `corpus/` and stays quiet on the benign events.
- [ ] Every ATT&CK tag in your corrected rules resolves against the ATT&CK ID list / attack.mitre.org.
- [ ] You can articulate, in one sentence each, why each error was dangerous *and survived a casual read*.

## Deliverables
The **corrected rules** (`fixed/`), a **`review-findings.md`** (one entry per finding: tell →
primary-source proof → fire-proof, plus a line on why you judged `05` the control), and a
**`trust-checklist.md`** — the reusable policy stating what must *always* be re-verified before
AI-generated detection output ships (every field fired, every modifier/logsource checked, every ID
resolved). **Commit all three.** Do not commit your `ai-drafts/` edits or the corpus dumps.

## Automate & own it
**Required.** The bundled `review.py` already fires rules and resolves ATT&CK tags —
turn the checklist into a **merge gate** on top of it: a wrapper that, given a Sigma
rule, exits non-zero unless it (a) converts + lints, (b) fires against the corpus and
matches its tagged technique's known-bad sample, and (c) resolves every ATT&CK tag
against `attack/attack_ids.txt`. Wire it as a CI check (a GitHub Actions step committed
alongside) so an AI-drafted rule can't merge until it clears the gate. Have a model
draft the wrapper + workflow; **you read every line**, confirm it actually fails on the
four planted-bad drafts and passes on your `fixed/` rules and the control, and own the
thresholds. The gate encodes *your* verdict so the next batch of AI rules can't regress
past it.

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
> ATT&CK ID and field/logsource against the primary source, and enforce it all in a CI review gate. The
> AI drafts; I prove it's correct before it goes live."

## Stretch
- Add a **regression corpus** to the review gate: a held-out set of previously-caught AI mistakes, so the
  gate fails if a new draft reintroduces an old failure mode (ties to the eval-harness type).
- Run the same batch through two different models and diff their drafts — measure which failure modes are
  model-specific vs. universal, and fold the universal ones into the trust checklist as "always check."
