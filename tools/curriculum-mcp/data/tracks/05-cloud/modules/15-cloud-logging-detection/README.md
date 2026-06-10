# Module 15 — Cloud Logging & Detection

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *the attacker's footprint is in the API log; the defender's job is to find it before it becomes news.*

## Why this matters
Cloud environments are comprehensively logged by default in ways on-premises infrastructure never
was — every IAM call, every S3 access, every console login is a signed, tamper-evident record. The
troubling implication is that your ability to detect attacks is proportional to your ability to
actually use those logs. Most organisations have GuardDuty enabled but haven't looked at a raw
CloudTrail file. When an incident happens and GuardDuty is quiet, you need to know what to search.
This module gives you both: the native detectors and the open-tool skills to operate when they
don't cover a technique.

## Objective
Write a Sigma rule for a CloudTrail privilege-escalation sequence (CreateUser → AttachUserPolicy),
run it against a bundled set of real-shaped events using a Python matcher, reproduce the same
finding using GuardDuty's event model, and articulate when native detectors are sufficient versus
when open tooling adds coverage.

## The core idea
The cloud logging surface splits cleanly into two planes, and you must understand both. The
**management events** plane (CloudTrail's default) captures every API call that changes or reads
the configuration of a resource: CreateUser, AssumeRole, RunInstances, PutBucketPolicy. This is
the control plane in log form — everything an attacker does to reconfigure or escalate inside your
environment produces a management event. The **data events** plane captures the actual reads and
writes against data: S3 GetObject, DynamoDB GetItem, Lambda invocations. Data events cost money to
log and generate enormous volume, so most organisations log them only for sensitive buckets. The
first thing to check in any cloud incident is which data events were enabled — if S3 object-level
logging wasn't on, you can't tell which objects an attacker exfiltrated.

Native cloud detectors — AWS GuardDuty, Microsoft Defender for Cloud, GCP Security Command Center
— are trained on the same control-plane logs and apply pre-built ML models and rule libraries that
a platform team would take months to write from scratch. Their strength is low-friction coverage:
you click enable and immediately get detections for the most common attack patterns. Their weakness
is opacity and lag: GuardDuty's rules are a black box, the technique coverage lags the ATT&CK
Cloud matrix, and when an attacker uses a novel technique or stays below the ML model's thresholds,
you get silence. The practitioner position is not "native or open" — it is "native as the baseline,
open tooling for the gaps."

Sigma rules are the lingua franca for detection-as-code in the cloud logging space. A Sigma rule
for a CloudTrail sequence is a YAML document that specifies the `logsource`, the `detection` logic
(field matches, conditions, and crucially for sequences — the `followed by` syntax with a time
window), and the `falsepositives` you've thought through. The value is portability: a Sigma rule
can be compiled to Splunk SPL, Elastic KQL, Panther Python, or evaluated directly — without being
rewritten. The challenge is that CloudTrail's event structure is nested (the interesting fields live
inside `requestParameters` and `userIdentity`, not at the top level), and naive rules generate
alert fatigue because they match on a single event without the sequence context.

The detection engineering discipline this module drills is **sequence logic with context**. A
single `CreateUser` call is benign a hundred times a day. A `CreateUser` followed by
`AttachUserPolicy` with `AdministratorAccess` within five minutes from a non-corporate IP is almost
never legitimate — but you need both events, the policy name, the IP, and the time window to write
a rule that fires precisely. This is the analytical pattern behind most of the high-fidelity cloud
detections: not a single event, but a sequence with qualifying conditions. Getting that logic right
— and encoding it reproducibly in a Sigma rule rather than in someone's head — is the job.

## Learn (~3.5 hrs)

**CloudTrail and AWS logging architecture (~1 hr)**
- [AWS CloudTrail Concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html)
  — read the "How CloudTrail works" and "Management events vs. data events" sections; this is the
  primary source on what gets logged, what doesn't, and the cost model. Skip the regional trail
  setup detail for now.
- [CloudTrail event record fields reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html)
  — bookmark this; every detection rule you write will reference `eventSource`, `eventName`,
  `userIdentity.type`, `sourceIPAddress`, and `requestParameters`. One field at a time.

**GuardDuty and native cloud detectors (~1 hr)**
- [AWS GuardDuty finding types](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html)
  — skim the IAM and S3 sections to understand which techniques GuardDuty covers natively and at
  what confidence level. The `UnauthorizedAccess:IAMUser/TorIPCaller` finding is in this lab's seed
  data.
- [Microsoft Defender for Cloud: overview of security alerts](https://learn.microsoft.com/en-us/azure/defender-for-cloud/alerts-overview)
  — 15 minutes on the Azure equivalent; note the structural similarity to GuardDuty (finding type,
  severity, affected resource, evidence fields). The mental model is transferable across clouds.

**Sigma rules for cloud logs (~1.5 hrs)**
- [Sigma rule specification — detection logic](https://sigmahq.io/docs/basics/rules.html) — read
  the "Detection" section specifically; the `followed by` temporal correlation syntax is what makes
  sequence rules possible. (~30 min)
- [SigmaHQ CloudTrail rule collection](https://github.com/SigmaHQ/sigma/tree/master/rules/cloud/aws)
  — browse five to ten actual rules from this repo; notice how the `logsource` is set, how
  `requestParameters` fields are referenced with dot notation, and how `falsepositives` are
  documented. Don't just read them — mentally run each one against a CloudTrail event and ask: what
  fields would have to match for this to fire? (~1 hr)

## Key concepts
- Management events vs. data events: what logs by default, what costs extra, what's missing in a
  default CloudTrail config
- GuardDuty / Defender for Cloud / GCP SCC as the coverage baseline; open tooling for the gaps
- Sigma rule structure for CloudTrail: `logsource`, `detection`, `condition`, `falsepositives`
- Sequence detection: why single-event rules generate alert fatigue and how the `followed by` syntax
  fixes it
- The CreateUser → AttachUserPolicy escalation sequence as a canonical T1098 signature

## AI acceleration
Ask a model to draft a Sigma rule for a CloudTrail sequence you describe in plain English. Models
know the Sigma syntax and the common CloudTrail field names, and a first draft saves thirty minutes
of scaffolding. The review work is yours: check that the `logsource` product/service matches the
CloudTrail Sigma pipeline, that the field references use the correct nested notation, and that the
`falsepositives` section reflects what your organisation's legitimate automation does. Run the rule
against the bundled events with the lab's `detect.py` before trusting it — a rule that doesn't fire
on the data it's designed to catch is not a rule.
