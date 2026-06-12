# Lab 08 — SOAR Fundamentals

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/08-soar-fundamentals
make up        # starts n8n + mock threat-intel API + file-ticket backend
make demo      # triggers the pre-loaded Meridian workflow via webhook and shows output
make shell     # shell for manual curl testing
make down
```

Three containers: **n8n** (the SOAR platform) on port 5678, the **mock threat-intel API** (port
8080), and a minimal **file-ticket backend** (Flask, port 8081) that accepts `POST /ticket` and
writes a JSON file to `data/tickets/`. `data/meridian-workflow.json` is pre-loaded into n8n on
startup as the Meridian incident playbook — inspect it at `http://localhost:5678`.

> n8n runs with `N8N_BASIC_AUTH_ACTIVE=false` for lab simplicity. Never run n8n without
> authentication in production.

## Scenario
Meridian's SIEM is configured to send a webhook to your playbook whenever a HIGH alert fires.
The playbook must: receive the alert → enrich the source IP → create a ticket with the verdict
→ log a notification. A live analyst will review the ticket; the playbook does not take
containment actions automatically.

## Do
1. [ ] `make demo` — watch the webhook fire, the n8n workflow execute, and the ticket appear in
   `data/tickets/`. Read the ticket JSON — does it contain the alert data, the enrichment
   verdict, and a recommended action?
2. [ ] Open n8n at `http://localhost:5678` and inspect the Meridian workflow:
   - Identify the Webhook node (the trigger), the HTTP Request node (the enrichment call),
     the IF node (verdict check), and the Write File node (the ticket).
   - For the IF node: what condition routes to "escalate" vs. "monitor"?
3. [ ] Modify the workflow: add a second outcome to the IF node for `"unknown"` verdicts —
   create a ticket but with recommended action `"investigate"` rather than `"escalate"`.
4. [ ] Test the four scenarios by sending curl requests to the webhook URL:
   - Happy path: `{"source_ip": "185.220.101.1", "alert": "brute force detected", "severity": "HIGH"}`
   - Missing field: `{"alert": "brute force detected", "severity": "HIGH"}` (no `source_ip`)
   - API-down scenario: `docker compose stop threat-api` then send a normal alert
   - Unknown IP: `{"source_ip": "1.2.3.4", "alert": "port scan", "severity": "MEDIUM"}`
5. [ ] Confirm a ticket is created for all four scenarios (even if the ticket says "enrichment
   unavailable" for the API-down case).
6. [ ] **Add the human-in-the-loop containment gate and prove it holds (the build half).** A
   ticket is a recommendation; a *containment action* (block the IP) must never fire automatically.
   Extend the workflow: for a HIGH-severity malicious verdict, instead of acting, write the proposed
   action to `data/pending_approval/<alert-id>.json` and stop. Add a second entry path — an
   `approve` webhook (or a node that reads an `approved/` directory) — that performs the containment
   by writing `data/containment/block-<ip>.json`. Now **prove the gate**: send a HIGH malicious
   alert and confirm a `pending_approval/` record appears and **no** `containment/` artifact exists;
   then approve and confirm the `containment/` artifact is created. The auto path stops at the gate;
   only an approved action contains.
7. [ ] Export the completed workflow as `data/meridian-workflow-v2.json`.

## Success criteria — you're done when
- [ ] All four test scenarios produce a ticket in `data/tickets/`.
- [ ] The ticket JSON contains `source_ip`, `verdict`, `recommended_action`, and `timestamp`.
- [ ] The "unknown" IP scenario routes to `recommended_action: "investigate"`.
- [ ] The API-down scenario creates a ticket with `verdict: "enrichment_unavailable"`.
- [ ] A HIGH malicious alert produces a `pending_approval/` record and **no** `containment/` artifact
  until you approve; after approval, the `containment/block-<ip>.json` artifact is created.

## Deliverables
`data/meridian-workflow-v2.json` (exported from n8n). Commit it — the workflow JSON is the
version-controlled artifact. Do not commit `data/tickets/` (runtime output).

## Automate & own it
**Required.** Write a `test_webhook.sh` script that sends all four test curl requests in
sequence and validates that the correct ticket files were created (check the `recommended_action`
field in each). Have a model draft the curl commands and the jq validation expressions; verify
each validation actually checks what it claims. Commit `test_webhook.sh`.

## AI acceleration
Describe the four-node playbook (webhook → enrich → if → ticket) to a model and ask it to
generate the n8n workflow JSON. Import it into n8n. How many nodes are missing? Does it handle
the API-down error path? The model will produce a functional happy-path workflow; the error
handling nodes are the part you add and test.

## Connects forward
The n8n playbook pattern is the capstone integration for Track 10: a pipeline that gates
misconfigurations in CI and a SOAR playbook that responds to alerts — built from the individual
components of every preceding module.

## Marketable proof
> "I've built a SOAR playbook from scratch — webhook trigger, API enrichment, conditional
> routing, ticket creation, and tested against four failure modes including the API-down case —
> using n8n in Docker."

## Stretch
- Make the approval real-time: replace the `approved/`-directory poll with a Slack interactive
  message (or an n8n Wait-for-webhook node) so the analyst approves with one click, and record the
  approver identity + timestamp in the containment artifact (the audit trail of who authorised it).
- Add an auto-expiry: if a `pending_approval/` record isn't approved within N minutes, the playbook
  writes a `expired/` record and notifies — so a gate that's never answered fails closed, not open.
- Version the workflow by committing `meridian-workflow-v2.json` and diffing it against v1
  — this is detection-as-code for SOAR playbooks.
