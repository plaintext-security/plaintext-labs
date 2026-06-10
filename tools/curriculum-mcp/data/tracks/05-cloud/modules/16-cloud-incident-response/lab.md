# Lab 16 — Cloud Incident Response

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — the environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/16-cloud-incident-response
make up       # build the lab container
make demo     # run triage.py and print the incident timeline
make shell    # drop into the container for interactive analysis
make down     # stop when done
```

The environment is a Python 3.12 container with `triage.py` and all data pre-loaded. No AWS
account needed. `data/cloudtrail/incident.json` contains 17 CloudTrail events spanning the full
attack chain. `data/vpc/flowlogs.csv` contains VPC flow log entries including large outbound
transfers to external IPs.

## Scenario
It is 08:45 UTC on 2024-11-14. Meridian Financial's SOC received a GuardDuty alert at 08:40 —
six hours after the fact — flagging an `UnauthorizedAccess:IAMUser/TorIPCaller` finding. Your job
is to reconstruct the full incident, determine what data was exfiltrated, identify whether the
attacker left any persistence mechanisms, and produce a timeline and IOC set for the executive
briefing in 90 minutes.

The CloudTrail trail was stopped at 02:18 UTC and re-enabled at 08:35 UTC by the SOC. You have
complete logs for 02:14–02:18 (the attack window) and from 08:30 onward (remediation).

> Only test systems you own or have explicit written permission to test. This lab uses
> bundled synthetic data; no real AWS account or credentials are involved.

## Do

1. [ ] **Triage the raw events yourself first.** Open `data/cloudtrail/incident.json` and work the
   incident by hand before running the bundled tool. Establish the attacker's source IP, the
   compromised principal, the event that stopped the trail, and the timestamp where the logging gap
   begins. How long was the gap? Then run `make demo` and use `triage.py`'s timeline as a check
   against what you found — what did you miss, and what did the tool miss?

2. [ ] **Reconstruct the attack chain.** Label each CloudTrail event with its kill-chain phase. The
   phases are: Initial Access → Enumeration → Privilege Escalation → Collection → Exfiltration →
   Defense Evasion → Persistence → Remediation. Assign the phase yourself from the event names and
   parameters, then cross-reference each against its ATT&CK technique ID to confirm your tagging.

3. [ ] **Identify the persistence mechanism.** The attacker created a second access key before
   stopping the trail. Find the event, note the new key ID, and explain: if the SOC had only
   disabled the original key (`AKIAIOSFODNN7EXAMPLE`), would the attacker still have access?
   What does the containment checklist in `triage.py` output say about this?

4. [ ] **Correlate with flow logs.** Look at the VPC flow log output from `make demo`. Identify
   the outbound flow(s) to the attacker IP `203.0.113.42`. What is the total bytes transferred
   outbound? What does the corresponding CloudTrail event tell you about what was transferred?
   What additional information does the flow log add that CloudTrail doesn't have?

5. [ ] **Assess the exfiltration scope.** The attacker accessed four objects in
   `meridian-financial-reports-prod`: three quarterly earnings reports and a compensation
   spreadsheet. They also added a bucket replication rule. Write a one-paragraph impact assessment:
   what data is confirmed exfiltrated (in CloudTrail), what data may have been exfiltrated via the
   replication rule before it was removed, and what is the regulatory notification implication
   (hint: financial data + compensation data + GDPR/state privacy law)?

6. [ ] **Extend `triage.py`.** Add a function `print_gap_analysis()` that detects when a
   `StopLogging` event is present in the CloudTrail data and calculates the duration of the
   logging gap (time between `StopLogging` and `StartLogging`). Print a warning with the gap
   duration. Run `make demo` and confirm the output includes the gap.

## Success criteria — you're done when
- [ ] You have a complete attack-chain table (phase, eventName, timestamp, technique ID) covering
  all attacker events in the timeline.
- [ ] You can name both access keys the attacker used or created, and confirm the containment
  checklist addresses both.
- [ ] Your gap analysis extension fires and prints the correct gap duration (approximately 6h 17m).
- [ ] Your impact assessment is written and addresses data confirmed exfiltrated, potential
  replication scope, and regulatory notification.

## Deliverables
- `timeline.md` — the attack chain table (phase, eventName, timestamp, technique ID, what it means).
- `impact.md` — the impact assessment from step 5.
- `triage.py` — updated with the gap analysis function from step 6.

## Automate & own it
**Required.** Extend `triage.py` with a `--json` flag that outputs the timeline and IOC set as
structured JSON rather than human-readable text. The output should be a single JSON object with
keys `timeline` (list of event objects), `iocs` (IPs, keys, principals, buckets, external
accounts), and `containment_checklist` (list of action strings). Have a model draft the
output-mode flag and the JSON serialisation. Before committing: run it, parse the output with
`python -c "import json,sys; json.load(sys.stdin)"` to confirm it is valid JSON, and verify the
`iocs` section contains all the attacker-associated keys and IPs from the incident. You own the
logic.

## AI acceleration
Paste the full timeline from `make demo` into a model and ask: "Based on this CloudTrail timeline,
what did the attacker access, what persistence mechanisms did they leave, and what containment
steps are missing?" Use the output as a second-opinion check against your own analysis in step 2–5.
Note any discrepancies — cases where the model misattributes a phase or misses a persistence
mechanism — and explain why your analysis is correct. This is the review discipline that keeps
AI-assisted IR from missing the subtleties.

## Connects forward
This module closes the cloud attack ↔ defence cycle that ran through modules 14–16. Module 14 gave
you the attacker's perspective and the CloudTrail signatures; module 15 gave you the detection
rules; this module gives you the IR workflow. The cloud capstone integrates all three: find the
attack path, close it as code, and build the detection that would have fired sooner.

## Marketable proof
> "I reconstruct cloud incidents from raw CloudTrail and VPC flow logs — timeline, IOC extraction,
> impact assessment, and containment checklist — and I can explain exactly where the detection gap
> was and how to close it."

## Stretch
- Feed the `data/cloudtrail/incident.json` to a real Hayabusa invocation (if you have it
  installed) using `hayabusa json-timeline -f data/cloudtrail/incident.json`. Compare its output
  to `triage.py`'s timeline. What does Hayabusa surface that `triage.py` misses, and vice versa?
- Write a second version of `triage.py` that queries the events using Athena-style SQL logic
  (using Python's `sqlite3` in-memory table). Load the CloudTrail records into a table and run
  `SELECT eventTime, eventName, sourceIPAddress FROM events WHERE sourceIPAddress = '203.0.113.42'
  ORDER BY eventTime` to reconstruct the attacker timeline. This mimics the CloudTrail → S3 →
  Athena pattern used in production IR.
