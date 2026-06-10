# Lab 02 — IAM Enumeration with cloudfox

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo.
The environment uses LocalStack (simulated AWS) seeded with a deliberately misconfigured Meridian
Financial IAM configuration, and runs `cloudfox` inside the container against it.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/02-cloud-identity-iam
make up        # build + seed LocalStack with misconfigured IAM
make demo      # run the cloudfox enumeration walkthrough
make shell     # drop into the container to work interactively
make down      # stop when done
```

The container includes `cloudfox` (pre-built binary) and `awslocal`. The LocalStack environment is
seeded with three IAM principals — a developer user, a CI/CD role, and an admin role — with the
kind of over-broad permissions and loose trust policies that appear in real first-audit engagements
at organisations that have grown their cloud usage organically.

> Everything runs locally against a simulated environment you own. No real AWS account needed.

## Scenario
Meridian Financial's security team has engaged you to do an IAM audit of their AWS account. The
account predates their security programme: policies were created on demand, roles were cloned from
each other, and nobody has done a full trust-policy review. Your job is to enumerate the account
with `cloudfox`, identify misconfigured policies and trust relationships, and document two concrete
privilege-escalation paths that an attacker with `dev-alice`'s credentials could follow.

## Do
1. [ ] **Enumerate permissions for all principals.** Run `cloudfox` to list the effective permissions
   for every user and role in the account. Hint:
   `cloudfox aws --profile localstack permissions --output table 2>/dev/null`.
   Which principals have `iam:*` or `iam:PassRole` in their grants?

2. [ ] **Inspect role trust policies.** Use `cloudfox` or `awslocal` to retrieve the trust policy
   for each role. Hint: `cloudfox aws --profile localstack role-trusts --output table`.
   Which role can be assumed by any principal in the account (trust principal is the account root)?
   Why is that dangerous even though it looks like a restriction?

3. [ ] **Trace the escalation path from dev-alice.** `dev-alice` has `iam:PassRole` and
   `ec2:RunInstances`. Walk through the steps an attacker would take to reach admin privileges.
   No need to execute the attack — describe the chain: which API calls, in what order, using which
   role. Write this in `findings.md`.

4. [ ] **Check the CI/CD role's trust policy.** The CI/CD role is trusted by the developer account
   (simulated). Is the trust scoped to a specific OIDC subject (`sub` claim) or to any identity
   from the provider? Why does an unscoped OIDC trust allow any pipeline in the org to assume
   the role?

5. [ ] **Run `cloudfox iam-simulator`.** Use the simulator command to verify that `dev-alice` can
   perform `iam:PassRole` on `*`. Hint:
   `cloudfox aws --profile localstack iam-simulator --principal arn:aws:iam::000000000001:user/dev-alice --action iam:PassRole --resource '*'`.
   Does it confirm the grant?

6. [ ] **Run `make demo`** and compare the worked output to your manual findings.

## Success criteria — you're done when
- [ ] You can name every principal that has `iam:PassRole` and the resource scope it covers.
- [ ] You've documented the trust policy issue on at least one role.
- [ ] You've traced a step-by-step privilege-escalation path from `dev-alice` to admin.
- [ ] `cloudfox iam-simulator` confirms at least one dangerous permission grant.

## Deliverables
`findings.md` — a structured IAM audit report with: principal, finding type (over-broad policy /
loose trust / escalation path), severity (High/Medium), and the specific API call chain that
demonstrates the risk. Commit this file. Do not commit real credentials or real AWS data.

## Automate & own it
**Required.** Write a Python script (`audit_iam.py`) that calls `awslocal` (via `subprocess` or the
`boto3` library with a LocalStack endpoint) to list users, list attached policies, and flag any
policy that contains `iam:PassRole` or `iam:*` with a wildcard resource. Have a model draft the
boto3 calls from your cloudfox output; you review every line, run it against LocalStack, and confirm
it finds the same issues as your manual enumeration. This script is the foundation of the IAM audit
automation you'll extend with attack-path logic in module 03.

## AI acceleration
Paste any role's trust policy and attached permission policy into a model and ask: "What
privilege-escalation paths does this configuration enable, and what ATT&CK technique IDs apply?"
Models are reliable on the common paths (PassRole + RunInstances, CreateAccessKey on another user).
Cross-check each path against [Rhino Security Labs' escalation list](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/)
to confirm the technique is real and the required permissions match.

## Connects forward
The misconfigured roles you enumerated here become the nodes in the privilege-escalation graph in
module 03 (IAM Attack Paths), where `pmapper` turns what you traced manually into a graph search.

## Marketable proof
> "I can enumerate cloud IAM with cloudfox, identify over-broad policies and loose trust
> relationships, and trace concrete privilege-escalation paths — the core skill of a cloud
> security assessment."

## Stretch
- Add an `iam:CreateAccessKey` call in your enumeration: which principals could create a new access
  key for another user and thereby pivot to that user's permissions? This is a different escalation
  vector from PassRole.
- Review the CI/CD role trust policy and write a corrected version that scopes the OIDC trust to
  a specific repository and branch `sub` claim. Commit the corrected policy document alongside
  your findings.
