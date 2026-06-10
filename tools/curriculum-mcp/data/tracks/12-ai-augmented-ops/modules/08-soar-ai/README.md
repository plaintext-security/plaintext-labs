# Module 08 — SOAR + AI

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *SOAR handles the routing and the record; AI handles the judgment call in the middle.*

## Why this matters
SOAR (Security Orchestration, Automation, and Response) platforms have been in enterprise SOCs
for a decade. They're excellent at deterministic workflows — if alert X comes in, do steps A, B, C
— but they break down on decisions that require contextual judgment: is this alert high-confidence
enough to auto-contain, or does it need a human approval? Traditional SOAR answers this with rigid
threshold rules (score > 80 → auto-contain). AI-augmented SOAR uses a model to make the judgment
call, keeping the deterministic routing and record-keeping that SOAR does well, and inserting AI
where a rigid rule would either miss too many threats or generate too many false-positive
containment actions.

## Objective
Build and trigger an n8n workflow that receives a webhook alert, routes it through a local Ollama
classification step, and either auto-escalates or requests human approval before proceeding to
a simulated containment action.

## The core idea
The architecture here is a separation of concerns that plays to each component's strength. n8n
handles the workflow graph — the nodes, the branching logic, the connections to external systems
(ticketing, Slack, email), and the audit trail of every step taken. Ollama handles the AI
classification step — a single node in the n8n graph that calls the local model API, gets a
severity and confidence back, and passes the result to the next branching node. The model is a
worker inside the workflow, not the workflow orchestrator. This is the right inversion: the
model's job is to output a structured classification; n8n's job is to decide what to do with it.

The human-in-the-loop step is the most important architectural element and the hardest to get
right. For LOW/MEDIUM alerts, the model's classification routes to an automated queue with no
human step. For HIGH alerts, the workflow sends a notification (Slack message, email, webhook)
and waits for an explicit approval before proceeding to containment. For CRITICAL alerts, the
workflow escalates immediately and logs for human post-review — waiting for approval would lose
precious minutes during active ransomware. The threshold between "auto-contain" and "require
approval" is an operational policy decision, not a technical one; the workflow enforces it, but
a human set it. Document your threshold choices.

One failure mode specific to SOAR + AI integration: the model returns an unexpected output format,
and the workflow either crashes or routes the alert incorrectly. Unlike a pure Python script where
a `json.JSONDecodeError` raises an exception you handle, an n8n expression error silently takes the
default branch — which might be "no action," leaving a CRITICAL alert unescalated. The n8n workflow
must have an explicit error branch that escalates to human review whenever the AI node fails or
returns unparseable output. "No AI → escalate to human" is the correct failure mode; "No AI →
no action" is the dangerous one.

The audit trail is not optional. Every automated action taken on behalf of a model classification
must be logged with: the original alert, the full model output (not just the severity), the
action taken, the timestamp, and the identity of any human approver. This is both a compliance
requirement (most security frameworks require incident response audit trails) and a quality
control mechanism — the log is what lets you review last month's model decisions and discover
that the model had a systematic bias toward over-classifying a particular alert type.

## Learn (~2 hrs)

**n8n foundations (~1 hr)**
- [n8n — Getting started with self-hosted n8n](https://docs.n8n.io/hosting/) — skim the Docker installation section; `make up` does this for you, but understanding the container setup helps when the workflow breaks.
- [n8n — HTTP Request node documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/) — the node that calls the Ollama API from within the workflow; understand the Request and Response settings.

**AI-augmented SOAR design (~30 min)**
- [OWASP Top 10 for LLM — LLM08 (Excessive Agency)](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — the containment automation node is the excessive-agency risk; read the mitigation checklist.

**Workflow design (~30 min)**
- [n8n — Conditional node documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.if/) — the branching logic that splits HIGH → approval-required vs. CRITICAL → auto-escalate.

## Key concepts
- Model as a worker, not orchestrator: structured classification output feeds n8n's branching logic
- Human-in-the-loop threshold: the operational policy that determines what needs approval
- Error branch design: model failure → escalate to human, never → no action
- Audit trail as compliance requirement and quality control mechanism
- OWASP LLM08 (Excessive Agency): the containment node is where over-automation goes wrong

## AI acceleration
Have a model help convert the n8n workflow JSON — it can fill in node configurations from a
verbal description faster than the UI. Your job is to verify the error branch (does the
"AI call fails" path go to human escalation?) and the approval logic (does the workflow
genuinely wait for approval before running containment, or does it proceed on a timeout?).
The model fills in the JSON; you own the error semantics.
