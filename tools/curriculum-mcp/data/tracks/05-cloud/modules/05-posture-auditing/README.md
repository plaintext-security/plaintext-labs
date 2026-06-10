# Module 05 — Posture & Misconfiguration Auditing

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *your account is never as locked down as you think it is.*

## Why this matters
Every AWS account accumulates drift: a public S3 bucket from a quick demo, a security group opened
"temporarily," a root account that still has no MFA. Individually each one looks minor. Together they
are the attack surface that makes breach investigations awkward. Posture management is the discipline
of continuously measuring your configuration against known-safe baselines — and doing it with code so
it runs without human discipline.

## Objective
Run `prowler` and ScoutSuite against a misconfigured AWS account, triage findings by severity, and
produce a written remediation plan that maps each gap to a CIS benchmark control.

## The core idea

Cloud security posture management (CSPM) rests on one insight: misconfigurations cause more breaches
than software vulnerabilities in cloud environments. The Verizon DBIR has said it for years; the
Capital One, Toyota, and dozens of less-publicised breach post-mortems confirm it. The attack is
rarely exotic — it's an IAM user key committed to a public repo, an S3 bucket that serves files to
the whole internet, or an EC2 instance whose metadata endpoint hands a role token to anyone who can
send it a request. The misconfiguration was already there; the attacker found it before the owner did.

The response is benchmarking — not the document you file for a compliance audit, but the automated
check you run every day. CIS (Center for Internet Security) publishes scored benchmarks for AWS, GCP,
and Azure: a numbered list of controls with a rationale, the API check that tests it, and the fix.
`prowler` implements those checks (and several hundred more mapped to NIST 800-53, SOC 2, PCI-DSS,
and MITRE ATT&CK for Cloud) as a CLI you can run in a container. The output is a ranked list of your
gaps. ScoutSuite does the same job from a different angle — it collects a snapshot of your entire
account's configuration and renders it as a static HTML report you can walk a CTO through.

The mental model that separates a posture audit from a compliance checkbox is **risk triage**. A
medium finding on your production payment-processing account is not the same as a high finding on a
sandbox you spun up last week. Context is the job: who owns this resource, what data lives in it,
is it reachable from the internet, and does the blast radius include a compliance boundary? Tools
give you findings; you supply the asset context and make the call. The deliverable is not a PDF —
it's a prioritised backlog with an owner and a timeline.

One more practitioner reality: running a full posture audit the first time is humbling. A real AWS
account that has been active for a year will return hundreds of findings. Resist the instinct to
close them all by suppressing the rule. The right move is to triage ruthlessly — distinguish hygiene
issues (old access keys) from architectural misconfigurations (public bucket + data in it) from
actual misses (logging disabled). The architectural misconfigurations are the ones worth a sprint.

## Learn (~4 hrs)

**CIS benchmarks and the posture model (~1 hr)**
- [CIS Amazon Web Services Foundations Benchmark — summary landing page](https://www.cisecurity.org/benchmark/amazon_web_services) — the scored standard `prowler` implements. Skim the control families (Identity, Logging, Networking, Monitoring) to understand the structure before you read findings.
- [MITRE ATT&CK for Cloud — resource-hijacking and initial access](https://attack.mitre.org/matrices/enterprise/cloud/) — filter to Initial Access and Persistence to see which ATT&CK techniques a posture gap enables. Worth 20 minutes to map the mental model.

**Prowler (~1.5 hrs)**
- [Prowler docs — getting started](https://docs.prowler.com/introduction) — installation, authentication, running a scan, filtering by severity and compliance framework. Read the "Quick Start" and the "Output formats" sections.
- [Prowler GitHub — prowler-cloud/prowler](https://github.com/prowler-cloud/prowler) — the full check library. Browse `checks/aws/` to understand what each finding actually tests; this is the fastest way to learn what good configuration looks like.

**ScoutSuite (~1 hr)**
- [ScoutSuite — nccgroup/ScoutSuite](https://github.com/nccgroup/ScoutSuite) — NCC Group's multi-cloud auditor. Read the README for the auth model, then skim the `providers/aws/` source to see how it collects account state.

**Remediation and risk triage (~0.5 hr)**
- [AWS Security Hub — Automated Security Checks](https://docs.aws.amazon.com/securityhub/latest/userguide/securityhub-findings.html) — how AWS's native service structures findings. Useful context for how findings flow in a production environment beyond CLI tools.

## Key concepts
- CIS Benchmark structure: scored vs. not scored, Level 1 vs. Level 2
- CSPM: continuous configuration assessment vs. point-in-time penetration test
- Finding triage: severity × asset criticality × blast radius
- Common high-value gaps: public S3, open security groups, root MFA, CloudTrail disabled, access key rotation
- MITRE ATT&CK for Cloud: T1078 (Valid Accounts), T1530 (Data from Cloud Storage)

## AI acceleration
Paste a prowler JSON finding into a model and ask it to explain the risk and draft a Terraform
remediation block — it's fast and usually correct. Your job is to check that the Terraform matches
your naming conventions, that the remediation doesn't break a dependency you know about, and that
the finding is actually in scope (suppression has to be a conscious decision, not an AI shortcut).
For large finding sets, ask the model to group findings by resource and draft a prioritised backlog;
review the priority order against your actual asset criticality, which the model can't know.
