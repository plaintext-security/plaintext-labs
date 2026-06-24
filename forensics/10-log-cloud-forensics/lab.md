# Lab 10 — Log & Cloud Forensics: Hayabusa, Chainsaw, and CloudTrail

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/10-log-cloud-forensics
make up         # builds container with hayabusa, chainsaw, and python
make fetch-data # download the real EVTX-ATTACK-SAMPLES .evtx files into data/evtx/
make demo       # runs hayabusa + chainsaw over evtx/, then parses cloudtrail/
make shell      # interactive shell for investigation
make down       # stop when done
```

The lab ships two datasets:
- `data/evtx/` — the Windows half. The **primary artifact is real**: `make fetch-data` pulls
  Windows `.evtx` from the public
  [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) corpus (by sbousseaden)
  covering scheduled-task creation, PowerShell execution, and network logon. The synthetic
  `evtx_triage_summary.txt` / `chainsaw_summary.txt` are kept only as an offline fallback so
  `make demo` runs before `fetch-data`. See `PROVENANCE.md`.
- `data/cloudtrail/cloudtrail.json` — a small bundled AWS CloudTrail set **modelled on the public
  Lunar Spider cloud TTPs** (neutral naming): API activity after the developer IAM key was
  extracted from the compromised workstation.

> The CloudTrail set is bundled and synthetic; the EVTX are real public research samples. Do not
> use real incident data in shared lab environments.

## Scenario

This module is anchored to the **Lunar Spider** intrusion (The DFIR Report, 2025). The endpoint
triage (module 08) confirmed `BEACHHEAD-WS01` was compromised. DFIR pulled the Windows Event Logs
off the host before imaging. Simultaneously, the Cloud Security team noticed unusual IAM activity
in the affected organization's AWS account starting 40 minutes after the workstation alert — the
timeline suggests the attacker extracted the developer's AWS credentials from the machine and
pivoted to the cloud environment.

Your task: triage the EVTX files to build a timeline of endpoint activity, then parse the
CloudTrail events to reconstruct the attacker's cloud pivot.

> Only examine log data you are authorised to handle. Event logs may contain personal data
> subject to privacy regulations in your jurisdiction.

## Do

**Part 1 — Windows Event Log Triage**

1. [ ] **Run `make demo`** and read the Hayabusa output section. Find the highest-severity event.
   What Event ID is it? What does that Event ID typically indicate? (Hint: Event ID 4698 is
   scheduled task creation; 4624 is successful logon; 4688 is process creation.)

2. [ ] **Run Chainsaw** inside `make shell` to search the real `.evtx` for execution / logon activity:
   ```bash
   chainsaw search --json -t "SubjectUserName: jsmith" /data/evtx/
   ```
   How many events match? What are the earliest and latest timestamps? (Against the real
   EVTX-ATTACK-SAMPLES files, search by Event ID — `--event-id 4688` / `4624` — to find what ran
   and who authenticated.)

3. [ ] **Build a mini-timeline:** list the top five events in chronological order with their
   Event IDs and brief descriptions. This is the endpoint portion of the intrusion timeline.

**Part 2 — CloudTrail Analysis**

4. [ ] **Run the CloudTrail parser** (from `make demo` output or manually):
   ```bash
   python3 /scripts/parse_cloudtrail.py /data/cloudtrail/
   ```
   Which IAM principal (user or role) made the first API call? What was the `eventName`?

5. [ ] **Trace the event sequence.** The parser prints events in chronological order. Identify:
   - The first API call that looks like reconnaissance (`GetCallerIdentity`, `ListUsers`,
     `ListRoles`, `DescribeInstances`)
   - The first API call that looks like persistence (`CreateUser`, `AttachUserPolicy`,
     `CreateAccessKey`)
   - Any `AssumeRole` calls — these indicate lateral movement between IAM roles.

6. [ ] **Map to ATT&CK.** For each category identified in step 5, look up the corresponding
   Cloud Matrix technique on [attack.mitre.org](https://attack.mitre.org/matrices/enterprise/cloud/)
   and note the technique ID and tactic. (Work out, for instance, which sub-technique the
   `CreateUser` + `CreateAccessKey` pair maps to — don't guess the ID, find it in the matrix.)

7. [ ] **Combined timeline.** Merge your endpoint mini-timeline (Part 1) with the CloudTrail
   event sequence (Part 2) in chronological order. Is there a gap between the last endpoint
   event and the first CloudTrail event? How long? What might that gap represent?

## Success criteria — you're done when

- [ ] You have identified the highest-severity EVTX event by ID and description.
- [ ] You have a mini-timeline of five endpoint events in chronological order.
- [ ] You have identified the three categories of CloudTrail activity (recon, persistence, lateral).
- [ ] Each CloudTrail finding is mapped to an ATT&CK Cloud technique ID.
- [ ] You have a merged endpoint + cloud timeline with gap analysis.

## Deliverables

Commit to your portfolio repo:
- `timeline.md` — the merged endpoint + cloud timeline, with Event IDs and CloudTrail eventNames cited.
- `attack-mapping.md` — a table mapping each finding to its ATT&CK technique ID and tactic.

Do not commit EVTX files or CloudTrail JSON — reference filenames in your timeline instead.

## Automate & own it

**Required.** Write a Python script `cloudtrail_pivot.py` that:
1. Reads all `.json` files in a CloudTrail directory.
2. Extracts `eventTime`, `userIdentity.arn`, `eventName`, `sourceIPAddress`, and
   `requestParameters` (summary only).
3. Groups events by `userIdentity.arn` and prints a per-principal event timeline sorted by time.
4. Flags any principal that performed both a recon event (from a configurable list of
   eventNames) and a persistence event within 60 minutes of each other.

Have a model draft the script; **validate its output against the seed data** by manually checking
two flagged events against the raw JSON before trusting the automated findings. Commit `cloudtrail_pivot.py`.

## AI acceleration

Feed the Hayabusa JSON timeline to a model and ask it to identify the ATT&CK phase each event
belongs to. Compare the model's phase assignments to your own. The model will typically be accurate
for well-known Event IDs (4698, 4688, 4624) but may struggle with less common ones or with
distinguishing legitimate administrative activity from attacker activity when field values look
similar. The judgment call — "is this scheduled task creation expected for this host?" — is the
part you own.

## Connects forward

Module 11 (Anti-Forensics) examines what happens when an attacker tries to cover their tracks in
the EVTX and filesystem. Module 13 (IR Process) uses this combined timeline as the input to the
NIST SP 800-61 analysis phase.

## Marketable proof

> "I triage Windows Event Logs with Hayabusa and Chainsaw, map findings to ATT&CK, and reconstruct
> cloud attacker timelines from AWS CloudTrail — correlating endpoint and cloud evidence into a
> single merged investigation timeline."

## Stretch

- Modify `cloudtrail_pivot.py` to also ingest VPC Flow Log records (simulated in
  `data/cloudtrail/vpc_flow.log`) and correlate network connections with IAM API calls by
  timestamp — connecting "this IP made API calls" with "this IP also connected to the EC2
  instance."
- Add Hayabusa's `--MITRE-ATT&CK` output flag and produce a heatmap CSV showing which
  techniques are represented in the EVTX set; visualise it with a simple Python `matplotlib`
  bar chart.
