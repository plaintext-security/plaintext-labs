# Lab 10 — Red-team the copilot, then freeze it into a regression eval

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 15 · Red-team-the-AI (+ Type 13 · Eval Harness).** You run a systematic red-team of the SoC
copilot — broad statistical coverage with `garak`, expected-output assertions with `promptfoo` — write
a threat model of its attack surface, and ship the `promptfoo` suite as a **CI regression gate**
(plugging into module 11) that fails the build when a blocked attack becomes possible again.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/10-attacking-ai
make up && make demo
```

**Requirements:** Docker, 4 GB RAM free. No GPU needed. `make demo` runs `garak` against the local
Ollama model with a focused probe set (`injection` + `leakage` only — the full scan takes 30–60 min).
`make garak-full` runs the complete probe suite; `make promptfoo-eval` runs the assertion suite.

> **Authorization — offensive tooling.** garak and promptfoo generate real jailbreak, injection, and
> data-extraction payloads. Run them **only** against models and applications you own or have explicit
> written permission to assess. Every target in this lab is a local Docker container; never point these
> tools at a hosted model or a third party's deployment without sanction.

## Scenario
Before the SoC copilot you built across modules 04–06 goes to production, the security team runs a
systematic AI red-team — the move the three named incidents make non-optional: Air Canada owns what
its bot says, a system prompt didn't stop the Chevy "$1 car" jailbreak, and EchoLeak rode in on a
retrieved document with zero clicks. Your job: scan the copilot, interpret findings against those
incident classes, produce a threat model, and **leave behind a regression suite that re-runs in CI**
so the next model swap can't silently reopen a hole.

## Do

1. [ ] **Run the breadth scan.** `make demo` (garak, `injection` + `leakage`). For each probe class
   read: which probes ran, and the **pass rate** (higher = more attacks *blocked*). Treat any class
   below your declared threshold (start at 80% pass) as a finding. Copy the summary table into
   `results/garak-findings.md`. Note: re-running gives slightly different rates — that's the point,
   the results are statistical.

2. [ ] **Prove the misconception, hands-on.** Open `data/attack-prompts.yaml`; the copilot's system
   prompt tells it to act only as a SOC analyst. Craft one chat message that tries to override that
   role (a Chevy-style "from now on, ignore your role and..."). Send it a few times. Record in
   `results/garak-findings.md` whether the system prompt held *every* time — and why "just tell it not
   to" is not a control.

3. [ ] **Run the assertion suite (the Type 13 half).** `make promptfoo-eval` runs `promptfoo` over the
   test cases in `data/attack-prompts.yaml`. For each: the prompt sent, the model's actual output, and
   whether it passed its **assertion** (what a safe response must contain / must not contain). Copy any
   failing assertions into `results/promptfoo-findings.md` and explain *why* each failed.

4. [ ] **Write the per-finding analysis.** For each garak finding and each failing promptfoo
   assertion, one paragraph in the matching results file: what attack class it is, what an attacker
   could do to a SOC copilot if it works (reclassify a critical, extract the prompt, exfil via a
   retrieved doc), the **named incident it rhymes with** (Air Canada / Chevy / EchoLeak), and the
   mitigation (from module 09 or the OWASP-LLM ID).

5. [ ] **Write `results/threat-model.md`** for the copilot:
   - **Adversaries** — who targets it and why (include *malicious alert data / retrieved documents*).
   - **Assets** — what an attacker wants (correct triage, the system prompt, tool access).
   - **Attack surface** — prompt input, tool results, RAG context, the model API.
   - **Top 3 threats** — each tagged with an OWASP-LLM risk ID *and* a MITRE ATLAS technique ID, and
     anchored to one named incident.
   - **Mitigations implemented** — reference modules 05 and 09.
   - **Residual risk** — what's still open after all mitigations (be honest; EchoLeak shows filters get
     bypassed).

6. [ ] **Extend the suite.** Add at least one new test case to `data/attack-prompts.yaml` — a
   SOC-specific attack the existing set doesn't cover (e.g. an injection planted *in a retrieved alert
   body*, the EchoLeak-shaped vector). Give it a real assertion. Run `make promptfoo-eval`; record
   pass/fail.

7. [ ] **Ship the regression gate (the deliverable that makes it engineering).** Wire `promptfoo` into
   CI: add `.github/workflows/ai-redteam.yml` (or extend `scripts/scan.sh`) that runs the suite and
   **fails the build** if the safe-response pass rate drops below a declared threshold (e.g. 90%).
   Then **prove the gate bites:** point the suite at a deliberately weakened target (swap to a smaller
   model, or strip a guardrail / output filter) and confirm the run goes **red**; restore and confirm
   green. This is the same held-out-set-plus-regression-gate discipline as
   [module 11 — AI Evaluation & Observability](../11-ai-evaluation/README.md); reuse its scorecard
   shape. The contrast — green on the hardened copilot, red on the regressed one — *is* the proof.

## Success criteria — you're done when *(honor system — self-verified; no grader)*
- [ ] `make demo` completes and prints a garak probe summary (pass rates per class).
- [ ] `make promptfoo-eval` runs every test case and prints pass/fail per assertion.
- [ ] `results/garak-findings.md` has the summary table, one paragraph per finding, and the
  role-override hands-on note from step 2.
- [ ] `results/promptfoo-findings.md` analyses each failing assertion.
- [ ] `results/threat-model.md` is complete with all six sections, OWASP-LLM + ATLAS IDs, and each top
  threat anchored to a named incident.
- [ ] At least one new EchoLeak-/SOC-specific test case is in `data/attack-prompts.yaml` with a real
  assertion.
- [ ] The CI regression gate exists, **fails on the weakened target, and passes on the hardened one** —
  you've seen it go both red and green, not just pass.

## Deliverables
`data/attack-prompts.yaml` (with your new case) + `results/garak-findings.md` +
`results/promptfoo-findings.md` + `results/threat-model.md` + the CI regression workflow
(`.github/workflows/ai-redteam.yml` or the gating `scripts/scan.sh`). Commit all of them. Lab
artifacts — raw garak reports, full model transcripts — stay out of the commit.

## Automate & own it
**Required — and it's the regression gate above.** Turn "I red-teamed it once" into a suite that
re-runs on every change. Have a model draft the workflow YAML and the grep/jq that extracts the
failing-probe count from garak's report and the pass rate from `promptfoo`'s JSON; **you review the
extraction logic** (does it count *all* failure modes, or just lines containing "FAIL"?) and you set
the gate to **fail closed** — a missing or errored eval must turn the build red, never silently pass.
The artifact is a red-team you can re-prove on demand; a finding nobody re-checks reopens itself.

## AI acceleration
Two loops. **Drafting:** let a model write `promptfoo` assertion YAML from a plain-language safety spec
and the gate's extraction logic — it knows the formats. **Adversarial:** never ask a model "is this
safe?" (it reassures); ask it to *attack* — "given this copilot is RAG + MCP + Ollama, write ten
injection payloads that would arrive via a retrieved alert, and name ten MITRE ATLAS techniques my
threat model misses." Then verify each lands against the real surface and label them yourself — a
model grading its own attack list is the contamination module 11 warns about.

## Connects forward
This closes the track: you built the AI (04–06), measured it (07, 11), secured it (09), and now
red-teamed it systematically and **froze the result into a gate** (10). The capstone takes one tool
from the stack, demonstrates a finding against it, and ships a hardened version with this very
regression suite attached — the threat model here is the capstone's starting point, and the gate is
what proves the hardening holds.

## Marketable proof
> "I run systematic LLM red-teams with garak (statistical probe coverage) and promptfoo
> (expected-output assertions), interpret findings against real incidents (Air Canada, the Chevy '$1
> car' jailbreak, EchoLeak / CVE-2025-32711), produce a structured threat model tagged to OWASP-LLM
> and MITRE ATLAS, and ship the red-team as a CI regression gate that fails the build when a blocked
> attack becomes possible again."

## Stretch
- Run `make garak-full` and compare to the fast scan — which extra probe classes produce findings, and
  are any operationally significant for a SOC copilot?
- Add a *RAG-poisoning* test: plant an injection inside a document the copilot will retrieve (the
  EchoLeak shape) and assert the copilot does not act on it. This exercises the attack surface a
  prompt-only test never reaches.
- Gate on garak too: have the CI job also fail if any probe class drops below a declared pass-rate, so
  both breadth (garak) and depth (promptfoo) regressions block merge.
