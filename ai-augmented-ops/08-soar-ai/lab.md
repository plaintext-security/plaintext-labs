# Lab 08 — SOAR + AI: Build the Playbook, Then Gate What It Can Do

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/08-soar-ai
make up && make demo
```

**Requirements:** Docker, 6 GB RAM free. Two containers start: n8n and Ollama.
`make up` starts both and imports the pre-seeded AI playbook workflow; the first run pulls
`tinyllama` (~637 MB). `make demo` fires a test HIGH-severity alert at the webhook and shows the
routing decision and the audit-log entry it produced.
Access the n8n UI at http://localhost:5678 (no login required in local dev mode).

The lab ships two seed files you build on:
- `data/ai-playbook.json` — the importable n8n workflow (webhook → AI classify → branch).
- `data/alert-fixtures.json` — a **labelled** set of alerts (each tagged with its expected branch:
  `auto-escalate` / `require-approval` / `enrich-only`), including a low-confidence case and a
  model-down case. This is the answer key your branch-logic gate scores against.

## Scenario

A SOC team wants to add an AI classification step to its alert-triage workflow. Today every alert goes
to manual review; analysts are drowning. The new workflow receives a webhook alert → the local model
classifies severity and confidence → **CRITICAL auto-escalates, HIGH requires approval before
containment, LOW/MEDIUM is enriched and queued.** Containment — the one irreversible action — is never
the model's unsupervised call.

The stakes are not hypothetical. On August 1, 2012, **Knight Capital** let an autonomous system take
an irreversible action at machine speed with no gate between decision and action — $440 million and the
firm, gone in 45 minutes. Your job is the opposite discipline: build the workflow, *then* build the
gate that proves it can't silently do the wrong thing — including when the model is down.

> Everything runs locally. No external services, no authorization needed.

## Do

### Part A — Build & operate the workflow

1. [ ] `make demo` — watch the workflow process a HIGH-severity alert. In the terminal output, find:
   the raw alert payload, the AI classification result (`severity` *and* `confidence`), the routing
   decision (did it go to the approval branch?), and the audit-log entry written to
   `results/audit-log.jsonl`. Note: HIGH did **not** auto-contain — it asked for approval first.

2. [ ] Open the n8n UI at http://localhost:5678 and view the `AI Alert Playbook` workflow. Find:
   - The webhook trigger node — what's the URL path?
   - The HTTP Request node that calls Ollama — what prompt does it send, and what structure does it
     ask the model to return?
   - The IF node(s) that branch on severity/confidence — what are the conditions? Trace each of the
     three branches to its terminal node.

3. [ ] Trigger a CRITICAL alert and confirm it routes *differently* than HIGH:
   ```bash
   make trigger-critical
   ```
   Confirm it took the auto-escalate branch (not approval) and logged to `results/audit-log.jsonl`.
   Then trigger a LOW alert (`make trigger-low`) and confirm it was enriched-and-queued, not escalated.

4. [ ] **Implement the failure branch (the fail-safe).** Currently, if the Ollama API is unreachable
   or returns unparseable output, the workflow silently takes the default branch (no action) — a
   CRITICAL alert could go unescalated. Add an explicit error path: if the HTTP Request to Ollama
   fails *or* the response can't be parsed into `{severity, confidence}`, route to a **"Manual Review
   Required"** node that logs the alert with status `AI_UNAVAILABLE`. Edit it in the n8n UI, then
   `make export-workflow` to save your changes back to `data/ai-playbook.json`. **Rule: model fails →
   escalate, never → no action.**

5. [ ] Trigger with Ollama stopped to confirm the failure branch fires:
   ```bash
   docker compose stop ollama
   make trigger-high
   docker compose start ollama
   ```
   Verify `results/audit-log.jsonl` has an entry with status `AI_UNAVAILABLE` — *not* a silent drop.

### Part B — Build the branch-logic gate (the deliverable)

6. [ ] **Read the labelled fixture and own the ground truth.** Open `data/alert-fixtures.json`. Each
   alert carries an `expected_branch`. Skim them: confirm each label is a *judgment about the alert*,
   not a keyword match — e.g. an alert with high model severity but **low confidence** should be
   labelled `require-approval` or `escalate`, not `enrich-only`, because acting confidently on a
   low-confidence call is exactly the failure mode. Two fixtures are special:
   - a **low-confidence** alert — must NOT route to an unsupervised action;
   - a **model-down** alert (the fixture forces the AI node to fail) — must route to escalate /
     `AI_UNAVAILABLE`, never to the silent default.
   If you disagree with any label, change it and write down why — you own the answer key.

7. [ ] **Run the branch-logic gate.** `make gate` POSTs every fixture through the running workflow,
   reads the resulting `results/audit-log.jsonl` entry, and asserts the **actual** branch equals the
   `expected_branch`. It writes `results/branch-scorecard.md` (per-alert: expected vs actual, pass/fail)
   and **exits non-zero if any alert took the wrong branch**. Run it on your good workflow and confirm
   it goes **green (exit 0)** across all alert types — auto-escalate, require-approval, and enrich-only
   all land where the labels say.

8. [ ] **Prove the gate catches a real regression (red).** Break the routing on purpose: in the n8n
   UI, edit the IF node so HIGH falls through to the enrich-only branch (the classic "let the AI
   auto-resolve more to cut analyst load" mistake — which silently removes the human approval before
   containment). `make export-workflow`, re-run `make gate`, and watch the HIGH fixtures fail and the
   gate go **red (exit 1)**. This is the whole point: a "harmless" tuning tweak that removes a human
   gate is caught *before* it ships, not after a wrong auto-containment.

9. [ ] **Prove the fail-safe under the gate.** With the workflow restored, confirm `make gate` reports
   the **model-down** fixture took the escalate / `AI_UNAVAILABLE` branch. Then temporarily revert your
   Part-A failure branch (route the AI-fail case back to the default no-action node), re-run `make
   gate`, and confirm the model-down fixture now **fails the gate** — silent-no-op is a gate failure,
   by construction. Restore the failure branch. The gate now encodes the non-negotiable: *no AI → escalate.*

## Success criteria — you're done when
- [ ] `make demo` processes a HIGH alert through the full workflow (approval-required, **not**
  auto-contained) and writes an audit-log entry.
- [ ] `make trigger-critical` routes to auto-escalate and `make trigger-low` routes to enrich-only —
  three distinct branches, observed.
- [ ] The failure branch is implemented: Ollama down → `AI_UNAVAILABLE` log entry, never a silent drop.
- [ ] `make gate` exits **0** on the good workflow (all fixtures land in their `expected_branch`,
  including low-confidence and model-down → escalate) and exits **1** after you break the HIGH routing.
- [ ] `results/branch-scorecard.md` shows the per-alert expected-vs-actual table.

*Honor-system self-check:* re-read `results/branch-scorecard.md`. If the **model-down** and
**low-confidence** rows pass, your gate proves the dangerous failure mode — silently doing nothing, or
acting unsupervised on a shaky call — cannot reach production unnoticed. If they're absent, the gate
isn't done.

## Deliverables
`data/ai-playbook.json` (your exported workflow, **with** the failure branch) +
`data/alert-fixtures.json` (the labelled branch-logic fixture — including the low-confidence and
model-down cases) + `scripts/branch_gate.py` (the gate) + `results/branch-scorecard.md`. Commit all
four. **The operating playbook + the branch-logic gate are the artifact**: a working AI-augmented SOAR
workflow *and* the executable proof that its routing — and its fail-safe — hold across alert types. Do
**not** commit raw run dumps or live audit logs beyond the committed scorecard (`results/audit-log.jsonl`
is gitignored; it regenerates from the fixtures).

## Automate & own it
**Required.** The gate's value is that it runs on every change. Wire `scripts/branch_gate.py` so it
can't be skipped: it reads `data/alert-fixtures.json`, drives each alert through the workflow, compares
the actual branch to `expected_branch`, and **exits non-zero on any mismatch**. Have a model draft the
POST-and-poll logic; **you own three things it will get wrong:** (1) it must **fail closed** — if the
workflow never writes an audit-log entry within a timeout, that's a *failure*, not a pass (verify by
running the gate with n8n stopped and confirming a non-zero exit, not a hang); (2) the **model-down**
fixture passing means it reached the *escalate* branch, not that "no error was raised"; (3) the gate
asserts the *exact* expected branch, not merely "an action was taken." Commit the script and a captured
run showing it red on the broken-HIGH-routing regression and green when restored.

## AI acceleration
Paste your exported workflow JSON into a frontier model and ask it to (1) identify any missing error
branches and (2) confirm the audit-log node records every required field (timestamp, alert ID, full
model output, action taken, approver). Compare its findings to your own review — where does it catch
something you missed, and where does it miss the *semantic* gap (a branch that runs without erroring
but routes a HIGH alert past the human gate)? Then have it **propose additional fixtures** for
`data/alert-fixtures.json` — adversarial alerts at the boundary between two branches — but **label the
expected branch yourself** against your threshold policy. The model expands coverage; you own the
answer key.

## Connects forward
The HITL threshold you set here is an **ADR-shaped decision** — write it up in the format from
[Module 01](../01-hybrid-ai-pattern/README.md) (Context · Options · Decision · Consequences), naming
OWASP **LLM06 (Excessive Agency)** in the Consequences. The workflow you build is also the
orchestration layer that **Module 09 (Securing the AI You Run)** attacks with a prompt-injection
payload — an alert crafted to flip the AI classification and trip an auto-action. Your failure branch
and your branch-logic gate are both mitigations: the gate becomes the regression test proving the
injection stays fixed once you harden it. The labelled fixture is a sibling of the held-out sets in
[Module 11](../../README.md) — same held-out + scorecard + gate discipline, applied to branch logic.

## Marketable proof
> "I built an AI-augmented SOAR workflow in n8n — local-model classification feeding deterministic
> n8n branching, a human-in-the-loop approval gate before any containment, and a fail-safe branch that
> escalates to a human whenever the model is down or low-confidence. Then I built the branch-logic gate
> that proves it: a labelled alert→branch fixture and a CI check that fails when the routing regresses
> or the model-down case silently no-ops. The AI never auto-contains, and I can prove it."

## Stretch
- Add a second AI step after classification: a second Ollama call for the ATT&CK technique ID, used to
  attach the relevant runbook to the ticket. Add fixtures that assert the enrichment ran without
  changing the branch — enrichment must never silently upgrade an alert into an auto-action.
- Add retry-with-backoff on the Ollama HTTP Request node (up to 3 attempts, 5 s apart) *before* the
  failure branch — then prove with the gate that the model-down fixture still escalates after retries
  exhaust, rather than the retries masking the failure.
- Express the threshold as config (a `thresholds.json` the workflow reads) and add a fixture that
  fails the gate if the config is edited to let the AI auto-contain — encoding "no unsupervised
  irreversible action" as a rule the team can't quietly relax.
