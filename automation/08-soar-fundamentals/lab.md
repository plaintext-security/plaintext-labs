# Lab 08 — SOAR Fundamentals

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate.** You build a working SOAR playbook (trigger → enrich → decide →
respond) in n8n, draw the human-in-the-loop gate yourself, and **operate it against four scenarios**
until it produces a sensible ticket for every one. The deliverable is the *operating playbook plus
its four-scenario test*, committed — not a writeup. No grader; you verify your own work against the
observable success criteria below.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/08-soar-fundamentals
make up        # starts n8n + mock threat-intel API + file-ticket backend
make demo      # fires a sample alert at the pre-loaded playbook via webhook and shows the output
make shell     # shell for manual curl testing
make down
```

Three containers: **n8n** (the SOAR platform) on port 5678, the **mock threat-intel API** (port
8080) that returns a verdict for a source IP, and a minimal **file-ticket backend** (Flask, port
8081) that accepts `POST /ticket` and writes a JSON file to `data/tickets/`. A starter playbook is
loaded into n8n on startup — inspect it at `http://localhost:5678`.

> n8n runs with `N8N_BASIC_AUTH_ACTIVE=false` for lab simplicity. **Never run n8n without
> authentication in production** — an unauthenticated SOAR platform is a remote-code-execution box
> wired to your firewall.

## Scenario
A SIEM is configured to fire a webhook at your playbook whenever a HIGH alert triggers. The playbook
must: receive the alert → enrich the source IP via threat intel → decide → create a ticket carrying
the verdict and a *recommended* action → log a notification. **A live analyst reviews the ticket; the
playbook does not take containment actions automatically** — that's the gate you're committing to (see
*The core idea*: reversible steps auto-run, the irreversible block waits for a human).

## Do

Build the four-stage playbook, then operate it against the four scenarios until none of them crashes.

**Build & operate the playbook**
1. [ ] `make demo` — watch the webhook fire, the n8n workflow run, and a ticket appear in
   `data/tickets/`. Read the ticket JSON: does it carry the alert data, the enrichment verdict, and a
   *recommended* action (not an executed one)?
2. [ ] Open n8n at `http://localhost:5678` and trace the playbook end to end. Identify the four
   stages: the **Webhook** node (trigger), the **HTTP Request** node (enrichment call to the
   threat-intel API), the **IF** node (the decision), and the node that **posts the ticket** (the
   response). For the IF node, state in one sentence: what verdict routes to *escalate* vs. *monitor*?

**Draw the gate — the design judgment**
3. [ ] Extend the decision: add a third route to the IF logic for an `"unknown"` verdict. An
   `unknown` IP should still create a ticket, but with `recommended_action: "investigate"` rather than
   `"escalate"`. (This is the gate in miniature — `unknown` is neither "ignore" nor "auto-act"; it's
   "put a human on it.")
4. [ ] Confirm the playbook *recommends* containment but never *executes* it. The ticket's job is to
   give the analyst a one-click decision; the irreversible block stays on the human side of the gate.

**Operate it against the four scenarios** — send each to the webhook URL (use `make shell` + `curl`):
5. [ ] **Happy path** — a malicious IP:
   `{"source_ip": "185.220.101.1", "alert": "brute force detected", "severity": "HIGH"}`
6. [ ] **Missing field** — no `source_ip`:
   `{"alert": "brute force detected", "severity": "HIGH"}` (the playbook must not crash on the null)
7. [ ] **Enrichment API down** — `docker compose stop threat-api`, then send a normal alert. The
   playbook must catch the failed lookup and still produce a ticket.
8. [ ] **Unknown verdict** — an IP the intel returns `unknown` for:
   `{"source_ip": "1.2.3.4", "alert": "port scan", "severity": "MEDIUM"}`
9. [ ] Confirm a ticket is created for **all four** (the API-down case writing
   `verdict: "enrichment_unavailable"`), then export the completed workflow to
   `data/playbook-v2.json`.

## Success criteria — you're done when
- [ ] All four scenarios produce a ticket in `data/tickets/` — none crashes the playbook, none is silently dropped.
- [ ] Every ticket JSON contains `source_ip`, `verdict`, `recommended_action`, and `timestamp`.
- [ ] The `unknown`-verdict scenario routes to `recommended_action: "investigate"`.
- [ ] The API-down scenario produces a ticket with `verdict: "enrichment_unavailable"`.
- [ ] No scenario results in an *executed* containment action — the playbook only ever *recommends*.

## Deliverables
Commit `data/playbook-v2.json` (exported from n8n) — the workflow JSON is the version-controlled
artifact; it *is* the playbook. **The operating playbook plus the four-scenario test is the
deliverable.** Do **not** commit `data/tickets/` (runtime output).

## Automate & own it
**Required.** Turn the four-scenario operation into a repeatable test: write `test_playbook.sh` that
sends all four curl requests in sequence (including the `docker compose stop threat-api` step) and
**validates** that the correct ticket was created for each — assert with `jq` that the happy-path
ticket has `recommended_action: "escalate"`, the unknown ticket `"investigate"`, and the API-down
ticket `verdict: "enrichment_unavailable"`. Have a model draft the curl commands and the `jq`
expressions, then **review every line and prove each assertion actually checks what it claims** — run
it once with a deliberately broken playbook and confirm the test *fails* (a test that can't fail
isn't a test). Commit `test_playbook.sh`. (AI drafts; you prove it catches a regression and you own
it.)

## AI acceleration
Describe the four-stage playbook (webhook → enrich → IF → ticket) to a model and ask it to generate
the n8n workflow JSON. Import it. Then operate it against the four scenarios and count: how many nodes
are missing? Does it handle the API-down path, the missing `source_ip`, the `unknown` verdict? The
model will hand you a functional happy-path workflow; the error-handling branches are the part you
add and test. The gaps in its workflow are the gaps in its model of how things fail — closing them is
the lab.

## Connects forward
The trigger → enrich → decide → respond playbook pattern is one half of the Track 10 capstone: a CI
pipeline that gates misconfigurations *before* deploy (Modules 03/05) and a SOAR playbook that
responds to alerts *after* — built from the components of every preceding module. The enrichment
stage reuses the data-pipeline work from Module 07.

## Marketable proof
> "I've built and operated a SOAR playbook end to end in n8n — webhook trigger, threat-intel
> enrichment, a human-in-the-loop decision gate that recommends rather than auto-contains, and
> conditional ticket creation — and tested it against four failure modes including a missing field
> and a downed enrichment API, with a scripted regression test."

## Stretch
- **Add a real human-approval gate.** Instead of auto-creating the ticket for an *escalate* verdict,
  write to a `pending_approval/` file (or send a chat message) and require a human "approve" before
  the response stage runs — the gate made explicit rather than implicit.
- **Score it (Type 13 Eval Harness).** Build a held-out, labelled corpus of alerts (each tagged with
  the *correct* escalate/monitor/investigate call), run the playbook over all of them, and compute its
  precision/recall on the routing decision — then wire a regression gate that fails if a changed
  playbook misroutes a previously-correct alert. Four hand-picked scenarios prove it *runs*; a scored
  corpus proves it's *accurate*. That measurement discipline is Module 09's whole subject.
