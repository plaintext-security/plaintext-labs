# Lab 01 — Cloud Account Enumeration & Shared Responsibility Mapping

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo.
The environment uses [LocalStack](https://localstack.cloud/) to simulate an AWS account locally — no
cloud account or real credentials required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/01-cloud-fundamentals
make up        # start LocalStack + seed the account
make demo      # run the worked enumeration walkthrough
make shell     # drop into the lab container to work
make down      # stop when done
```

The `make up` step seeds the LocalStack account with a realistic Meridian Financial IAM configuration:
one admin user, one developer user with an overly-broad policy, one EC2 instance role, and an S3 bucket.
The `awslocal` command (bundled in the container) is a drop-in replacement for `aws` that points at the
local endpoint.

> Everything runs locally against a simulated AWS environment you own. No real AWS account needed for
> this lab.

## Scenario
Meridian Financial's security team has brought you in to review the AWS account they set up for their
first cloud workload — a Python API backend on EC2 with an S3 bucket for file storage. The account
has been running for six months with minimal security review. Your job: enumerate the account, map
what Meridian owns in the shared responsibility model, and produce a responsibility matrix that the
engineering team can use to prioritise hardening.

## Do
1. [ ] **Enumerate users and policies.** Inside the container (`make shell`), list IAM users and get
   the policies attached to each one. Hint: `awslocal iam list-users` then
   `awslocal iam list-attached-user-policies --user-name <name>`. Which user has a policy that looks
   overly broad?

2. [ ] **Inspect the broad policy.** Retrieve the policy document and find the specific statement that
   grants more than it should. Hint: `awslocal iam get-policy --policy-arn <arn>` then
   `awslocal iam get-policy-version --policy-arn <arn> --version-id <vid>`. What actions does it
   allow and on what resources?

3. [ ] **Enumerate the EC2 role trust policy.** List instance profiles and retrieve the trust policy
   for the EC2 role. Hint: `awslocal iam list-instance-profiles` and
   `awslocal iam get-role --role-name <name>`. What principal is trusted — is that scope tighter
   or looser than it needs to be?

4. [ ] **Inspect the S3 bucket.** List buckets and check the bucket's ACL and public-access-block
   settings. Hint: `awslocal s3api list-buckets`, then `awslocal s3api get-bucket-acl` and
   `awslocal s3api get-public-access-block` for the bucket name you find. Is it accessible publicly?

5. [ ] **Map to the shared responsibility model.** For each finding, write down whether the
   misconfiguration lives in the *customer* layer or whether it could be argued to be a provider
   default. Use the `data/account.json` file as the written record — it's a snapshot of the
   policy document; annotate it or create a `findings.md` alongside it.

6. [ ] **Run `make demo`** (if you haven't already) and compare the worked walkthrough output to
   your manual enumeration. Did you find the same issues?

## Success criteria — you're done when
- [ ] You've identified the over-broad IAM policy and the specific `Action`/`Resource` statement that
  violates least privilege.
- [ ] You've checked the S3 public-access-block configuration and can say whether the bucket is at
  risk of public exposure.
- [ ] You've noted the EC2 instance role trust policy principal and evaluated its scope.
- [ ] You've produced a `findings.md` that maps each issue to the customer side of the shared
  responsibility model with a one-sentence rationale.

## Deliverables
`findings.md` — a short responsibility matrix: finding, the responsible party (customer vs. provider),
and one sentence on what needs to change. Commit this alongside the seed `data/account.json`. Do not
commit any real credentials or real AWS account data.

## Automate & own it
**Required.** Write a shell script (or Python) named `enumerate.sh` (or `enumerate.py`) that replays
your enumeration steps non-interactively: lists users, retrieves policy documents, and checks the
S3 public-access-block, printing a one-line finding for each. Have a model draft it from your command
history; you read every line and confirm it runs cleanly against LocalStack (`make demo` should invoke
it). This is the seed of a cloud account audit tool you'll extend in later modules.

## AI acceleration
Paste the policy JSON from step 2 into a model and ask: "What ATT&CK techniques could an attacker
exercise with these permissions?" It will give you a realistic first cut — then verify each technique
ID against the [ATT&CK for Cloud matrix](https://attack.mitre.org/matrices/enterprise/cloud/) to
confirm the mapping is accurate. Note any techniques the model missed or misidentified.

## Connects forward
The IAM configuration enumerated here becomes the attack surface for module 02 (Cloud Identity & IAM),
where `cloudfox` automates exactly what you did by hand. The S3 public-access finding reappears in
module 05 (Posture & Misconfiguration Auditing) where `prowler` would catch it in a benchmark scan.

## Marketable proof
> "I can enumerate an AWS account via CLI, map findings to the shared responsibility model, and
> articulate what the customer owns — the foundation of any cloud security engagement."

## Stretch
- Repeat the enumeration against a real AWS free-tier account (follow the `awscli` setup guide in
  the Learn section to get actual credentials). The commands are identical; the output is richer.
- Add a `get-account-password-policy` call to your script and check whether MFA is enforced — a
  common finding in first-audit engagements.
