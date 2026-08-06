# Lab 02 — Blast Radius & the Minimum Cut: Prove a Key's Reach, Then Close It

> **Hands-on lab.** Environment: `plaintext-labs/cloud/02-cloud-identity-iam` (floci). Objective:
> **predict `dev-alice`'s blast radius, prove it by evaluation, then author the minimum-cut policy that
> denies the dangerous reach while her real job still works — and prove the cut holds.** Target:
> **~90 min**, one finish line. *[← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Blast radius is the *transitive closure*, not the label.** | "dev" is a name, not a boundary — the reach includes the permissions the key can grant *itself*. |
| 2 | **`iam:PassRole` + `ec2:RunInstances` composes into admin.** | Two legitimate grants, no exploit — launch an instance carrying an admin role and the key *is* admin. |
| 3 | **The rulebook: explicit deny > allow > implicit (default) deny.** | A fix is "proven" only when evaluation *denies* the dangerous action and still *allows* the legitimate one. |
| 4 | **One account = one point of failure — reach over the system *and* its backups.** | Code Spaces died in 12 hrs because one credential could delete data *and* the backups beside it. |
| 5 | **A trust policy is a wall too.** | `"...:root"` trusts every identity in the account; an OIDC trust with no `sub` trusts every workflow. |
| 6 | **floci does not *enforce* IAM — you prove reach by evaluation.** | A denied call won't bounce locally; the skill is judgment made provable, not a lucky API call. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [blast radius, revealed](README.md#the-blast-radius-revealed) and the
> [evaluation rulebook](README.md#go-deeper-3-hrs-optional).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A key's policy is named "dev." Name the **two things** that actually bound its blast radius (not the
   label), and the one permission that lets a key *widen its own* reach.
2. A role has `Allow s3:*` and `Deny s3:Del*` attached. Can it delete an object — and which rule decides?

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[floci](https://github.com/floci-io/floci), a free, MIT-licensed local AWS emulator, to simulate AWS on
`localhost:4566` — no cloud account or real credentials required. (floci replaces LocalStack, whose
community edition sunset in March 2026.)

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/02-cloud-identity-iam
make up         # build + seed floci with the misconfigured IAM
make demo       # worked enumeration walkthrough
make shell      # drop into the container (cloudfox + aws) to work
make down       # stop when done
```

**What this lab is — and isn't (read this).** **A local emulator does not *enforce* IAM** — a denied
call won't actually bounce, so you can't prove "the wall holds" by brute-forcing the API. That's fine,
because the skill here isn't exploitation; it's **judgment, proven.** Where floci won't enforce, you
prove reach by **evaluation**: `make check-escalation` runs `check_escalation.py`, which applies AWS's
real order (explicit deny > allow > implicit deny) to a policy and returns `PASS`/`FAIL` *and why*. The
same reasoning is what `aws iam simulate-principal-policy` returns against a **real AWS account you own**
(`allowed` / `explicitDeny` / `implicitDeny`) — because the lab drives plain `aws` via
`AWS_ENDPOINT_URL`, the identical steps later run there to watch enforcement live. Honest tool, honest
answer.

> **▸ On track if:** `make demo` prints the `dev-alice`/`dev-bob` user table, the roles table with their
> trust principals, `AdminRole`'s trust on `...:root`, `CICDRole`'s OIDC trust with **no `sub`**, and the
> `check_escalation.py` run — **two `[FAIL] ALLOW` lines** on the original `DevPolicy` (the PassRole
> escalation), then **all `[PASS]`** on the reference fixed policy. The seeded account is live.

> **Authorization note.** Only test systems you own or have explicit written permission to test.
> Everything here runs locally against a simulated account you own.

---

## Scenario

The target account has handed you their AWS account after a near-miss: a developer laptop was lost with
an access key on it. The account grew organically — policies created on demand, roles cloned from each
other, no trust-policy review. You hold `dev-alice`'s credentials, the same shape of key Code Spaces
lost. Your deliverable is a **blast-radius finding plus the fix**: prove how far the key reaches, then
author the least-privilege policy that cuts the dangerous reach without breaking her real job, and prove
the cut holds.

Each step runs the same rhythm: **Predict** (commit before you touch anything) → **Do** (gather/prove
the evidence) → **Reveal** (check your call) → **Record** (one line in the report).

---

## Build it — read a little, do a little

### Step 1 — Map the principals, predict the reach

**Concept (30 sec):** Flight-card #1. "dev" is a name on a policy, not a boundary. The grant that matters
is `Action` × `Resource`; the moment either is `*` the label stops meaning anything.

**Predict, then do:** write your gut verdict on how far past "dev" the key reaches, then enumerate:
`aws iam list-users`, `aws iam list-roles`, and `dev-alice`'s attached policy (`DevPolicy` — get it with
`aws iam get-policy-version`, or read `data/dev-alice-policy.json`).

> **▸ On track if:** `list-users` returns **`dev-alice` and `dev-bob`**, and `DevPolicy` shows
> **`s3:*` on `*`**, `ec2:RunInstances`, and **`iam:PassRole` on `*`**. **Record:** the label said "dev";
> the grant says "account."

### Step 2 — Prove the S3 blast radius (not just her bucket)

**Concept (30 sec):** Flight-card #1/#4. `s3:*` on `*` reaches — and can **delete** — every bucket,
backups included. That reach is the Code Spaces failure in miniature.

**Do it:** create a second, unrelated bucket and reason about her reach to it (floci will *let* the
create succeed; it won't enforce a later denial, so you assert reach by policy logic):
```bash
aws s3api create-bucket --bucket payroll-prod
```

> **▸ On track if:** the bucket is created, and you can state that `DevPolicy`'s `s3:*` on `*` makes
> `dev-alice` `allowed` to read **and delete** `payroll-prod` — a bucket she has no business touching.
> (Confirm the read leg in Step 6's evaluator: the `s3:GetObject` assertion is `ALLOW` under the
> original policy.) **Record:** owner of finding = customer (the policy scope); the key can destroy data
> it has no business touching.

### Step 3 — Prove the escalation (the reach that grants more reach)

**Concept (30 sec):** Flight-card #2. `iam:PassRole` on `*` + `ec2:RunInstances` is the canonical
compose: launch an EC2 instance attached to `EC2AdminRole` (AdministratorAccess) and the key *becomes*
admin. No exploit — two legitimate grants.

**Do it:** confirm `dev-alice` can pass the admin role by running the evaluator over the original policy:
```bash
make check-escalation      # check_escalation.py over data/dev-alice-policy.json
```

> **▸ On track if:** the run prints **`[FAIL] ALLOW (want DENY )`** for *"dev-alice can PassRole the EC2
> ADMIN role"* **and** *"...PassRole *any* role"*, while the two legitimate assertions
> (`ec2:DescribeInstances`, the dev-bucket read) stay `[PASS] ALLOW`. It exits non-zero:
> `2 assertion(s) FAILED — the PassRole escalation is still open`. That `ALLOW` on the admin role **is**
> the escalation. **Record:** this is the hop that turns a lost laptop into a dead company.

### Step 4 — Check the trust walls (federation footnote)

**Concept (30 sec):** Flight-card #5. A trust policy decides *who can assume a role*. `root` and "no
`sub`" look scoped but trust **everyone in their class** — the same over-trust that, with a forged
signing key, is Golden SAML.

**Do it:** read the trust policies:
```bash
aws iam get-role --role-name AdminRole --query Role.AssumeRolePolicyDocument
aws iam get-role --role-name CICDRole  --query Role.AssumeRolePolicyDocument
```

> **▸ On track if:** `AdminRole` trusts **`arn:aws:iam::000000000001:root`** (the whole account), and
> `CICDRole`'s OIDC trust has an `aud` condition but **no `token.actions.githubusercontent.com:sub`**
> condition (every GitHub Actions workflow from the provider). **Record** one line per role: "trusts
> everyone in its class."

### Step 5 — Author the minimum cut

**Concept (30 sec):** Flight-card #3. Tracing the reach is the finding; **cutting it without breaking
`dev-alice`'s real job is the fix** — the smallest change that breaks the path.

**Do it:** edit `data/dev-alice-fixed-policy.json` (a reference solution is bundled — try it yourself
first). Apply the rulebook: scope `iam:PassRole`'s `Resource` from `*` to a single **non-admin** role
(`arn:aws:iam::000000000001:role/AppRole`) so she can no longer pass `EC2AdminRole`; scope `s3` to the
dev bucket and drop `Delete` where she doesn't need it. **Keep** her legitimate `ec2:Describe/Run` and
`iam:List*/Get*`.

> **▸ On track if:** your policy still lists `ec2:DescribeInstances` and an `s3:GetObject` on the dev
> bucket, and `iam:PassRole`'s `Resource` is a single non-admin role ARN — never `*`, never
> `EC2AdminRole`.

### Step 6 — Prove the cut holds

**Do it:**
```bash
make check-fixed           # check_escalation.py over YOUR data/dev-alice-fixed-policy.json
```

> **▸ On track if:** **all four assertions print `[PASS]`** and the run exits zero:
> `All assertions PASS — escalation closed, legitimate access intact.` The two PassRole assertions now
> read `[PASS] DENY (want DENY)` while `ec2:DescribeInstances` and the dev-bucket read stay
> `[PASS] ALLOW`. If a legitimate assertion flipped to `[FAIL] DENY`, you cut too much — that's the whole
> craft of the minimum cut. **Record:** scoping the `iam:PassRole` *resource* is the minimum cut.
> *(Optional: `make apply-fixed` pushes the policy to floci as a new default version and re-enumerates,
> so you see the change land the way it would in a real account.)*

---

## Prove the control (your finish line)

Two artifacts, and the verdict must **flip**:

1. **`blast-radius-report.md`** — per principal: the proven reach (with the evaluator verdict that
   demonstrates it), the `iam:PassRole` + `ec2:RunInstances` escalation, the two trust-policy findings,
   and the remediation. Write it like the cloud-IR/GRC artifact it is.
2. **The evaluation flips** — `make check-escalation` **fails** the original `DevPolicy` (two PassRole
   `ALLOW`s), and `make check-fixed` **passes** your scoped policy (all `DENY`/`ALLOW` as intended). If
   it doesn't flip, the fix isn't yet proven.

Score your three README "Call it" predictions against the reveals; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why is a "dev" key's blast radius almost never what the label suggests — and which permission lets it
   widen its *own* reach?
2. Name the two-permission compose that reached admin, and say why neither is a bug in IAM.
3. `make check-fixed` passes. In one sentence, what does "the reach is gone" actually mean in evaluation
   terms?

---

## Deliverables

- **`blast-radius-report.md`** — per principal: the proven reach (with the evaluator verdict), the
  escalation chain, the trust-policy finding, and the remediation. A genuine cloud-IR/GRC artifact —
  write it like one.
- **`dev-alice-fixed-policy.json`** — your least-privilege policy that makes `make check-fixed` pass.

Commit both. *Do not commit credentials, bucket contents, or any real account data.*

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your finding is "this key can pass the admin
role." Encode that verdict as a **guardrail that fails the bad state and passes the fix**: a small check
(`assert_no_escalation.py`) that, given an IAM policy, asserts the principal is **denied** `iam:PassRole`
on any admin-class role and **denied** `s3:*` / `Resource:"*"`, while still **allowed** its legitimate
actions — exit non-zero on the original `DevPolicy`, exit zero on your fix. (The bundled
`check_escalation.py` is your model; extend it, don't just copy it — add the `s3:*`-on-`*` assertion.)
Run it against both and show it flips. Have a model draft the assertions; review every line and confirm
it fails the original for the *right* reason (the PassRole reach, not an unrelated nit). This is your
verdict made un-recurrable — and the seed of the attack-path checker you'll extend in module 03.

## Definition of done (`cloud-identity-iam` ✅)

- [ ] `make check-escalation` shows `dev-alice` `[FAIL] ALLOW` on `iam:PassRole` to the admin role (and to `*`) — the escalation reproduced.
- [ ] You can state the escalation as a compose (`iam:PassRole` + `ec2:RunInstances` → admin) and name the minimum cut that breaks it.
- [ ] `data/dev-alice-fixed-policy.json` makes `make check-fixed` print **all `[PASS]`**: both escalation assertions now **deny**, both legitimate-access assertions still **allow**.
- [ ] `blast-radius-report.md` records the reach, the escalation, both trust-policy findings, and the fix.
- [ ] Your `assert_no_escalation.py` guardrail exits non-zero on `DevPolicy` and zero on your fix — and you scored your three "Call it" predictions.

## Connects forward

The principals and edges you proved here become the nodes of the privilege-escalation **graph** in module
03 (IAM Attack Paths), where pmapper/cloudfox turn this manual trace into graph search and the "minimum
cut" becomes a graph operation. The over-broad grants feed posture auditing in module 05, and the
evaluator-as-guardrail pattern returns as IaC scanning in module 06.

## Marketable proof

> "Given a leaked cloud principal, I predict and *prove* its blast radius by policy evaluation — including
> `iam:PassRole` escalation to admin — then author the minimum-cut least-privilege policy and prove by
> evaluation that the dangerous reach is denied while the principal's real job still works. I can explain
> why explicit-deny beats allow and why a `root` trust trusts the whole account."

## Stretch

- Add the `iam:CreateAccessKey`-on-another-user escalation to your enumeration and guardrail — a
  different vector from PassRole.
- Re-run the whole loop against a CloudGoat `iam_privesc_by_*` scenario in a real (free-tier) account and
  compare how `aws iam simulate-principal-policy` behaves when IAM is actually *enforced* versus floci's
  logical-only mode.
- Close the trust walls in code: rewrite `AdminRole`'s trust to a specific role/user instead of `root`,
  and add a `repo:org/name:ref` `sub` condition to the CICD OIDC trust; note why each original trusted
  "everyone in its class."
