# Module 02 — Cloud Identity & IAM

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *in the cloud, identity is the perimeter — and most of the misconfiguration lives here.*

## Why this matters
Network perimeters dissolve in the cloud; what you can do is entirely defined by IAM. Every breach
investigation that starts with "how did they get in?" arrives at a policy, a role, or a trust
relationship that was too permissive. The IAM surface is also the most reliably enumerable part of
the cloud estate — and `cloudfox` makes it tractable at scale. This module is the prerequisite for
everything that follows in offensive and defensive cloud work.

## Objective
Use `cloudfox` to enumerate IAM users, roles, and policies in a deliberately misconfigured AWS
environment, identify the specific policy statements that violate least privilege, and describe at
least two privilege-escalation vectors the configuration enables.

## The core idea
AWS IAM is an authorisation system that answers a single question: is this identity allowed to
perform this action on this resource, right now, given all the context? The deceptive part is
"all the context" — an answer isn't determined by one policy document but by the *intersection* of
identity-based policies, resource-based policies, permission boundaries, service control policies
(SCPs), and session policies. Strip any one of those layers away and you get a different effective
permission. This is why pasting a policy into a chatbot and asking "is this safe?" is unreliable: the
bot sees one piece of a multi-layer evaluation, and the dangerous interaction is almost always between
two layers, not visible in any single document.

The conceptual model that makes IAM legible is to think of it as a default-deny firewall with an
ordered rule chain. Unless an explicit Allow exists, nothing is permitted. An explicit Deny anywhere
in the chain wins regardless of Allows (with one exception: resource-based policies and
cross-account access have additional nuance). The reason so many IAM configurations are
over-permissive isn't that engineers set out to grant too much — it's that the abstraction
layers (managed policies, inline policies, role chaining) obscure the cumulative grant. You attach
`AmazonS3FullAccess` to unblock a developer, attach `PowerUserAccess` for the prod deploy role, and
nobody revisits either once the immediate need is met. The effective permissions drift upward over
time and are never reviewed as a whole.

The trust policy is the piece that trips people up most. An IAM role's trust policy specifies *who
can assume the role* — which AWS services, which other accounts, which specific ARNs. A trust policy
with `"Principal": "*"` allows any principal in the AWS universe (including accounts you don't
control) to attempt assumption, limited only by any conditions you've attached. A trust policy with
`"Principal": {"AWS": "arn:aws:iam::123456789012:root"}` allows any IAM identity in account
`123456789012` — that's every user and role in the account, not just a specific one. Neither of
these is necessarily wrong in a specific context, but both are routinely wrong in practice because
they were copy-pasted without understanding the scope. Trust policies deserve the same scrutiny as
permission policies.

Where this converges with the attacker's view: privilege escalation through IAM is not about
exploiting bugs — it's about following chains of legitimate API calls that, taken together, land an
identity at a higher permission set. The canonical path: a developer user has `iam:PassRole` and
`ec2:RunInstances`; they can launch an EC2 instance attached to any role they can pass — including
the admin role. That's not a vulnerability in IAM; it's two legitimate permissions that compose into
root. `cloudfox` is purpose-built to surface exactly these compositions at speed, which is why it
appears in both red team and cloud security assessment toolkits.

## Learn (~4 hrs)

**IAM fundamentals (~1.5 hrs)**
- [AWS IAM Policy Evaluation Logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) — the authoritative walkthrough of how AWS evaluates the full policy chain. This is the primary source; read the flow diagram and the "policy evaluation steps" section carefully.
- [AWS IAM — Actions, Resources, and Condition Keys Reference](https://docs.aws.amazon.com/service-authorization/latest/reference/reference_policies_actions-resources-contextkeys.html) — the canonical reference for what each AWS service exposes as IAM actions. Bookmark it; you'll return to it every time you read a policy.

**Misconfiguration patterns (~1 hr)**
- [AWS — IAM Security Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html) — the official best-practice checklist. Work through it as a gap analysis against what you'll see in the lab environment — most Meridian findings will map to a specific item here.
- [Rhino Security Labs — AWS IAM Privilege Escalation Methods](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/) — a methodical breakdown of 21 real IAM escalation paths with their required permissions. Read the first five in detail; the rest are reference.

**cloudfox (~1.5 hrs)**
- [cloudfox GitHub — README and usage](https://github.com/BishopFox/cloudfox) — tool overview, install, and the commands you'll run: `cloudfox aws --profile <p> iam-simulator`, `permissions`, and `role-trusts`. Read the AWS section.

## Key concepts
- IAM as a default-deny, multi-layer policy evaluation (identity policy + resource policy + SCP + boundary)
- The difference between identity-based and resource-based policies, and why both must be reviewed
- Trust policies: who can assume a role, and the common scope mistakes (`*`, account root)
- How `iam:PassRole` + a launch action composes into privilege escalation
- `cloudfox` as an enumeration accelerator for the IAM surface

## AI acceleration
Ask a model to explain a complex IAM policy and flag any privilege-escalation risks. Models are
genuinely useful here: they'll spot `iam:PassRole`, `iam:CreateAccessKey`, `sts:AssumeRole` with
loose conditions. But they cannot evaluate the full context — permission boundaries, the SCP chain
above, what roles are assumable with the flagged PassRole. Treat the model as a first-pass escalation
detector; validate every hit with `cloudfox` or the [AWS IAM Policy Simulator](https://policysim.aws.amazon.com/)
before you report it.
