# Module 15 — Cloud Logging & Detection

*Variant D · breach-driven, predict-what-fires ("the logs existed; predict the signal, then write the detection"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *detection is not a logging problem; it's an attention problem. The log was always there.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4.5–6.5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 14 — Cloud Attack Techniques](../14-cloud-attack-techniques/README.md)
{ .module-meta }


## The case

In both of the breaches that bookend this track, **the log existed the whole time.** Capital One's
attacker assumed a role and listed every bucket — and it was [in CloudTrail](https://www.justice.gov/usao-wdwa/press-release/file/1188626/download);
an outsider, not the company, reported the breach. In the [LastPass 2022 incidents](https://blog.lastpass.com/posts/2022/12/notice-of-recent-security-incident),
an attacker used keys stolen from a senior engineer to reach S3 and a DynamoDB store and walk out with
encrypted customer vaults plus configuration — and the activity ran against logged AWS APIs. Neither
breach was a *logging* failure. The telemetry was generated, signed, and retained. **Nobody was
watching the stream it landed in.**

That is the uncomfortable truth this module turns on: cloud is comprehensively logged by default in a
way on-prem never was, and that abundance creates a false sense of safety. A detection is a hypothesis
about attacker behaviour scored against a stream that is **99.99% benign** — and the hard part is never
the true positive. It's making the rule quiet enough that a human will still read its alerts a month
from now. So before you read on:

> **Of the techniques you detonated in module 14, which one shows up *loud and clear* in CloudTrail by
> default — and which is *nearly invisible*?**

## Your job

By the end of this module you'll take the telemetry from module 14, **predict which attacker actions
the default log even captured**, then **write a Sigma rule** for the one worth detecting and **tune it
against benign activity** until it fires on the attack and *not* on the noise. You'll reproduce the same
finding in a native detector's event model (GuardDuty / Defender / SCC) and rule on where native
coverage is enough and where you must fill the gap. The deliverable is detection-as-code with an
explicit false-positive analysis — the artifact a cloud detection engineer is actually paid for.

## Call it before you read on

Don't scroll. Commit to these — being wrong is the teaching event, and you'll grade yourself in the lab.

> **Q1.** In module 14 the attacker assumed a role (T1078.004), created an admin user (T1098), *and*
> bulk-downloaded objects from S3 (T1530 — the LastPass exfil move). **By default, which of those is
> NOT in CloudTrail at all?**
>
> **Q2.** You write a rule: alert on any `CreateUser`. It fires perfectly on the attack. Why is it a
> *bad* detection — what happens to it in week two?
>
> **Q3.** A single `GetObject` is benign a thousand times a day. So is `AssumeRole`. How do you turn
> "individually-benign events" into a high-fidelity detection without drowning in false positives?

## What fires, revealed

Hold your answers against these.

**Q1 — the data plane is dark by default.** CloudTrail splits into two planes, and the split is the
single most important gotcha in cloud detection. **Management events** — `AssumeRole`, `CreateUser`,
`AttachUserPolicy`, `PutBucketPolicy`, `RunInstances` — are the control plane in log form, and they are
logged *for free, by default*. **Data events** — `s3:GetObject`, `s3:PutObject`, `dynamodb:GetItem`,
`lambda:Invoke` — are the actual reads and writes against your data, and they are **off by default**,
cost money, and generate enormous volume, so most orgs log them only on a few sensitive buckets. So the
answer to Q1 is **T1530, the bulk download** — the exact move that exfiltrated LastPass's vaults is, in
a default account, *invisible*. The first question in any cloud incident is "were S3 data events enabled
for this bucket?" — and the honest, common answer is *no, so we cannot tell which objects left.* The
attacker's loudest action (the one that did the damage) is the one your default log is silent on.

**Q2 — the false-positive economics is the whole craft.** A rule that fires on every `CreateUser` is
correct on the attack and *useless* in production, because legitimate automation creates users all day.
By week two it's muted, ignored, or routed to a folder no one opens — and a muted rule is a non-existent
rule that *feels* like coverage. **A detection isn't scored on whether it catches the attack; it's scored
on its signal-to-noise on a 99.99%-benign stream.** Precision is the product. This is why "we have
GuardDuty enabled" is not the same as "we detect": coverage you don't tune is alert fatigue with a
dashboard.

**Q3 — sequence and qualifying context turn benign atoms into a signal.** The fix for Q2 is to stop
detecting single events and start detecting *behaviour*. `CreateUser` alone is noise; `CreateUser`
**followed by** `AttachUserPolicy` attaching `AdministratorAccess` **within five minutes** **from an IP
that isn't your CI range** is almost never legitimate — and that compound is precise. This is Sigma's
job: a YAML detection that names the `logsource`, the field matches (the interesting fields are *nested*,
in `requestParameters` and `userIdentity` — not top-level), the temporal `condition`, and — the part
beginners skip — the `falsepositives` you've reasoned through. Native detectors (GuardDuty, Defender for
Cloud, GCP SCC) ship pre-built versions of exactly this logic over the same control-plane logs; their
strength is one-click coverage of common patterns, their weakness is opacity and lag behind the ATT&CK
Cloud matrix. The practitioner posture is not "native or open" — it's **native as the baseline, Sigma
for the gap, and every rule tuned against benign traffic before it's trusted.**

In the lab you'll do exactly this against the module-14 telemetry: confirm the data-plane blind spot,
write and tune one Sigma rule, and reproduce the finding in a native detector's model.

## Learn (~3.5 hrs)

*Richer than a foundations module — detection engineering is a craft. Read the case first, then the mechanism.*

**The logging surface and its blind spot (~1 hr)**
- [AWS — CloudTrail concepts: management vs. data events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html) (~30 min) — the primary source. Read "Management events vs. data events"; this is *why* T1530 is dark by default. The cost/volume model is the reason, not an accident.
- [AWS — CloudTrail record contents reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html) (~20 min, bookmark) — every rule references `eventName`, `eventSource`, `userIdentity.type`, `sourceIPAddress`, `requestParameters`. Learn where the interesting fields are nested.

**Native detectors as the baseline (~1 hr)**
- [AWS — GuardDuty finding types](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty_finding-types-active.html) (~30 min, skim) — read the IAM and S3 sections: which techniques native coverage catches and at what confidence. Note what it *doesn't* cover.
- [Microsoft — Defender for Cloud security alerts](https://learn.microsoft.com/en-us/azure/defender-for-cloud/alerts-overview) (~20 min) — the Azure equivalent; note the structural parity (finding type, severity, evidence) so the model transfers across clouds.

**Sigma — detection-as-code for the gap (~1.5 hrs)**
- [Sigma — rule structure & detection logic](https://sigmahq.io/docs/basics/rules.html) (~30 min) — read the Detection section and `condition`/temporal correlation. This is the format your judgment ships in.
- [SigmaHQ — CloudTrail rule collection](https://github.com/SigmaHQ/sigma/tree/master/rules/cloud/aws) (~1 hr) — read 8–10 real rules. For each, mentally run it against a CloudTrail event: what must match to fire, and what benign thing might *also* match? Study how the good rules document `falsepositives`.

## Key concepts
- Management events (default, free) vs. data events (off by default, costly) — and that T1530/S3 exfil is invisible without data events on
- A detection is a hypothesis scored on a 99.99%-benign stream; **precision, not recall, is the product**
- A rule that fires correctly but noisily is muted by week two — a muted rule is no coverage at all
- Sequence + qualifying context (`CreateUser` → `AttachUserPolicy(AdministratorAccess)` in 5 min from a non-CI IP) turns benign atoms into a signal
- Sigma structure: `logsource`, nested-field `detection`, temporal `condition`, and a reasoned `falsepositives` block
- Native detector as baseline, Sigma for the gap — and **every rule tuned against benign traffic before trust**

## AI acceleration
Hand a model a plain-English detection ("alert when a role is assumed from an unexpected region, then a
bucket policy is changed") and it will draft a passable Sigma rule in seconds — it knows the syntax and
the common field names. That's the cheap 80%. The expensive, owned 20% is the part the model can't do
for you: it doesn't know *your* benign baseline, so its `falsepositives` block is generic and its rule
is almost always too broad. Run its draft against the lab's benign events; watch it false-fire; then
tighten it and write the FP analysis from what you saw. The judgment-as-code here is the tuned rule plus
the explicit "what this must NOT fire on" — that's yours to own, not the model's to guess.
