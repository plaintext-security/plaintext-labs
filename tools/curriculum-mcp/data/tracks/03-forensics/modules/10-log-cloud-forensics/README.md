# Module 10 — Log & Cloud Forensics

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *investigate from the paper trail when the disk is gone, the instance is terminated, and the only artifact is what the platform logged.*

## Why this matters

Cloud-native incidents often produce no disk image. Autoscaling instances terminate and their local
storage vanishes; serverless functions leave no filesystem at all. What remains is the log: CloudTrail
in AWS, the Unified Audit Log in Microsoft 365, VPC Flow Logs, and Windows Event Logs forwarded to a
SIEM before the host was deprovisioned. A responder who can only work from disk images is stranded
in a cloud incident. The practitioner who can reconstruct an attacker's actions entirely from log
evidence — without ever touching the compromised system — is the one who can actually close cloud
investigations.

## Objective

Use Hayabusa to rapidly triage Windows Event Log (EVTX) files from the Meridian investigation,
use Chainsaw for a complementary pass, and parse a set of simulated AWS CloudTrail events with a
Python script to identify the sequence of API calls that preceded the developer account compromise.

## The core idea

Windows Event Logs are rich and noisy in equal measure. A typical endpoint generates thousands of
events per hour; an attacker generating a handful of authentication failures, a new scheduled task,
and a process creation event is lost in that noise without a way to triage by severity. **Hayabusa
and Chainsaw solve this by applying Sigma rules directly to EVTX files** — the same Sigma language
from module 08, now running against the raw log source rather than a SIEM. Load an EVTX archive
from a compromised host, run either tool, and within seconds you have a timeline of
high-and-medium-severity events sorted by time, ready to pivot on.

The distinction between the two tools is worth understanding because they're often used in sequence.
**Hayabusa** is built around a high-performance Sigma rule engine optimised for speed across large
EVTX sets — it can process hundreds of thousands of events in seconds and produces clean columnar
output or JSON. **Chainsaw** takes a heavier-weight approach: it also supports Sigma but adds its
own detection grammar, and it provides structured search across log fields (find all events where
SubjectUserName is "mfin\dev-svc01") that makes hypothesis-driven investigation faster when you
already know what you're looking for. Running both against the same artifact costs little time and
produces complementary coverage: Hayabusa for the initial triage heat map, Chainsaw for drilling
into specific accounts or techniques.

Cloud forensics requires a different model entirely. CloudTrail is not a log of what happened on
a system — it's a log of what the *API* was asked to do. Every `CreateUser`, `AttachUserPolicy`,
`AssumeRole`, `RunInstances`, or `GetCallerIdentity` call is a row. An attacker who compromised
a developer IAM key and then pivoted to create a backdoor role left a complete sequential record
in CloudTrail, if you know how to read it. The investigation pattern is: find the initial API call
from the compromised credential, then trace forward in time to every action that principal took,
then look for any new principals it created or any roles it assumed. **The attack graph is in the
event sequence** — you're reconstructing a timeline of API calls, not filesystem operations.

The gap that trips responders in cloud investigations is that **log availability is not
guaranteed.** CloudTrail must be enabled before the incident; if a trail wasn't configured, the
log doesn't exist. In AWS, CloudTrail management events are on by default for 90 days in Event
History — but data events (S3 GetObject, Lambda invocations) are off by default and must be
explicitly enabled. A mature cloud security posture ensures these are on and forwarded to a
tamper-evident log archive (S3 with Object Lock, or a separate logging account) before anyone
needs them. This is the planning decision that makes or breaks a cloud investigation.

## Learn (~3 hrs)

**Hayabusa and Chainsaw (~1.5 hrs)**
- [Hayabusa GitHub — README](https://github.com/Yamato-Security/hayabusa) — start here: the installation, rule sources, and output modes. Run `hayabusa --help` to see the full option surface; focus on the `csv-timeline` and `json-timeline` output modes.
- [Chainsaw GitHub — README and documentation](https://github.com/WithSecureLabs/chainsaw) — covers Chainsaw's own grammar (`chainsaw search`) and Sigma integration (`chainsaw hunt`). The "Usage" section shows how to search for specific account activity.
- [EVTX Attack Samples (GitHub)](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) — a large repository of real Windows attack event logs, categorised by ATT&CK technique. Browse the `T1078` (Valid Accounts) and `T1053` (Scheduled Task) samples — these are the techniques active in the Meridian scenario.

**AWS CloudTrail forensics (~1 hr)**
- [AWS CloudTrail — Log Event Reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html) — the field definitions: `userIdentity`, `eventSource`, `eventName`, `sourceIPAddress`, `requestParameters`. These are the fields you parse in the lab.
- [AWS CloudTrail User Guide — Searching and Querying Events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html) — official guide to interpreting CloudTrail for forensic investigation; covers privilege escalation and persistence event patterns.

**Detection context (~0.5 hrs)**
- [MITRE ATT&CK Cloud Matrix](https://attack.mitre.org/matrices/enterprise/cloud/) — the cloud-specific technique matrix; map the CloudTrail events you find in the lab to techniques here to understand what the attacker was doing.

## Key concepts
- Hayabusa and Chainsaw apply Sigma rules directly to EVTX files, triaging thousands of events to a severity-ranked timeline in seconds
- Hayabusa: optimised for speed and volume; best for initial triage across large EVTX archives
- Chainsaw: structured field search + Sigma; best for hypothesis-driven investigation
- CloudTrail records API calls: `userIdentity`, `eventName`, `sourceIPAddress`, `requestParameters` are the key investigation fields
- Cloud forensics: trace compromised credentials forward through the event sequence to find lateral movement and persistence API calls
- Log availability is a planning decision: CloudTrail data events and VPC Flow Logs must be enabled before they're needed

## AI acceleration

Hayabusa and Chainsaw produce structured JSON output that a model can reason about directly. Feed
the timeline output to a model and ask it to group events by phase (Initial Access, Execution,
Persistence, Lateral Movement) and identify the earliest evidence of each. Use this as a starting
point for your own timeline, not as the timeline itself — models miss events that require operational
context ("this account doing this action is expected in this environment") and sometimes hallucinate
by extrapolating from the event names without reading the field values. CloudTrail JSON is
particularly well-suited to model analysis: the JSON schema is consistent and well-documented, and
the model can trace an event chain faster than grep. Verify every model-identified event against
the raw JSON before citing it in the report.
