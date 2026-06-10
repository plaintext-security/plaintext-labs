# Lab 15 — Cloud Logging & Detection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — the environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/15-cloud-logging-detection
make up       # build the lab container
make demo     # run the bundled detector against the seed CloudTrail events
make shell    # drop into the container for interactive work
make down     # stop when done
```

The environment is a Python 3.12 container with the detection script (`detect.py`) and all seed
data pre-loaded. No AWS account needed.

## Scenario
Meridian Financial's CloudTrail has been forwarded to your analysis workstation as a JSON export.
The CISO wants to know: what did the attacker do, how would GuardDuty have detected it, and where
would GuardDuty have been silent? Your job is to build detections for the gaps.

The seed data in `data/cloudtrail/events.json` contains 19 events spanning a normal workday plus
several attacker actions — including an unusual `AssumeRole`, a mass S3 download, a suspicious
user-agent on a sensitive bucket, a root login without MFA, and a `CreateUser` + `AttachUserPolicy`
admin escalation sequence. A sample GuardDuty finding JSON is in `data/guardduty-finding.json`.

> Only test systems you own or have explicit written permission to test. This lab uses
> bundled synthetic data; no real AWS account or credentials are involved.

## Do
1. [ ] **Map the events manually.** Open `data/cloudtrail/events.json` and skim all 19 records.
   Identify the events you consider suspicious. For each, note: the `eventName`, the
   `userIdentity.arn` or type, the `sourceIPAddress`, and why it looks anomalous. (Hint: look for
   API calls from unexpected IP ranges, unexpected regions, and unexpected user-agents.)

2. [ ] **Run the bundled detector.** `make demo` runs `detect.py` against the seed events. Note
   every finding it prints: rule name, severity, technique ID, and the triggering event details.
   Are there events you flagged in step 1 that the detector missed? Are there detector findings
   you didn't flag?

3. [ ] **Read the GuardDuty finding.** Open `data/guardduty-finding.json`. Which event from the
   CloudTrail seed data does this correspond to? What additional context does GuardDuty provide
   that isn't in the raw CloudTrail event (geolocation, ASN, threat intelligence enrichment)?
   What did GuardDuty *not* detect that the Python detector caught?

4. [ ] **Write your own Sigma rule.** Open `data/sigma_rule.yml` and read the bundled
   `CreateUser + AttachUserPolicy` rule. Now write a *new* Sigma rule for the suspicious
   `AssumeRole` from an unexpected region (the event at 09:20:15 from `eu-west-2`). Your rule
   should fire on `AssumeRole` where `awsRegion` is not in the expected set. Save it as
   `my_assumedrole_rule.yml` in the lab directory. (Hint: Sigma supports the `not` keyword and
   value lists in the detection condition.)

5. [ ] **Add your rule to `detect.py`.** Implement `rule_assumedrole_my_rule()` in `detect.py`
   (alongside the existing rules) and confirm it fires against the seed events with `make demo`.
   The existing `rule_assumedrole_unexpected_region()` function is the reference implementation —
   compare your Sigma logic to the Python logic and explain any differences.

6. [ ] **Compare detection approaches.** For each of the five rules in `detect.py`, write one
   sentence on whether GuardDuty would catch the same thing natively, and if not, why not. (Use
   the GuardDuty finding types list from the Learn path.)

## Success criteria — you're done when
- [ ] You can identify all five suspicious event categories in the seed data by hand.
- [ ] `make demo` fires findings for all five rules against the bundled events.
- [ ] You have written a Sigma rule (`my_assumedrole_rule.yml`) that is syntactically valid and
  correctly describes the detection logic.
- [ ] You can explain one case where GuardDuty provides coverage the Python detector doesn't, and
  one case where the open tool is needed.

## Deliverables
- `my_assumedrole_rule.yml` — your Sigma rule for the unexpected-region AssumeRole.
- `detection-analysis.md` — the comparison table from step 6: rule, GuardDuty coverage (Y/N),
  why the open tool adds/doesn't add value.

## Automate & own it
**Required.** Extend `detect.py` with a new rule of your choice — one not already implemented.
Ideas: flag `DeleteTrail` or `StopLogging` (T1562.008 — Impair Defenses: Disable Cloud Logs);
flag `CreateAccessKey` for a user you didn't create; flag `GetSecretValue` from Secrets Manager
outside business hours. Have a model draft the rule function. Before committing, manually verify
it fires against at least one event (add a synthetic event to the seed data if needed) and doesn't
fire on the benign events. You own the logic.

## AI acceleration
Describe your intended detection in plain English to a model: "I want to detect when someone calls
CreateAccessKey on a user other than themselves, from an external IP." Ask it to draft the Python
function body and the corresponding Sigma rule. Your job is to check: are the field names correct
against the actual CloudTrail JSON structure? Does the logic handle missing fields without
crashing? Does the false-positive section reflect your environment? Run it; fix it; own it.

## Connects forward
Module 16 (Cloud Incident Response) gives you a richer CloudTrail corpus — a full incident from
initial access to exfiltration — and asks you to build a timeline. The detection rules you wrote
here define what should have fired during the incident; the IR module asks you to explain why they
did or didn't.

## Marketable proof
> "I read raw CloudTrail JSON, write Sigma rules for sequence-based cloud attack techniques, and
> can articulate exactly where GuardDuty provides coverage and where open tooling fills the gap."

## Stretch
- Use the `sigma-cli` tool (installed in the container) to compile `data/sigma_rule.yml` to
  Splunk SPL: `sigma convert -t splunk -p sysmon data/sigma_rule.yml`. The output won't be
  perfectly valid for CloudTrail (Sysmon pipeline mismatch), but observe the structure and note
  what a proper CloudTrail Sigma pipeline would need to change.
- Extend `detect.py` to output its findings as structured JSON (one object per finding) rather
  than human-readable text. This makes it easy to feed findings into a downstream SIEM or alert
  management system.
