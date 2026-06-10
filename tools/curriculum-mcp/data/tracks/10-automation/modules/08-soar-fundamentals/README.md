# Module 08 — SOAR Fundamentals

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *a playbook is repeatable; a human running the same steps for the fifth time this week is not.*

## Why this matters
Security Orchestration, Automation, and Response (SOAR) connects the tools a SOC uses —
SIEM, threat-intel APIs, ticketing systems, firewalls — into playbooks that can run the first
five minutes of an alert response automatically. The analyst arrives to a pre-enriched, pre-
triaged event with a recommended action, not a raw alert and a list of tabs to open. At
Meridian scale, this is the difference between 45-minute mean time to triage and 5-minute
mean time to triage.

## Objective
Build a SOAR playbook in n8n that receives a webhook alert, enriches the source IP via the mock
threat-intel API, creates a ticket (writes a JSON file), and notifies the analyst (logs to
stdout) — end to end, from webhook trigger to human-readable notification, without leaving the
lab environment.

## The core idea
SOAR platforms are essentially workflow engines with pre-built connectors to security tools.
The workflow model is: trigger → data enrichment → decision logic → response action. The trigger
is usually a webhook from a SIEM or alert platform; the enrichment queries threat-intel and
asset databases; the decision logic checks whether the alert meets the escalation threshold;
the response creates a ticket, sends a notification, or (with human approval) blocks an IP.

The human-in-the-loop gate is the hardest design decision in SOAR. Fully automated response
(auto-block an IP if VT score > 90) is fast but brittle — false positives block legitimate
traffic and create outages. Human-gated response (alert engineer, wait for approval, then block)
is safe but slow. The practical middle ground for most teams: automate everything up to the
containment action, create a ticket with a pre-filled "approve to block" button, and give the
analyst a one-click decision rather than a fifteen-step procedure. This module implements that
pattern: the playbook does everything up to the action, then creates a ticket that records
what action is recommended and why.

n8n is an open-source workflow automation platform with a visual editor, webhook triggers, and
built-in HTTP request nodes. It is a good learning platform because the workflow JSON is human-
readable (unlike some proprietary SOAR platforms), the nodes map directly to REST API calls
(which you understand from module 04), and it runs locally in Docker. The production
alternatives — Splunk SOAR, Palo Alto XSOAR, Tines, Torq — share the same mental model:
triggers, nodes, conditions, actions.

Workflow testing is more important than it sounds. A playbook that handles the happy path but
crashes on a null field in the alert payload will fail exactly when you need it most — during
a live incident. Test every playbook with: (1) a well-formed alert; (2) an alert with a missing
field; (3) an alert where the enrichment API is down; (4) an alert where the verdict is
"unknown." The playbook should produce a sensible ticket for all four.

## Learn (~2.5 hrs)

**SOAR concepts (~1 hr)**
- [What is SOAR? — IBM Security](https://www.ibm.com/think/topics/security-orchestration-automation-and-response) — a vendor-neutral overview of the SOAR category; read the "How SOAR works" and "SOAR vs SIEM" sections.

**n8n (~1.5 hrs)**
- [n8n — Getting started guide](https://docs.n8n.io/try-it-out/quickstart/) — work through the quickstart; understand workflow, node, and connection concepts.
- [n8n — Webhook node documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) — the trigger node used in this lab; understand how to get the webhook URL and how n8n passes the payload to subsequent nodes.
- [n8n — HTTP Request node documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/) — the node you'll use to query the mock API; understand authentication and response handling.

## Key concepts
- SOAR workflow: trigger → enrich → decide → respond
- Human-in-the-loop gate: ticket with recommended action vs. auto-execute
- Webhook trigger: the interface between SIEM and playbook
- n8n workflow JSON: human-readable, version-controllable
- Testing with four scenarios: happy path, missing field, API down, unknown verdict

## AI acceleration
n8n workflow JSON is verbose. Ask a model to generate the workflow JSON for a given playbook
description. Import it into n8n and test the four scenarios. A model-generated workflow will
usually handle the happy path but miss the error handling nodes — the "IF enrichment API is
down" branch. The gaps in the model's workflow are the gaps in its understanding of failure
modes; filling them is the learning.
