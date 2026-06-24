# Module 08 — SOAR + AI

*Type 7 · Build-&-Operate — wire an AI-assisted SOAR workflow with a human-in-the-loop gate that escalates on low confidence and never auto-acts on a model failure; the deliverable is the running workflow and its proven gate logic. (Secondary: Judgment-as-Code / Gate.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**AI-Augmented Security Operations** — *SOAR handles the routing and the record; AI handles the judgment call in the middle — and the gate decides what it is allowed to do unsupervised.*

<!-- module-meta -->
**Type:** Build-&-Operate + Judgment-as-Code / Gate (Family II) &nbsp;·&nbsp; **Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md), [Module 01 — The Hybrid AI Pattern](../01-hybrid-ai-pattern/README.md)
{ .module-meta }

## Why this matters

SOAR (Security Orchestration, Automation, and Response) platforms have been in enterprise SOCs for a
decade. They are excellent at deterministic workflows — *if alert X comes in, do steps A, B, C* — and
they break down on decisions that need contextual judgment: is this alert high-confidence enough to
auto-contain, or does it need a human approval? The temptation is to wire a model into that gap and
let it decide — *and then let it act*. That last step is where the danger lives.

On **August 1, 2012, Knight Capital deployed automated trading code to its routing servers** and, in
**45 minutes, sent more than 4 million unintended orders into the market, lost about $440 million, and
destroyed the firm**. The SEC's [2013 cease-and-desist order](https://www.sec.gov/litigation/admin/2013/34-70694.pdf)
found Knight "did not have technology governance controls and supervisory procedures sufficient to
ensure the orderly deployment of new code or to prevent the activation of code no longer intended for
use." It is not an AI story, but it is *the* automation story: an autonomous system that could take an
**irreversible action** at machine speed, with **no gate** between the decision and the action. SOAR +
AI is the same shape with a model in the loop — and the model is *less* deterministic than Knight's
code was. The job of this module is to build the workflow **and** build the gate that bounds it: a
model that can auto-contain a host unsupervised is a Knight Capital waiting to happen.

## Objective

Build and operate an n8n workflow that receives a webhook alert, routes it through a local Ollama
classification step, and branches on the result — auto-escalate, request human approval before
containment, or enrich-only — with an explicit failure branch. Then **encode the routing as a gate**:
a branch-logic test fixture (a labelled set of alerts → expected branch) that proves the decision
logic holds across alert types and that any low-confidence or model-down case **escalates, never
silently no-ops**.

## The core idea — the architecture, and the one judgment that bounds it

The architecture is a separation of concerns that plays to each component's strength. n8n owns the
workflow graph — the nodes, the branching, the connectors (ticketing, Slack, email), and the audit
trail of every step. Ollama owns one node: it calls the local model, returns a structured `{severity,
confidence}`, and hands it to the next branch. **The model is a worker inside the workflow, not the
orchestrator.** Its job is to emit a structured classification; n8n's job is to decide what to do with
it. That inversion is what keeps a non-deterministic component inside a deterministic frame.

The load-bearing judgment is **the human-in-the-loop threshold — what the AI is allowed to do without
a human, and what it must hand up.** It is not a technical setting; it is an operational policy, and
like the routing decision in [Module 01](../01-hybrid-ai-pattern/README.md), it is an **ADR-shaped
decision** — you write down the threshold, the options you rejected, and the consequences you accept.
The default split, mapped to recoverability:

- **LOW / MEDIUM** → enrich-only / standard queue. The action is recoverable; no human gate needed.
- **HIGH** → request approval before containment. Containment is *not* recoverable, so a human signs
  off first. The workflow genuinely **waits** for the approval — it does not proceed on a timeout.
- **CRITICAL** → auto-escalate immediately and log for human post-review. Waiting would lose minutes
  during active ransomware; the *escalation* is the action, and escalation is recoverable.

Notice what is missing: **the AI never auto-contains.** Containment — the one irreversible action — is
gated behind a human for HIGH and is never the model's unsupervised call. That is the Knight Capital
lesson encoded as policy: the faster and less deterministic the actor, the tighter the gate on its
irreversible actions.

The second judgment is the **failure mode**, and it is where SOAR + AI quietly betrays you. In a
Python script, a bad model response raises `json.JSONDecodeError` and you handle it. In n8n, an
expression error **silently takes the default branch** — which, if you built it naively, is "no
action," leaving a CRITICAL alert unescalated. So the rule is absolute: **model fails, or returns
low-confidence / unparseable output → escalate to human review. Never → no action.** "No AI →
escalate" is the safe failure; "No AI → no action" is the dangerous one. The branch-logic test fixture
exists to *prove* this holds — that a model-down case lands in the escalate branch, not the silent
default.

The audit trail is not optional. Every automated action taken on a model classification is logged
with: the original alert, the **full** model output (not just the severity), the action taken, the
timestamp, and the identity of any human approver. It is a compliance requirement (most IR frameworks
mandate an audit trail) and a quality-control mechanism — the log is what lets you review last month's
decisions and discover the model systematically over-classifies a particular alert type. It is also
how the branch-logic gate stays honest: the test reads the audit log to confirm each labelled alert
took its expected branch.

## Learn (~2.5 hrs)

**The anchor — automation without a gate (~30 min)**
- [SEC Order: In the Matter of Knight Capital Americas LLC (Release No. 70694, Oct 2013)](https://www.sec.gov/litigation/admin/2013/34-70694.pdf) — the primary source. Read sections III.A–III.C (the deployment and the 45 minutes) and the findings on inadequate controls. The phrase to carry into the lab: *no control prevented the irreversible action.*

**n8n foundations (~1 hr)**
- [n8n — Self-hosting with Docker](https://docs.n8n.io/hosting/installation/docker/) — skim the Docker section; `make up` does this for you, but understanding the container setup helps when the workflow breaks.
- [n8n — HTTP Request node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/) — the node that calls the Ollama API from inside the workflow; understand the Request settings and how its errors surface.
- [n8n — IF node (conditional branching)](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/) — the branching logic that splits CRITICAL → auto-escalate vs. HIGH → approval-required vs. LOW/MEDIUM → enrich.

**The over-automation risk (~30 min)**
- [OWASP Top 10 for LLM Applications — LLM06: Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) — the containment node *is* the excessive-agency risk; read the mitigation checklist (least-privilege actions, human-in-the-loop for high-impact operations). You'll cite it in the threshold ADR.

**Error handling in workflows (~30 min)**
- [n8n — Error handling (Error Trigger & error workflows)](https://docs.n8n.io/flow-logic/error-handling/) — how to make a node failure route somewhere explicit instead of silently dropping to a default. This is the mechanism behind "model fails → escalate."

## Key concepts

- **Model as a worker, not orchestrator** — structured `{severity, confidence}` feeds n8n's deterministic branching.
- **The HITL threshold is the load-bearing judgment** — what the AI may do unsupervised vs. what it hands up; an ADR-shaped policy decision (reference [Module 01](../01-hybrid-ai-pattern/README.md)), set by recoverability.
- **The AI never auto-contains** — containment is the irreversible action; it is gated behind a human (HIGH) and never the model's unsupervised call. The Knight Capital lesson as policy.
- **Fail-safe branch design** — model fails / low-confidence / unparseable → **escalate**, never → **no action**.
- **The branch-logic gate** — a labelled alert→branch fixture that proves the routing holds across alert types *and* that the model-down case escalates rather than silently no-ops.
- **Audit trail** — full model output + action + timestamp + approver; compliance requirement, QC mechanism, and the data the gate checks.
- **OWASP LLM06 (Excessive Agency)** — the containment node is where over-automation goes wrong.

## AI acceleration

Have a model help author the n8n workflow JSON — it can fill node configurations from a verbal
description faster than the UI. **What you own is the gate, not the JSON.** Two things the model will
get wrong if you let it: (1) it will route the *happy path* correctly and leave the failure branch
implicit — verify the "AI call fails" path explicitly goes to human escalation, not the default node;
(2) it will treat "wait for approval" and "proceed after a timeout" as interchangeable — they are not,
and a timeout-to-proceed turns your human gate into theatre. Then have a model **draft the
branch-logic test fixture** (the labelled alerts), but **label the expected branches yourself**: a
model writing its own answer key is the contamination Module 11 warns about. The model drafts the
JSON and proposes test cases; you own the branch semantics and the ground truth.
