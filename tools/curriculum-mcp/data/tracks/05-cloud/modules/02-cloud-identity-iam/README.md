# Module 02 — Cloud Identity & IAM

*Variant D · breach-driven, predict-the-blast-radius, audit→build ("trace the reach, then close it"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *in the cloud the perimeter is identity; one leaked key is a question of how much of the business it can touch.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 01 — Shared Responsibility](../01-cloud-fundamentals/README.md)
{ .module-meta }


## The case

In June 2014, **Code Spaces** — a code-hosting and project-management company that had run for seven
years — received an extortion email. The attacker already had access to the company's **Amazon EC2
control panel.** When Code Spaces tried to retake control by changing passwords, the attacker, still
holding valid credentials, began **deleting everything**: EC2 instances, S3 buckets, AMIs, EBS volumes,
and — fatally — **the backups, which lived in the same account.** Within roughly **twelve hours** most
of the company's data and infrastructure was gone. Code Spaces did not recover. Its own closing notice
told customers the damage was "unrecoverable" and that continuing would "cause irreparable harm" — the
company effectively ceased to exist.

There was no zero-day, no exotic exploit. The whole breach was **one set of credentials that could
reach the entire account**, including the one thing that was supposed to survive a bad day: the backups.
So before you read on, this module turns on a single question:

> **One leaked key. How much of the business can it actually touch — and how much of that is reversible?**

## Your job

By the end of this module you'll **predict a principal's blast radius, then prove it** — enumerate a
seeded over-broad identity, demonstrate its real reach with `iam simulate-principal-policy` (AWS's own
evaluation logic, not a guess), and then do the half that auditing alone skips: **author the
least-privilege policy that closes the path and re-simulate to prove the reach is gone.** That
audit→build loop — find the over-grant, cut it to the minimum, verify the cut holds — is the exact
motion of a cloud IAM assessment, and it is what makes the verdict yours instead of a finding you copied.

## Call it before you read on

Don't scroll. Write down your gut answers — being wrong here is the teaching event, and you'll grade
yourself in the lab.

> **Q1.** A developer's leaked access key is scoped "just for dev work." Realistically, how far past
> dev can it reach — its own bucket, the whole account, or somewhere in between?
>
> **Q2.** The attacker deleted the **backups** too. Why didn't a backup save Code Spaces — what made
> the blast *irreversible*?
>
> **Q3.** An IAM policy says `Allow s3:*`. Another, attached to the same role, says `Deny s3:Del*`.
> Can the principal delete an object?

## The blast radius, revealed

Hold your answers against these.

**Q1 — the reach is almost always wider than the label.** "Dev" is a name on a policy, not a boundary.
The grant that matters is `Action` × `Resource`, and the moment either is `*` the label stops meaning
anything. The over-broad developer policy you'll enumerate grants `s3:*` on `*` and `iam:PassRole` on
`*` — so "dev-alice" can read and delete *every* bucket in the account, and, far worse, **pass any role
to a service she controls.** `iam:PassRole` + `ec2:RunInstances` is the canonical escalation: launch an
EC2 instance attached to the admin role, and the instance — and through it, the attacker — *is* admin.
That isn't a bug in IAM; it's two legitimate permissions that **compose** into root. The blast radius of
a key is never what its name suggests — it's the transitive closure of everything its permissions can
reach, including the permissions it can grant itself. People reliably under-guess this, and the
under-guess is how a "dev" key ends a company.

**Q2 — the perimeter is identity, and there was only one of it.** Backups defend against deletion only
if the thing that can delete the primary **cannot also delete the backup.** Code Spaces' backups lived
in the *same* account, reachable by the *same* control-plane credentials — so a single identity with
account-wide power was a single point of failure for the entire business, recovery included.
This is the cloud's hard lesson: when access is identity, **the blast radius of one principal is the
intersection of its reach and your inability to recover from it.** Encryption, redundancy, and backups
are all silent against a principal you *authorized* to destroy them. The fix isn't "more backups" — it's
that no single principal should be able to reach both the system and its recovery path.

**Q3 — explicit deny wins, always.** This is the rulebook every wall in IAM obeys, and it's worth
memorizing because every guardrail you write depends on it. AWS evaluates a request as **default-deny**:
with no matching `Allow`, the answer is no (*implicit deny*). A matching `Allow` flips it to yes. But a
matching **explicit `Deny` anywhere in the chain overrides every `Allow`** — identity policy, resource
policy, SCP, boundary, session. So the order is **explicit deny > allow > implicit (default) deny.**
The principal in Q3 *cannot* delete: the `Deny s3:Del*` beats the `s3:*` allow. That ordering is what
makes least-privilege *enforceable* — you scope allows down to the minimum, and where you must keep a
broad allow, an explicit deny is the wall that holds regardless. In the lab, "the reach is gone" means
exactly this evaluation returns `implicitDeny`/`explicitDeny` for the dangerous action and `allowed`
for the legitimate one.

The federation footnote: the same evaluation governs *who can assume a role* via its **trust policy.**
A trust policy with `"Principal": {"AWS": "...:root"}` trusts **every** identity in the account, not one;
an OIDC trust with no `sub` condition trusts **every** workflow from the provider. When that trust is
forged or over-broad, the wall never even gets consulted — which is exactly how **Golden SAML** worked in
SolarWinds (a stolen token-signing key let attackers mint SAML assertions for *any* user, federating
straight past authentication). Same model — who can act, evaluated against policy — one layer up.

## Learn (~3 hrs)

*Richer than a foundations module: IAM evaluation is the load-bearing mechanism for the next three
modules, so it's worth the time. Read the case above first, then go deep on the mechanism.*

**The evaluation rulebook (~1 hr)**
- [AWS — IAM policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) (~30 min) — the primary source for explicit-deny > allow > implicit-deny. Read the flowchart and the "Determining whether a request is allowed or denied within an account" section; everything in this module is an application of that one diagram.
- [AWS — `simulate-principal-policy` (CLI reference)](https://docs.aws.amazon.com/cli/latest/reference/iam/simulate-principal-policy.html) (~15 min) — the command that *runs* that logic for you and returns `allowed`/`explicitDeny`/`implicitDeny`. This is how the lab proves a wall holds without LocalStack enforcing it.
- [AWS — Grant least privilege](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege) (~15 min) — the official best-practice section; treat it as the gap analysis checklist against the findings.

**The escalation that the reach hides (~1 hr)**
- [Rhino Security Labs — AWS IAM Privilege Escalation Methods](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/) (~40 min) — primary research cataloguing 21 real escalation paths. Read `iam:PassRole`+`RunInstances` and `CreateAccessKey` in detail; the rest is reference for module 03.
- [BishopFox — cloudfox README (AWS section)](https://github.com/BishopFox/cloudfox) (~20 min) — the enumeration accelerator; skim `permissions`, `role-trusts`, `iam-simulator` so the lab's commands are familiar.

**The federation footnote (~30 min)**
- [CISA — Emergency Directive 21-01 (SolarWinds / SUNBURST)](https://www.cisa.gov/news-events/directives/ed-21-01-mitigate-solarwinds-orion-code-compromise-closed) (~15 min, skim) — the federal response; orient on the trust-compromise angle.
- [CISA — guidance on detecting forged SAML tokens (Golden SAML)](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-008a) (~15 min) — why a stolen signing key defeats the trust wall entirely.

## Key concepts
- A key's blast radius is the *transitive closure* of its permissions — including the permissions it can grant itself (`iam:PassRole`, `CreateAccessKey`) — not the label on its policy
- IAM evaluation order is the rulebook every wall obeys: **explicit deny > allow > implicit (default) deny**
- `iam:PassRole` + a launch action (`ec2:RunInstances`, `lambda:CreateFunction`) composes two legitimate grants into admin
- Trust policies decide *who can assume a role*; `root` trusts the whole account, an unscoped OIDC trust trusts every workflow — Golden SAML forges past the wall entirely
- Single-principal, account-wide reach over both a system *and* its backups is what makes a blast irreversible (Code Spaces)
- Least privilege is verifiable: a fix is "proven" only when `simulate-principal-policy` denies the dangerous action *and* still allows the legitimate one

## AI acceleration
Hand a model the over-broad developer policy and ask it to enumerate the blast radius and escalation
paths *before* you do. It's a strong first-pass escalation detector — it will reliably flag
`iam:PassRole` and `s3:*` on `*`. But it sees one document, and IAM is a multi-layer evaluation: it
cannot tell you whether an SCP or permission boundary above caps the grant, or whether a `Deny` you
didn't paste already closes the path. Treat its output as a hypothesis and validate every hit with
`simulate-principal-policy`, which runs AWS's real logic. The skill the model can't do for you is the
*minimum cut* — author the smallest policy change that denies the dangerous action without breaking the
principal's real job, then prove it. You direct it; you own the verdict.
