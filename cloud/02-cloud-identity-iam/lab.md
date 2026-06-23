# Lab 02 — Blast Radius & the Minimum Cut: Prove a Key's Reach, Then Close It

*Variant D · breach-driven, audit→build. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[LocalStack](https://localstack.cloud/) to simulate AWS locally — no cloud account or real credentials.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/02-cloud-identity-iam
make up         # build + seed LocalStack with the misconfigured IAM
make demo       # worked enumeration walkthrough
make shell      # drop into the container (cloudfox + awslocal) to work
make down       # stop when done
```

**What this lab is — and isn't (read this).** **LocalStack CE does not *enforce* IAM** — a denied call
won't actually bounce, so you can't prove "the wall holds" by brute-forcing the API. That's fine,
because the skill here isn't exploitation; it's **judgment, proven.** You prove reach with
`awslocal iam simulate-principal-policy`, which runs AWS's real policy-evaluation logic and returns
`allowed` / `explicitDeny` / `implicitDeny` *and why*. So "she can reach it" and later "the path is now
closed" are both **logical evaluations**, not lucky API calls. Honest tool, honest answer.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against a simulated account you own.

## Scenario
The target account has handed you their AWS account after a near-miss: a developer laptop was lost with
an access key on it. The account grew organically — policies created on demand, roles cloned from each
other, no trust-policy review. You hold `dev-alice`'s credentials, the same shape of key Code Spaces lost.
Your deliverable is a **blast-radius finding plus the fix**: prove how far the key reaches, then author
the least-privilege policy that cuts the dangerous reach without breaking her real job, and prove the cut
holds.

Each step runs the same rhythm: **Predict** (commit before you touch anything) → **Do** (gather/prove
the evidence) → **Reveal** (check your call) → **Record** (one line in the report).

## Do

### Part 1 — Predict the reach, then prove it

1. [ ] **Map the principals.** Enumerate users and roles
   (`awslocal iam list-users`, `awslocal iam list-roles`) and `dev-alice`'s attached policy
   (`DevPolicy`). **Predict** before reading it: how far past "dev" does her key reach?
   **Reveal:** `s3:*` on `*`, `ec2:RunInstances`, and `iam:PassRole` on `*`. **Record:** the label said
   "dev"; the grant says "account."

2. [ ] **Prove the S3 blast radius — not just her bucket.** Create a second, unrelated bucket
   (`awslocal s3api create-bucket --bucket payroll-prod`), then run
   `awslocal iam simulate-principal-policy` for `dev-alice` on `s3:DeleteObject` against **both**
   `uploads-dev` and `payroll-prod`. Both return `allowed`. This is the Code Spaces
   reach: one key, every bucket, **delete** included. **Record:** owner of finding = customer (the policy
   scope); the key reaches and can destroy data it has no business touching.

3. [ ] **Prove the escalation — the reach that grants more reach.** `dev-alice` has `iam:PassRole` on `*`
   and `ec2:RunInstances`. Confirm with the simulator that she is `allowed` to `iam:PassRole` on the
   admin instance role (`EC2AdminRole`). **Reveal:** that's the canonical compose — launch an
   instance attached to that role and the key *becomes* admin. No exploit; two legitimate grants. (Use
   `cloudfox aws --profile localstack iam-simulator ...` to corroborate.) **Record:** this is the hop
   that turns a lost laptop into a dead company.

4. [ ] **Check the trust walls (federation footnote).** Read the trust policies:
   `AdminRole` trusts `...:root` (the **whole** account, every principal), and `CICDRole`'s
   OIDC trust has **no `sub` condition** (every GitHub Actions workflow from the provider). **Predict
   then Reveal:** "root" and "no sub" look like scoping but trust *everyone* in their class — the same
   over-trust that, with a forged signing key, is Golden SAML. **Record** one line per role.

### Part 2 — Cut it to the minimum, and prove the cut holds

Tracing the reach is the finding; **cutting it without breaking dev-alice's real job is the fix** — and
in IAM a fix is only real when you can *prove* it by evaluation.

5. [ ] **See the reach as policy logic.** Run `make check-escalation` — a `simulate-principal-policy`
   harness over the original `DevPolicy`. The two dangerous assertions report `allowed`
   (`iam:PassRole` on the admin role, and on `*`); the two legitimate ones (`ec2:DescribeInstances`, an
   S3 read on the dev bucket) also `allowed`. The escalation, expressed as evaluable permissions.

6. [ ] **Author the minimum cut.** Edit `data/dev-alice-fixed-policy.json` (a reference solution is
   bundled — try it yourself first). Apply the rulebook from the README: scope `iam:PassRole`'s
   `Resource` from `*` to a single **non-admin** role (`arn:aws:iam::000000000001:role/AppRole`)
   so she can no longer pass `EC2AdminRole`; scope `s3` to the dev bucket and drop delete where
   she doesn't need it. **The smallest change that breaks the path** — keep her real EC2/IAM-read access.

7. [ ] **Prove the path is closed.** Run `make check-fixed`. All four assertions must pass the *verdict*:
   the two PassRole-escalation paths now return `implicitDeny`/`explicitDeny`, while
   `ec2:DescribeInstances` and the dev-bucket read still return `allowed`. If a legitimate assertion
   flipped to denied, you cut too much — that's the whole craft of the minimum cut. Optionally
   `make apply-fixed` pushes the policy to LocalStack as a new default version and re-enumerates so you
   see the change land the way it would in a real account.

8. [ ] **(In-lab stretch) Close the trust walls too.** Rewrite `AdminRole`'s trust to a specific
   role/user instead of `root`, and add a `repo:org/name:ref` `sub` condition to the CICD OIDC trust.
   Note in the report why each original trusted "everyone in its class."

## Success criteria — you're done when
- [ ] You proved with `simulate-principal-policy` that `dev-alice` is `allowed` to delete a bucket she has
  no business touching **and** to `iam:PassRole` the admin role — the full blast radius.
- [ ] You can state the escalation as a compose (`iam:PassRole` + `ec2:RunInstances` → admin) and name the
  minimum cut that breaks it.
- [ ] Your `dev-alice-fixed-policy.json` makes the checker pass: both escalation assertions now **deny**,
  both legitimate-access assertions still **allow** — and you can say in one sentence why scoping the
  `iam:PassRole` *resource* is the minimum cut.
- [ ] You scored your three "Call it" predictions from the README against the reveals.

## Deliverables
`blast-radius-report.md` — per principal: the proven reach (with the simulator verdict that demonstrates
it), the escalation chain, the trust-policy finding, and the remediation. `dev-alice-fixed-policy.json` —
your least-privilege policy that passes the checker. Commit both. Do not commit credentials, bucket
contents, or any real account data.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your finding is "this key can pass the admin
role." Encode that verdict as a **guardrail that fails the bad state and passes the fix**: a small check
(`assert_no_escalation.py`) that, given an IAM policy, asserts via `simulate-principal-policy` (or static
analysis equivalent to a Checkov rule) that the principal is **denied** `iam:PassRole` on any admin-class
role and **denied** `s3:*`/`Resource:"*"`, while still **allowed** its legitimate actions — exit non-zero
on the original `DevPolicy`, exit zero on your fix. Run it against both and show it flips. Have a
model draft the assertions; review every line and confirm it fails the original for the *right* reason
(the PassRole reach, not an unrelated nit). This is your verdict made un-recurrable — and the seed of the
attack-path checker you'll extend in module 03.

## AI acceleration
Paste `DevPolicy` and a role's trust policy into a model and ask: "What's the blast radius and
which escalation paths and ATT&CK-for-Cloud techniques apply?" It's reliable on the common composes
(PassRole+RunInstances, CreateAccessKey on another user) but sees one layer — it can't know what an SCP or
boundary caps. Validate each claim with `simulate-principal-policy`. Then paste your guardrail and ask it
to author a policy that sneaks past — if it can, your rule is too narrow.

## Connects forward
The principals and edges you proved here become the nodes of the privilege-escalation **graph** in module
03 (IAM Attack Paths), where pmapper/cloudfox turn this manual trace into graph search and the "minimum
cut" becomes a graph operation. The over-broad grants feed posture auditing in module 05, and the
simulator-as-guardrail pattern returns as IaC scanning in module 06.

## Marketable proof
> "Given a leaked cloud principal, I predict and *prove* its blast radius with `simulate-principal-policy`
> — including `iam:PassRole` escalation to admin — then author the minimum-cut least-privilege policy and
> prove by evaluation that the dangerous reach is denied while the principal's real job still works.
> I can explain why explicit-deny beats allow and why a `root` trust trusts the whole account."

## Stretch
- Add the `iam:CreateAccessKey`-on-another-user escalation to your enumeration and guardrail — a different
  vector from PassRole.
- Re-run the whole loop against a CloudGoat `iam_privesc_by_*` scenario in a real (free-tier) account and
  compare how `simulate-principal-policy` behaves when IAM is actually enforced versus LocalStack's logical-only mode.
