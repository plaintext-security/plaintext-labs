# Module 16 — Cloud Incident Response

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *the attacker left in the API log; your job is to find the thread and pull it.*

## Why this matters
Cloud IR is the place where everything the previous modules taught converges under pressure. The
attacker used a technique you studied; the logs that recorded it are the ones you learned to parse;
the containment actions are the inverse of the misconfigurations you audited. But IR is harder than
the lab conditions because the data is enormous, the time pressure is real, and the sequence of
events you need to reconstruct spans hours of logs across multiple services. The practitioner who
can take a raw CloudTrail export and, within an hour, have a defensible timeline, a list of IOCs,
and a containment checklist is the one the CISO calls first.

## Objective
Given a CloudTrail export and VPC flow logs from a simulated Meridian Financial incident, build a
chronological timeline of attacker actions from initial access to exfiltration, extract all IOCs
(IPs, access keys, affected resources), identify the phases of the attack that would not have been
caught by default GuardDuty, and produce a containment checklist using `triage.py`.

## The core idea
Cloud IR has a different shape than traditional endpoint IR. There is no binary to reverse, no
memory image to analyse — the entire crime scene is a sequence of authenticated API calls in an
audit log. The canonical tool is CloudTrail: a tamper-evident, structured, per-event record of
everything that happened in the control plane. The first IR question is always "is the trail
intact?" — because one of the first things a competent attacker does is call `StopLogging`. When
the trail is complete, you have everything; when it's been stopped, you have a gap, and the gap's
duration is itself evidence.

The hayabusa approach — building a timeline from raw log records sorted by timestamp and tagged
with kill-chain phase — translates directly to CloudTrail. The tool `hayabusa` is a Sigma-based
Windows event log timeline builder, but the methodology is the same in the cloud: ingest, sort,
tag, filter to the attacker's identity and source IPs. What you get is not a raw log but a readable
narrative: "02:14 — credential validation; 02:15 — enumeration; 02:16 — privilege escalation;
02:17 — data collection; 02:18 — exfiltration channel opened; 02:18 — trail stopped." That
narrative is the incident report; the CloudTrail records are the evidence.

The VPC flow logs add the data-plane dimension. CloudTrail tells you the control-plane story (what
APIs were called, by whom, from where). Flow logs tell you the network story (how many bytes left
this instance, to which external IP, at what time). The two logs are complementary: an
`AssumeRole` + mass `GetObject` in CloudTrail correlates with an outbound flow of hundreds of
megabytes to an external IP in the flow logs. When both are present, you have a very strong case
for data exfiltration. When only flow logs show unusual outbound volume but CloudTrail is clean,
either a data-plane exfiltration path was used (S3 URLs, pre-signed URLs, STS credentials stolen
out-of-band) or the control-plane log was tampered.

Containment in the cloud is faster than on-premises, but the sequencing matters. The four steps in
order: (1) revoke active credentials — disable the access keys and invalidate any active role
sessions; (2) close the exfiltration channel — delete bucket replication rules, revoke
cross-account access, remove any new IAM users or keys the attacker created; (3) restore the audit
trail — re-enable CloudTrail; (4) scope the impact — enumerate every API call made from the
attacker's key and session between first compromise and revocation. Step 4 is often where
organisations undercount the blast radius because they only check the original compromised key and
miss the persistence mechanisms (a second access key, a new IAM user, an EC2 instance profile
modified to include `s3:*`). The timeline you build in this lab is the tool that surfaces those.

## Learn (~3.5 hrs)

**Cloud incident response frameworks (~1 hr)**
- [AWS Security Incident Response Guide](https://docs.aws.amazon.com/security-ir/latest/userguide/security-incident-response-guide.html)
  — read the "Preparation" and "Detection and Analysis" chapters; these are the primary AWS source
  for how to structure a cloud IR engagement. Skip the organisational sections for now; focus on
  the forensics workflow.
- [CISA Cloud Security Incident Response Reference: section 4](https://www.cisa.gov/resources-tools/resources/cloud-security-technical-reference-architecture)
  — the US-government guidance on cloud IR; section 4 covers log acquisition and evidence
  preservation. Useful for understanding the legal and chain-of-custody considerations that differ
  from on-premises IR.

**CloudTrail forensics (~1 hr)**
- [CloudTrail userIdentity element reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-user-identity.html)
  — the `userIdentity` block is the most forensically rich field in a CloudTrail record; understand
  the difference between `IAMUser`, `AssumedRole`, `Root`, and `AWSService` types and what each
  implies for the attack chain.
- [Detect and respond to compromised AWS credentials — AWS Blog](https://docs.aws.amazon.com/config/latest/developerguide/evaluate-config.html)
  — a practitioner walkthrough; watch for the pattern of using CloudTrail Insights and Athena for
  large-scale log queries. (~20 min read)

**Hayabusa and timeline analysis (~1.5 hrs)**
- [Hayabusa GitHub README](https://github.com/Yamato-Security/hayabusa) — understand the
  timeline-building approach: ingest event logs, run Sigma rules over them, output a sorted CSV.
  The methodology transfers directly to CloudTrail. (~30 min)
- [DFIR.report: Cloud IR case study (2023)](https://thedfirreport.com/) — browse recent public
  cloud IR case reports; the attack chains are real, the containment steps are documented, and the
  timeline methodology is explicit. Pick one AWS-related report (~1 hr).

## Key concepts
- CloudTrail as the crime scene: management events, the `userIdentity` block, and the `StopLogging`
  tell
- Timeline reconstruction: sort by timestamp, tag by kill-chain phase, filter to attacker identity
- VPC flow logs as the data-plane complement: bytes out + external IP = exfiltration corroboration
- Containment order: revoke credentials → close exfiltration channels → restore logging → scope
  impact
- Persistence traps: second access keys, new IAM users, modified role trust policies — scope beyond
  the initial compromised key

## AI acceleration
Feed your timeline to a model and ask it to identify any gaps — periods where activity stopped
that might indicate the trail was tampered, or where the attacker's behaviour doesn't match any
known technique. Models are good at pattern-matching a sequence of API calls against ATT&CK
technique descriptions. They're less reliable at temporal reasoning (e.g., "this key was used 6
hours later — is that the persistence mechanism or a different attacker?"). Use the model for the
first-pass tagging and technique mapping; apply your own judgement on the sequencing and
attribution. The timeline you commit is your professional analysis — not the model's.
