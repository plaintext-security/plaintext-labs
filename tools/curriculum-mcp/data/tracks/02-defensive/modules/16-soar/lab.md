# Lab 16 — Build a Response Playbook (Track Capstone)

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/16-soar
make up      # builds the Python SOAR harness
make demo    # runs all 3 test alerts through the 4-stage pipeline
make down
```

Bundled data: `data/alerts.json` (3 test alerts — true positive,
false positive, brute-force success) and `data/intel.json` (5 IP
verdicts). The `playbook.py` harness implements the four-stage SOAR
pattern in plain Python with explicit code for the human-gate
contract: no host is isolated and no network path is blocked without
human approval.

> **Authorization:** this lab simulates alert processing and
> containment actions only — no live firewall or host calls are made.

## Scenario
**This is the Track 02 capstone.** The SIEM has queued three alerts
from the March 15 incidents. Wire them through your response playbook
— enrich, score, route, ticket — and confirm the human gate fires
before any containment action is dispatched.

## Do

1. [ ] Run `make demo` (uses `--auto` to bypass the human gate in the
   demo environment). Read the three alert outcomes:
   - ALERT-001: why does the score reach 81?
   - ALERT-002: why is the score near 0 despite the same signature?
   - ALERT-003: what makes the brute-force score higher than the C2 alert?

2. [ ] Run `python3 playbook.py` (without `--auto`). When the human
   gate fires for ALERT-001, type `y` to approve containment. Type `N`
   for ALERT-003. Confirm the output matches — containment for 001,
   open case (no containment) for 003.

3. [ ] The triage step for ALERT-003 produces a firewall block against
   the *destination* (the internal server) instead of the *source*
   (the attacker). Fix `step_contain()` so it blocks `src_ip` on SSH
   and disables the account that was successfully brute-forced
   (`success_user` from `alert.additional`).

4. [ ] Run `python3 playbook.py --export` to see the YAML playbook.
   Add a sixth step to the YAML for `post_incident_note` — an action
   that posts a summary message to a Slack webhook URL with the alert
   ID, score, and containment status. Commit the updated YAML.

5. [ ] Add a fourth test alert to `data/alerts.json`: a medium-severity
   IDS hit against an IP that is not in `data/intel.json`. Trace the
   triage step — what score does it produce, and is the routing correct?

## Success criteria — you're done when
- [ ] You can explain why ALERT-002 suppresses while ALERT-001 escalates,
  with reference to the `step_triage()` scoring factors.
- [ ] The containment fix correctly blocks the attacker IP for ALERT-003.
- [ ] `--export` produces valid YAML you could import into Shuffle or Tines.

## Deliverables
`soar-playbook.md`: the three-alert trace (scores and routing), the
`step_contain` fix, and your new YAML step. Also commit the exported
`playbook.yaml` from `--export`. **This is the Track 02 capstone
artifact.**

## AI acceleration
Have a model draft the Slack-webhook YAML step and the fourth test alert
— then validate the routing decision manually before adding them.
A model can write the YAML schema; you verify the trigger conditions
match the actual scoring logic.

## Automate & own it
**Required.** The `playbook.yaml` export *is* the artifact — it
captures your pipeline as workflow-as-code. Wire the real
`step_human_gate` to send a Slack message with approval buttons
(AI drafts the webhook payload; you test it with `curl`). Commit the
updated script and `playbook.yaml` together so the pipeline is
reproducible from a single `git clone`.

## Connects forward
This capstone integrates modules 05 (IDS alerts), 06 (SIEM rules),
14 (threat-intel enrichment), and 13 (TheHive case management) into
one automated pipeline. The human-gate + AI-scoring pattern is the
foundation Track 12 (AI-Augmented Ops) builds on with MCP and RAG.

## Marketable proof
> "I build SOAR playbooks that automate alert enrichment, AI-assisted
> triage, and gated containment — the human stays in command, the
> toil is automated, and the pipeline is committed as workflow-as-code."

## Stretch
- Add a local-model triage step using the [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md):
  instead of the rule-based scorer, POST the enriched alert JSON to
  `http://localhost:11434/api/generate` with a system prompt that
  returns a 0–100 score and one-sentence reasoning. Compare the
  LLM score against the rule-based score on all three test alerts.
