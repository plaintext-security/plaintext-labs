# Lab 08 — SOAR + AI

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/08-soar-ai
make up && make demo
```

**Requirements:** Docker, 6 GB RAM free. Two containers: n8n and Ollama.
`make up` starts both and imports the pre-seeded AI playbook workflow.
`make demo` fires a test HIGH-severity alert at the webhook and shows the routing decision.
Access the n8n UI at http://localhost:5678 (no login required in local dev mode).

## Scenario
Meridian's SOAR team wants to add an AI classification step to their alert triage workflow.
The current workflow routes all alerts to manual review. The new workflow: receives a webhook
alert → AI classifies severity → CRITICAL auto-escalates → HIGH requires approval → LOW/MEDIUM
goes to the standard queue. Your job: validate the workflow logic and implement the error branch.

> Everything runs locally. No external services, no authorization needed.

## Do

1. [ ] `make demo` — watch the workflow process a HIGH-severity alert. In the terminal output,
   find: the raw alert payload, the AI classification result, the routing decision (was it
   sent to the approval branch?), and the simulated containment log.

2. [ ] Open the n8n UI at http://localhost:5678 and view the `AI Alert Playbook` workflow.
   Find:
   - The webhook trigger node — what's the URL?
   - The HTTP Request node that calls Ollama — what prompt does it send?
   - The IF node that branches on severity — what's the condition?

3. [ ] Trigger the workflow manually with a CRITICAL alert:
   ```bash
   make trigger-critical
   ```
   Does it route differently than the HIGH alert? Does it log to `results/audit-log.jsonl`?

4. [ ] **Implement the error branch.** Currently, if the Ollama API is unreachable, the
   workflow takes the default branch (no action). Add an error branch: if the HTTP Request
   to Ollama fails, route to a "Manual Review Required" node that logs the alert with
   status `AI_UNAVAILABLE`. You can edit the workflow in the n8n UI and export it via
   `make export-workflow` to save your changes.

5. [ ] Trigger the workflow with Ollama stopped to confirm the error branch fires:
   ```bash
   docker compose stop ollama
   make trigger-high
   docker compose start ollama
   ```
   Verify `results/audit-log.jsonl` has an entry with `AI_UNAVAILABLE`.

## Success criteria — you're done when
- [ ] `make demo` processes a HIGH alert through the full workflow and produces an audit log entry.
- [ ] `make trigger-critical` routes to the auto-escalate branch (not the approval branch).
- [ ] The error branch is implemented: Ollama failure produces a `AI_UNAVAILABLE` log entry.
- [ ] `results/audit-log.jsonl` has entries for all test runs.

## Deliverables
`data/ai-playbook.json` (your exported workflow, with error branch) + `results/audit-log.jsonl`.
Commit both.

## Automate & own it
**Required.** Write `scripts/trigger.py` — a script that reads alert payloads from stdin (one
JSON object per line) and POSTs each to the n8n webhook, then waits for the audit log to show
the result. Have a model draft the polling logic; you review the timeout handling (what happens
if the workflow never writes to the audit log — does the script hang forever, or does it time out
gracefully?). Commit the script.

## AI acceleration
Paste the n8n workflow JSON into a frontier model and ask it to: (1) identify any missing error
branches, (2) check that the audit log node records all required fields (timestamp, alert ID,
model output, action taken). Compare its findings to your own review of the workflow. Where does
it catch something you missed?

## Connects forward
The SOAR workflow you build here is the orchestration layer that Module 09 will test with a
prompt-injection payload — an alert crafted to manipulate the AI classification step. The
error branch you implement is also a mitigation: it limits the blast radius when the AI node
is compromised or unavailable.

## Marketable proof
> "I built an AI-augmented SOAR workflow in n8n — local model classification with a human-in-the-loop
> approval gate, a failure branch that escalates to human review on AI errors, and a full audit trail."

## Stretch
- Add a second AI step: after the severity classification, send the alert to a second Ollama
  call asking for the ATT&CK technique ID. Use the technique ID to look up the relevant
  runbook and attach it to the ticket output.
- Implement rate limiting on the Ollama HTTP Request node: if the model returns a non-200
  response, retry up to 3 times with a 5-second delay before taking the error branch.
