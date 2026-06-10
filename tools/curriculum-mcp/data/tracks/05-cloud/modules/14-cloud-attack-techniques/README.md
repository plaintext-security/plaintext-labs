# Module 14 — Cloud Attack Techniques

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *you can't defend what you haven't attacked: simulate adversary techniques safely, in your own environment.*

## Why this matters
Every GuardDuty finding, every CloudTrail anomaly alert, and every incident response playbook you'll
ever write was born from someone first answering the question: what does this attack actually look
like in the logs? The defensive half of cloud security is built on top of the offensive half — and
the practitioners who can articulate exactly what `AssumeRole` chaining, S3 mass-download, or IAM
user creation looks like from the attacker's perspective are the ones who write detection rules that
don't miss. This module gives you that fluency.

## Objective
Simulate three MITRE ATT&CK Cloud techniques (T1078.004 — Valid Cloud Accounts, T1530 — Data from
Cloud Storage, T1537 — Transfer Data to Cloud Account) against a local AWS environment, capture the
CloudTrail-shaped API calls each technique generates, and articulate exactly which log fields
distinguish attacker behaviour from normal operations.

## The core idea
Cloud attacks are almost entirely API attacks. Unlike traditional post-exploitation — where an
adversary moves laterally by dropping binaries, modifying the registry, or pivoting through network
segments — cloud attacks are sequences of signed API calls made with stolen or escalated credentials.
The attacker's footprint is in the control plane: CloudTrail, the GCP Audit Log, the Azure Activity
Log. Understanding that the "malware" is a signed API call, not a binary, reframes both the attack
and the detection.

The two dominant simulation tools reflect this. **Pacu** (Rhino Security Labs) is an AWS
exploitation framework built on the same mental model as Metasploit, except every module is a call to
the AWS API. It chains techniques — enumerate IAM, find an over-privileged role, assume it, then use
the new session to enumerate what the original credentials couldn't reach. The attack narrative is
linear and module-driven. **Stratus Red Team** (DataDog) takes a different approach: it codifies
individual ATT&CK techniques as atomic actions — each one stands alone, generates a specific set of
API calls, and can be detonated and cleaned up independently. It is built for detection engineers
who want the precise log signature of a single technique, not a full attack chain. Both belong in
the toolkit; Pacu for chain reasoning, Stratus for detection validation.

The critical safety discipline is simulation containment. Stratus Red Team's `--localstack` support
and Pacu against a LocalStack environment let you generate realistic CloudTrail-shaped events without
touching a real account. When you do work against a real AWS account (your own, deliberately
misconfigured test account), the blast radius controls are: dedicated test account, no production
resources, all findings torn down after the exercise. This is the same constraint red-team
engagements put in their rules of engagement — except here you set it yourself.

MITRE ATT&CK for Cloud is the vocabulary. The techniques in this module (T1078.004, T1530, T1537)
map to a compressed version of the cloud kill chain: the attacker already has credentials (initial
access is module 02–03's territory), they use those credentials to pull data from storage, and they
stage that data for exfiltration to an attacker-controlled location. Each technique has a distinct
log signature, and the gap between "normal S3 activity" and "T1530 mass download" lives in the
combination of user identity, request rate, absence of the normal application's user-agent, and the
breadth of objects accessed — not in any single field. That's the analytical challenge this lab
forces you to confront.

## Learn (~3 hrs)

**MITRE ATT&CK for Cloud (~1 hr)**
- [ATT&CK Cloud Matrix](https://attack.mitre.org/matrices/enterprise/cloud/) — spend time on the
  Initial Access, Credential Access, and Exfiltration columns. Each technique card shows real
  procedure examples; the examples column is where you learn what the API calls actually look like
  in practice.
- [T1078.004 — Valid Accounts: Cloud Accounts](https://attack.mitre.org/techniques/T1078/004/) —
  the primary entry point for cloud attacks; read the detection guidance section carefully, it lists
  the exact log sources and fields.
- [T1530 — Data from Cloud Storage](https://attack.mitre.org/techniques/T1530/) — S3/GCS/Blob mass
  download; note the contrast between control-plane and data-plane logging requirements.
- [T1537 — Transfer Data to Cloud Account](https://attack.mitre.org/techniques/T1537/) — adversary
  stages data in their own bucket; the detection is the S3 replication/sync call with an external
  destination.

**Stratus Red Team (~1 hr)**
- [Stratus Red Team documentation](https://stratus-red-team.cloud/attack-techniques/list/) — browse
  the AWS technique list; each entry has the detonation method, the exact API calls it fires, and
  example CloudTrail events. This is the best cloud-attack log reference on the public internet.
- [Stratus Red Team GitHub README](https://github.com/DataDog/stratus-red-team) — quick-start and
  the LocalStack integration; skim the `--endpoint-url` workflow before the lab.

**Pacu (~1 hr)**
- [Pacu GitHub wiki — Getting Started](https://github.com/RhinoSecurityLabs/pacu/wiki/)
  — module layout and the `run`, `exec`, and `search` commands; the module naming convention mirrors
  ATT&CK technique IDs.
- [Rhino Security Labs: "Pacu the AWS Exploitation Framework"](https://rhinosecuritylabs.com/aws/pacu-open-source-aws-exploitation-framework/)
  — the original framing post; useful for understanding what problem Pacu was designed to solve vs.
  manual CLI enumeration. (~10 min read.)

## Key concepts
- Cloud attacks are API attacks: the attack surface is the control plane, not the filesystem
- T1078.004 / T1530 / T1537 as a compressed cloud kill chain: access → collect → stage
- Pacu for attack-chain reasoning; Stratus Red Team for atomic, detection-focused technique detonation
- Simulation containment: LocalStack, dedicated test accounts, blast radius controls
- The log fields that distinguish attacker from normal operator: userIdentity, userAgent, eventTime
  density, requestParameters breadth

## AI acceleration
Feed a Pacu session output or a set of CloudTrail events to a model and ask it to identify the
ATT&CK techniques and flag the highest-risk API calls. Models are good at pattern-matching known
technique signatures against event fields — but they will hallucinate specific CloudTrail field names
and can miss the *combination* logic (event A followed by event B from the same identity within a
window). Use the model output as a triage pass, then validate each identified technique against the
ATT&CK technique card's detection guidance. You own the final mapping.
