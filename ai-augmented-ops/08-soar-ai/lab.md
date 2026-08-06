# Lab 08 — SOAR + AI: Draft the Response, Then Gate What It Can Do

> **Hands-on lab.** Environment: `plaintext-labs/ai-augmented-ops/08-soar-ai`.
> Objective: **build an AI-augmented SOAR workflow that *drafts* a response and then proves it cannot
> auto-act** — a HIGH alert's containment is parked behind a human approval gate, a model-down alert
> fails safe to escalate, and a branch-logic gate proves both across every alert type. Target: **~2 hrs**,
> one finish line. Runs entirely on **local infrastructure you own** (n8n + Ollama + `tinyllama`, CPU-only).

---

## ✈ Flight card — the 7 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The model is a worker, not the orchestrator.** | It emits `{severity, confidence}`; **n8n** owns the branching, connectors, and audit trail. |
| 2 | **The AI never auto-contains.** | Containment is the one irreversible action — it is gated behind a human (HIGH), never the model's call. |
| 3 | **HIGH → draft, then PAUSE for approval.** | The workflow parks the response as `PENDING_APPROVAL`; it does **not** proceed on a timeout. |
| 4 | **Model fails / low-confidence / unparseable → escalate, never → no action.** | An n8n expression error silently takes the default branch — the dangerous failure is a silent no-op. |
| 5 | **The branch-logic gate is the deliverable.** | A labelled alert→branch fixture + a CI check that exits non-zero when the routing (or the fail-safe) regresses. |
| 6 | **Audit trail is not optional.** | Full model output + action + timestamp + approver — the compliance record *and* the data the gate reads. |
| 7 | **Knight Capital is the lesson.** | An autonomous system took an irreversible action at machine speed with no gate — ~$440M gone in ~45 min. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea-the-architecture-and-the-one-judgment-that-bounds-it) (the branch
> flowchart and the approval-gate lifecycle) and OWASP **LLM06 (Excessive Agency)** — the risk the gate exists to bound.

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A CRITICAL alert can auto-escalate but a HIGH alert cannot auto-contain. What is the one property of
   *containment* that forces it behind a human gate — and which real incident is the lesson?
2. In n8n, a node error **silently takes the default branch**. Why is "no AI → no action" the dangerous
   failure here, and what must the default branch be instead?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/08-soar-ai
make up
make import-workflow   # loads + activates the AI Alert Playbook in n8n
make demo              # fires a HIGH alert and shows the routing decision
```

**Requirements:** Docker, ~6 GB RAM free, no GPU. Two service containers start — **n8n** (workflow
engine, UI at http://localhost:5678, no login in local dev mode) and **Ollama** (local model). First
`make up` pulls `tinyllama` (~637 MB); later runs use the cache.

The lab ships two seed files you build on:

- **`data/ai-playbook.json`** — the importable n8n workflow: webhook → AI classify → parse → branch to
  **Auto Escalate (CRITICAL)** / **Approval Gate (HIGH)** / **Standard Queue (MEDIUM/LOW)**. The branch
  nodes write an audit entry whose `action_taken` field is `AUTO_ESCALATED` / `PENDING_APPROVAL` / `QUEUED`.
- **`data/alert-fixtures.json`** — a **labelled** set of alerts, each tagged with its `expected_branch`
  (`auto-escalate` / `require-approval` / `enrich-only` / `escalate`), plus `expected_decision`,
  `expected_confidence_band`, and a one-line `rationale`. It deliberately includes a **low-confidence**
  case (ambiguous alert → human review, never an unsupervised action) and a **model-down** case (AI node
  forced to fail → must fail safe to escalate, never the silent default). This is the answer key your
  gate scores against. The alert shape matches what `trigger.py` POSTs (`id`/`timestamp`/`host`/`title`/`description`).

> **▸ On track if:** `curl -s http://localhost:5678/healthz` returns `{"status":"ok"}` **and**
> `curl -s http://localhost:11434/api/tags` lists `tinyllama`. The n8n UI shows an **active** workflow
> named *AI Alert Playbook*.

> **Authorization note.** Everything here runs against **local infrastructure you own** — n8n and Ollama
> in Docker, no external targets. Later modules *attack* AI systems (Module 09 injects this very
> workflow); there the rule binds — only test systems you own or have written permission to test.

---

## Build it — read a little, do a little

### Part A — Build & operate the workflow

#### Step 1 — Watch a HIGH alert get *drafted, not taken*

**Concept (30 sec):** Flight-card #2–#3. The model classifies; n8n decides. A HIGH alert is likely
malicious, but containment is irreversible — so the workflow **drafts** a response and parks it for a
human, rather than acting.

**Do it:** `make demo`. In the output, find the raw alert, the classification (`severity` **and**
`confidence`), the routing decision, and the audit entry written to `results/audit-log.jsonl`.

> **▸ On track if:** the webhook response and the audit entry carry `"action_taken": "PENDING_APPROVAL"`
> — the response was **drafted and parked**, not `CONTAINED`. If you see any auto-containment for a HIGH
> alert, the gate is broken.

#### Step 2 — Read the workflow and name each node's job

**Concept (30 sec):** Flight-card #1. The model owns *one* node; n8n owns the graph, the branches, and
the audit trail.

**Do it:** open http://localhost:5678, open *AI Alert Playbook*, and trace it end to end:
- the **webhook** trigger — what path does it listen on (`/webhook/alert`)?
- the **AI Classify** HTTP node — what prompt does it send Ollama, and what JSON structure does it demand back?
- the **Parse Classification** code node — what does it do when the model returns unparseable text?
- the two **IF** nodes — trace CRITICAL → auto-escalate, HIGH → approval, else → standard queue.

> **▸ On track if:** you can point at the single node the model owns (**AI Classify**) and the node that
> owns the *decision to act* (the **IF** nodes) — and say why that separation is the whole design.

#### Step 3 — Prove three distinct branches

**Concept (30 sec):** Flight-card #2. Recoverability sets the gate: CRITICAL escalation is recoverable
(auto-act), HIGH containment is not (human), LOW/MEDIUM is enriched and queued.

**Do it:**
```bash
make trigger-critical
docker compose run --rm lab sh -c 'pip install -q requests 2>/dev/null && python3 scripts/trigger.py --severity LOW'
```

> **▸ On track if:** the CRITICAL run logs `"action_taken": "AUTO_ESCALATED"` and the LOW run logs
> `"action_taken": "QUEUED"` — three distinct `action_taken` values across `make demo`/critical/low,
> read from the field, not the prose.

#### Step 4 — Implement the fail-safe branch (model down → escalate)

**Concept (30 sec):** Flight-card #4. If the HTTP call to Ollama fails, the naive default is *no action*
— a CRITICAL alert could go unescalated. The rule is absolute: **model fails → escalate.**

**Do it:** in the n8n UI, add an explicit error path so that if **AI Classify** errors *or* the response
can't be parsed into `{severity, confidence}`, the flow routes to a **Manual Review Required** node that
writes an audit entry with `action_taken: "AI_UNAVAILABLE"`. Then `make export-workflow` to save your
change back to `data/ai-playbook.json`. Trigger with Ollama stopped to prove it fires:
```bash
docker compose stop ollama
make trigger-high
docker compose start ollama
```

> **▸ On track if:** with Ollama down, the newest `results/audit-log.jsonl` entry carries
> `"action_taken": "AI_UNAVAILABLE"` — a logged escalation, **not** a silent drop and **not** a
> workflow error with no audit entry at all.

### Part B — Build the branch-logic gate (the deliverable)

#### Step 5 — Own the answer key

**Concept (30 sec):** Flight-card #5. A label is *analyst judgment about the alert*, not a keyword match.
An alert with high model severity but **low confidence** is `require-approval`/`escalate`, never
`enrich-only` — acting confidently on a shaky call is the failure mode.

**Do it:** open `data/alert-fixtures.json`. Confirm each `expected_branch`, paying attention to the two
special cases: the **low-confidence** alert (must not route to an unsupervised action) and the
**model-down** alert (must route to escalate / `AI_UNAVAILABLE`). If you disagree with any label, change
it and write down why — you own the ground truth.

> **▸ On track if:** the fixture file contains at least one `expected_confidence_band: "low"` case and
> one `FORCE_AI_FAILURE` case, and you can state in one sentence why each must **not** end in an
> unsupervised action.

#### Step 6 — Run the gate green, then prove it catches a regression

**Concept (30 sec):** Flight-card #5. The gate POSTs every fixture through the running workflow, reads
the resulting `action_taken`, and asserts it equals the `expected_branch`. Green = the routing and the
fail-safe hold; red = a regression is caught *before* it ships.

**Do it:** build `scripts/branch_gate.py` (see **Automate & own it**), then:
```bash
docker compose run --rm lab sh -c 'pip install -q requests 2>/dev/null && python3 scripts/branch_gate.py'
```
It writes `results/branch-scorecard.md` (per-alert expected vs actual) and exits non-zero on any
mismatch. Then break it on purpose: in the UI, edit the HIGH IF node so HIGH falls through to
enrich-only (the classic "let the AI auto-resolve more to cut analyst load" mistake — which silently
removes the human approval before containment). `make export-workflow`, re-run the gate.

> **▸ On track if:** on the good workflow the gate **exits 0** and `branch-scorecard.md` shows every
> fixture in its `expected_branch`; after you break the HIGH routing it **exits non-zero** and the HIGH
> rows read `require-approval` (expected) vs `enrich-only` (actual). Judge by **exit code**, not by
> reading the log yourself.

---

## Prove the control (your finish line)

**One thing to demonstrate: the workflow *drafts* a response and cannot auto-act.** With the workflow
restored, produce two pieces of evidence and put them in `results/branch-scorecard.md`:

1. **The human gate holds.** A HIGH alert lands `action_taken: "PENDING_APPROVAL"` — the containment
   response was *drafted and parked for a human*, never `CONTAINED`. Break the HIGH routing and the gate
   goes **red**; restore it and the gate goes **green**. A "harmless" tuning tweak that removes the human
   gate is caught before it ships.
2. **The fail-safe holds.** The **model-down** fixture lands `AI_UNAVAILABLE` (escalate), and if you
   temporarily route the AI-fail case back to the default no-action node, that same fixture **fails the
   gate** — silent no-op is a gate failure by construction. Restore the fail-safe.

**The honesty check (the real finish line):** re-read `results/branch-scorecard.md`. **If the
low-confidence and model-down rows are absent or passing-by-accident, it's not done** — the gate only
earns its keep if it proves the dangerous failure modes (auto-acting on a shaky call; silently doing
nothing) cannot reach production unnoticed.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why is the model a "worker, not the orchestrator," and which component owns the decision to *act*?
2. Name the four branches and the `action_taken` value each writes — including the fail-safe.
3. An n8n expression error takes the default branch. What must that default be, and what real incident
   makes the point?

---

## Deliverables

`data/ai-playbook.json` (your exported workflow, **with** the fail-safe branch) +
`data/alert-fixtures.json` (the labelled fixture — including the low-confidence and model-down cases) +
`scripts/branch_gate.py` (the gate) + `results/branch-scorecard.md`. Commit all four. **The operating
playbook + the branch-logic gate are the artifact:** a working AI-augmented SOAR workflow *and* the
executable proof that its routing — and its fail-safe — hold across alert types. Do **not** commit raw
run dumps or live audit logs beyond the committed scorecard (`results/audit-log.jsonl` is gitignored; it
regenerates from the fixtures).

## Automate & own it

**Required.** The gate's value is that it runs on every change. Write `scripts/branch_gate.py` so it
can't be skipped: it reads `data/alert-fixtures.json`, POSTs each alert through the running workflow,
reads the resulting `action_taken` from `results/audit-log.jsonl`, maps it to a branch, compares to
`expected_branch`, and **exits non-zero on any mismatch**. Have a model draft the POST-and-poll logic;
**you own three things it will get wrong:** (1) it must **fail closed** — if the workflow never writes an
audit entry within a timeout, that's a *failure*, not a pass (verify by running the gate with n8n stopped
and confirming a non-zero exit, not a hang); (2) the **model-down** fixture passing means it reached the
*escalate* branch (`AI_UNAVAILABLE`), not that "no error was raised"; (3) the gate asserts the *exact*
expected branch, not merely "an action was taken." Commit the script and a captured run showing it red on
the broken-HIGH-routing regression and green when restored.

## Definition of done (`soar-ai` ✅)

- [ ] `make demo` routes a HIGH alert to `PENDING_APPROVAL` (drafted, **not** auto-contained) and writes an audit entry.
- [ ] `make trigger-critical` → `AUTO_ESCALATED` and a LOW alert → `QUEUED` — three distinct `action_taken` values, observed.
- [ ] The fail-safe branch is implemented: Ollama down → `AI_UNAVAILABLE`, never a silent drop.
- [ ] `scripts/branch_gate.py` exits **0** on the good workflow (all fixtures land in their `expected_branch`, including low-confidence and model-down → escalate) and **non-zero** after you break the HIGH routing.
- [ ] `results/branch-scorecard.md` shows the per-alert expected-vs-actual table, and you can explain all seven flight-card facts cold.

## Connects forward

The HITL threshold you set here is an **ADR-shaped decision** — write it up in the format from
[Module 01](../01-hybrid-ai-pattern/README.md) (Context · Options · Decision · Consequences), naming OWASP **LLM06 (Excessive
Agency)** in the Consequences. The workflow you build is also the orchestration layer that **Module 09
(Securing the AI You Run)** attacks with a prompt-injection payload — an alert crafted to flip the AI
classification and trip an auto-action. Your fail-safe branch and your branch-logic gate are both
mitigations: the gate becomes the regression test proving the injection stays fixed once you harden it.
The labelled fixture is a sibling of the held-out sets in [Module 11 (AI Evaluation)](../11-ai-evaluation/README.md) — same held-out +
scorecard + gate discipline, applied to branch logic.

## Marketable proof

> "I built an AI-augmented SOAR workflow in n8n — local-model classification feeding deterministic n8n
> branching, a human-in-the-loop approval gate before any containment, and a fail-safe branch that
> escalates to a human whenever the model is down or low-confidence. Then I built the branch-logic gate
> that proves it: a labelled alert→branch fixture and a CI check that fails when the routing regresses or
> the model-down case silently no-ops. The AI never auto-contains, and I can prove it."

## Stretch

- Add a second AI step after classification: a second Ollama call for the ATT&CK technique ID, used to
  attach the relevant runbook to the ticket. Add fixtures that assert the enrichment ran without changing
  the branch — enrichment must never silently upgrade an alert into an auto-action.
- Add retry-with-backoff on the Ollama HTTP Request node (up to 3 attempts, 5 s apart) *before* the
  fail-safe branch — then prove with the gate that the model-down fixture still escalates after retries
  exhaust, rather than the retries masking the failure.
- Express the threshold as config (a `thresholds.json` the workflow reads) and add a fixture that fails
  the gate if the config is edited to let the AI auto-contain — encoding "no unsupervised irreversible
  action" as a rule the team can't quietly relax.
