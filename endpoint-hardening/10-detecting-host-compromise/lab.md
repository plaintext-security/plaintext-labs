# Lab 10 — Detecting Host Compromise

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/10-detecting-host-compromise
make up        # build the container with sigma-cli and alert data
make demo      # match Sigma rules against the sample Wazuh alert JSON
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally against bundled alert data. No Wazuh manager required for this lab.

## Scenario

Meridian Financial's SIEM team has triaged a suspicious host and pulled the Wazuh alert stream
from the last 24 hours. The alerts are in `data/alerts.json`. Three attack phases are
represented: a persistence mechanism being installed, a credential access attempt, and lateral
movement via SSH. Your job: write Sigma rules that fire on each phase, run them against the
alert data, and map the coverage to ATT&CK.

## Do

1. [ ] `make demo` — watch sigma-cli match the pre-built example rule against the alert JSON.
   Note: which alert matches, what the matching fields are, and what ATT&CK technique is
   tagged on the rule.

2. [ ] `make shell` and browse the alert data:
   ```bash
   cat /lab/data/alerts.json | jq '.[] | {id: .id, rule: .rule.description, data: .data}' | less
   ```
   Identify the three attack-phase alerts (look for descriptions containing "cron", "shadow",
   "ssh"). Note the fields available in each alert.

3. [ ] Write a Sigma rule for the **persistence** alert (cron-based persistence,
   ATT&CK T1053.003). Save it as `rules/persistence-cron.yml`. The logsource should match
   Wazuh's syslog/auditd format. Key fields: `data.audit.exe` containing `crontab`,
   `data.audit.key` or `rule.description` matching the cron modification.

4. [ ] Write a Sigma rule for the **credential access** alert (`/etc/shadow` read attempt,
   ATT&CK T1003.008). Save it as `rules/credential-shadow.yml`.

5. [ ] Write a Sigma rule for the **lateral movement** alert (SSH with new key,
   ATT&CK T1021.004). Save it as `rules/lateral-ssh.yml`.

6. [ ] Test all three rules against the alert data:
   ```bash
   sigma-cli match --target wazuh --format json \
     rules/persistence-cron.yml /lab/data/alerts.json
   # Repeat for each rule
   ```
   Confirm each rule fires on exactly the intended alert and no benign ones.

7. [ ] Map your three rules to the [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/):
   create a layer JSON file (`coverage.json`) marking T1053.003, T1003.008, and T1021.004
   as covered (score: 1). This is your detection coverage artefact.

## Success criteria — you're done when

- [ ] Three Sigma rules, each firing on exactly the intended alert in `alerts.json`.
- [ ] No false positives on the benign alerts in `alerts.json`.
- [ ] Each rule tagged with the correct ATT&CK technique ID.
- [ ] A `coverage.json` ATT&CK Navigator layer marking your three techniques as covered.

## Deliverables

`rules/` directory (three `.yml` Sigma rules) + `coverage.json` (ATT&CK Navigator layer).
Commit both.

## Automate & own it

**Required.** Write a shell script `run-detections.sh` that: takes a directory of Sigma rules
and an alert JSON file, runs sigma-cli against each rule, and outputs a summary table:
rule name, match count, technique ID. Exit non-zero if any rule produces zero matches (a
rule that never fires against its intended test data is broken). Have an AI draft the loop
and summary table logic; you verify the exit-code logic and test against both a matching and
a non-matching alert file.

## AI acceleration

Describe an alert's fields to an AI and ask it to write a Sigma rule that matches it. Then
run the rule through `sigma-cli` against the alert data — does it fire? Does it fire on the
benign events too? The model drafts the rule shape; the test data tells you if the detection
logic is correct. A rule the model wrote that you never tested is a guess, not a detection.

## Connects forward

The three Sigma rules you wrote here are the start of Meridian's host detection library. The
track capstone asks you to integrate the full hardening baseline (modules 02–09) with telemetry
(module 05), compliance scanning (module 07), and detections (this module) into a single
demonstrable posture — "this host is hardened AND we know when it's being attacked."

## Marketable proof

> "I wrote ATT&CK-mapped Sigma detection rules for host compromise indicators, tested them
> against Wazuh-shaped alert data, and produced an ATT&CK Navigator coverage layer showing
> what our endpoint detections cover and where the gaps are."

## Stretch

- Add a fourth rule for a technique you identify as a gap — look at the alert data for an
  event that doesn't match any of your three rules but looks suspicious. Write the rule,
  add the ATT&CK mapping, and update `coverage.json`.
- Research how Wazuh's active response feature works: a rule fires, Wazuh automatically runs
  a script (e.g. block an IP, quarantine a file). Design the active response for the lateral
  movement detection — what would you automatically block, and what is the false-positive risk?
