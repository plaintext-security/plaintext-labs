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

### Part 1: Enumerate — find the escalation
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

### Part 2: Close it — author the least-privilege policy and prove it
Tracing the escalation is the finding; cutting it without breaking dev-alice's real job is the fix.
`check_escalation.py` evaluates the IAM policy semantics and reports PASS/FAIL — so you can *prove*
the escalation is closed, not just claim it.

7. [ ] **See the escalation as policy logic.** Run `make check-escalation` (the checker against
   dev-alice's original policy). Two assertions FAIL: she can `iam:PassRole` the EC2 **admin** role
   and `*` — the escalation, expressed as a permission the checker can evaluate. The two legitimate
   assertions PASS.

8. [ ] **Author the minimum-cut fix.** Recall from the IAM-attack-paths idea that you want the
   *smallest* change that breaks the path. Edit
   `data/dev-alice-fixed-policy.json` (a reference solution is bundled — try it yourself first):
   scope the `iam:PassRole` statement's `Resource` from `*` to a single **non-admin** role ARN
   (`arn:aws:iam::000000000001:role/MeridianAppRole`) so dev-alice can no longer pass
   `MeridianEC2AdminRole`. Keep her legitimate S3 (scope it to the dev bucket), EC2, and IAM-read
   access. One edge cut closes the path.

9. [ ] **Prove the path is closed.** Run `make check-fixed`. All four assertions must PASS: the two
   PassRole-escalation paths now DENY, while `ec2:DescribeInstances` and the dev-bucket S3 read still
   ALLOW. If a legitimate assertion flipped to FAIL, you cut too much. Optionally, `make apply-fixed`
   pushes your policy to LocalStack as a new default version and re-enumerates, so you see the change
   land the way it would in a real account.

10. [ ] **(Stretch in-lab) Fix the trust policies too.** The `MeridianAdminRole` trusts the account
    root and `MeridianCICDRole`'s OIDC trust has no `sub` condition. Rewrite each trust policy to the
    least-privilege principal (a specific role/user; a specific `repo:org/name:ref` sub) and note in
    `findings.md` why the original was exploitable.

## Success criteria — you're done when
- [ ] You can name every principal that has `iam:PassRole` and the resource scope it covers.
- [ ] You've documented the trust policy issue on at least one role.
- [ ] You've traced a step-by-step privilege-escalation path from `dev-alice` to admin.
- [ ] Your `dev-alice-fixed-policy.json` makes `check_escalation.py` exit 0 — both PassRole-escalation
  assertions now DENY while the two legitimate-access assertions still ALLOW.
- [ ] You can state, in one sentence, why scoping the `iam:PassRole` *resource* is the minimum cut
  that breaks the path.

## Deliverables
`findings.md` — a structured IAM audit report with: principal, finding type (over-broad policy /
loose trust / escalation path), severity (High/Medium), the specific API call chain that demonstrates
the risk, and the remediation. `dev-alice-fixed-policy.json` — your least-privilege policy that passes
the checker. Commit both. Do not commit real credentials or real AWS data.

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
> "I enumerate cloud IAM with cloudfox, trace concrete privilege-escalation paths like PassRole, and
> then *remediate* — authoring the minimum-cut least-privilege policy and proving with a policy
> evaluation that the escalation is closed and the principal's real access still works."

## Stretch
- Add an `iam:CreateAccessKey` call in your enumeration: which principals could create a new access
  key for another user and thereby pivot to that user's permissions? This is a different escalation
  vector from PassRole.
- Review the CI/CD role trust policy and write a corrected version that scopes the OIDC trust to
  a specific repository and branch `sub` claim. Commit the corrected policy document alongside
  your findings.
