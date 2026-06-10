# Module 01 — Cloud Fundamentals & Shared Responsibility

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *before you can attack or defend the cloud, you have to know who owns what.*

## Why this matters
Every cloud breach investigation eventually arrives at the same question: was that a failure of the
provider, or of the customer? The answer determines what you can fix, who you escalate to, and whether
you were even responsible. Getting shared responsibility wrong is how SOCs miss detections they should
own, and how engineers ship workloads with the default "the cloud handles it" assumption that attackers
count on. This module is the frame every other cloud module hangs on.

## Objective
Enumerate a simulated AWS account using the CLI, identify the IAM policies and resource configurations
that define the customer's responsibility boundary, and articulate what the provider guarantees vs. what
you own for at least three service types (IaaS, PaaS, SaaS).

## The core idea
The shared responsibility model is the cloud's load-bearing conceptual structure — and it's genuinely
unintuitive until you think about it in terms of the managed-service spectrum. At one end, IaaS (raw EC2
instances) looks like a rented data-centre rack: AWS physically secures and virtualises the hardware, and
you own the OS, the patches, the firewall rules, the keys, and everything running on top. At the other end,
SaaS (think AWS WorkMail or Salesforce) hands you a running application; your surface is the identity
configuration and data governance. PaaS (Lambda, RDS) sits in between — the runtime is managed, but the
execution role's permissions, the code the function runs, and the data it touches are entirely yours.
The mental model that makes this stick: **draw a horizontal line through the stack; everything above the
line is yours, everything below is the provider's — and the line moves depending on the service type.**

What the model *doesn't* say is that the boundary is always clear. Misconfigurations regularly live in
the gap between provider default and secure customer config — an S3 bucket that the provider's default
left public, an RDS instance where you enabled public accessibility without realising it, an IAM role
with a trust policy that any principal in the account can assume. These aren't provider bugs; they're
customer-side responsibilities that look like provider defaults. **The dangerous assumption is that a
default is secure.** AWS, GCP, and Azure ship permissive defaults in many places precisely because the
alternative is blocking legitimate use cases. The responsibility model does not excuse defaults from
scrutiny.

There's a second layer that trips up even experienced engineers: **the control plane vs. the data plane.**
IAM controls who can call the API (the control plane — the CloudTrail-logged, auditable surface). S3
access policies, VPC security groups, and object ACLs control what flows through the service (the data
plane). Both are the customer's responsibility, but they're controlled differently, fail differently, and
are logged differently. A GuardDuty finding about API abuse and a VPC flow log finding about data
exfiltration represent the same breach at two different planes — and the detective controls are different.
Understanding this split is what separates a cloud security practitioner from someone who just reads the
shared responsibility FAQ.

The practical starting point for any cloud engagement — offensive or defensive — is account enumeration:
what's deployed, how it's configured, and what relationships it implies. The CLI is the lingua franca here.
`aws`, `gcloud`, and `az` are the read-side of the control plane; every specialised cloud security tool
ultimately calls the same APIs under the covers. Knowing how to enumerate IAM policies, list resources by
region, and spot the misconfigurations the console hides behind coloured icons is the foundation skill.
The lab makes this concrete with a simulated AWS environment seeded with the kind of "it was the default"
misconfiguration Meridian Financial's team found on their first audit.

## Learn (~3 hrs)

**Shared responsibility (~1 hr)**
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/) — the definitive primary source; read the full page, not just the diagram. Note how the boundary shifts between EC2, RDS, and S3.
- [CISA Cloud Security Technical Reference Architecture (TRA), section 2](https://www.cisa.gov/resources-tools/resources/cloud-security-technical-reference-architecture) — a US-government synthesis of shared responsibility across all three hyperscalers; section 2 maps the model to concrete services.

**AWS account structure & CLI (~1.5 hrs)**
- [AWS CLI Getting Started](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) — installation and credential setup; follow the "install" and "configure" sections.
- [AWS CLI Command Reference: IAM](https://docs.aws.amazon.com/cli/latest/reference/iam/) — the enumeration commands you'll use: `list-users`, `list-roles`, `get-policy`, `get-policy-version`. Skim the structure before the lab.

**Threat framework orientation (~0.5 hr)**
- [MITRE ATT&CK for Cloud — Tactics overview](https://attack.mitre.org/matrices/enterprise/cloud/) — look at the tactic columns; each one maps to a phase of an attack that crosses one of the responsibility layers you just studied.

## Key concepts
- The shared responsibility model as a spectrum (IaaS → PaaS → SaaS), not a binary split
- Customer-owned vs. provider-owned surface for EC2, S3, RDS, and Lambda
- "Default is not secure" — permissive defaults are customer responsibility to harden
- Control plane (IAM/API) vs. data plane (flow logs, object policies) and why both matter
- CLI as the ground-truth interface to the control plane

## AI acceleration
Paste an IAM policy document into a model and ask it to identify overly-broad permissions and whether
the actions map to ATT&CK techniques. The model is reliable at spotting `*` wildcards and unused
actions — but it cannot see the effective permissions that arise from permission boundaries, SCPs, and
resource policies all layered together. Treat its output as a first-pass triage list; validate each
finding against the actual policy evaluation logic before escalating. You own the conclusion.
