# Lab 05 — Posture & Misconfiguration Auditing

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/05-posture-auditing
make up
make demo
make shell
make down
```

The environment spins up a **LocalStack** container (a local AWS API emulator) and a **lab**
container with `prowler` 4.x pinned. `make up` builds both, then runs `data/setup.sh` via
`awslocal` to create a deliberately misconfigured account: a public S3 bucket, an overly-permissive
security group, a CloudTrail trail that is disabled, and a fake IAM access key that has never been
rotated. No real AWS credentials are needed — LocalStack handles the fake API surface.

> This lab uses LocalStack, not a real AWS account. Never run posture tools against accounts or
> tenants you do not own or have explicit written permission to audit.

## Scenario

Meridian Financial has just acquired a startup and inherited its AWS account. The security team
has been asked to produce a first-pass posture report before the account is connected to the
corporate network. You are running the initial audit. The account has never been formally reviewed.
Your deliverable: a triage-ready finding list, mapped to CIS controls, with a remediation plan for
the top five issues.

## Do

1. [ ] **Enumerate the environment first.**
   Before scanning, inventory what's actually in the account with the AWS CLI. List all S3 buckets,
   running EC2 instances, IAM users, and security groups using `awslocal` from the lab shell.
   *Hint:* `awslocal s3 ls`, `awslocal ec2 describe-security-groups`, `awslocal iam list-users`.
   Note anything that looks unusual — public ACLs, wide-open ingress rules.

2. [ ] **Run a prowler scan.**
   From the lab shell, run prowler against the LocalStack endpoint, scoping to checks with MEDIUM
   severity or above. Output findings in JSON to `/tmp/findings.json`.
   *Hint:* `prowler aws --endpoint-url http://localstack:4566 -S -o /tmp/findings.json`.
   Count how many findings you have. How many are HIGH or CRITICAL?

3. [ ] **Identify the top five findings.**
   Open the JSON output and extract the five highest-severity findings. For each one, record:
   the check ID, the affected resource ARN, the severity, and the CIS benchmark control it maps to.
   *Hint:* `jq '[.[] | select(.status=="FAIL")] | sort_by(.severity) | reverse | .[0:5]' /tmp/findings.json`

4. [ ] **Cross-reference findings against MITRE ATT&CK for Cloud.**
   Look up which ATT&CK techniques are enabled by the top findings. A public S3 bucket enables
   T1530 (Data from Cloud Storage); a missing MFA on a privileged account enables T1078 (Valid
   Accounts). Annotate your top-five list with technique IDs.

5. [ ] **Reproduce a finding manually.**
   Pick the public S3 bucket finding. Verify it manually: check the bucket's ACL and block-public-
   access settings using `awslocal s3api get-bucket-acl` and `get-public-access-block`. Confirm the
   bucket is readable without credentials. Understand *why* prowler flagged it, not just that it did.

6. [ ] **Draft a remediation.**
   For your top five findings, write a short remediation note for each: what the fix is, which team
   owns it (IAM = security team, S3 ACL = application team), and whether it can be scripted.
   At least two of the five should have a one-line `awslocal` remediation command you can actually run.

7. [ ] **Verify a remediation.**
   Apply one of your `awslocal` remediations (e.g., block public access on the S3 bucket), then
   re-run the relevant prowler check and confirm the finding no longer appears.
   *Hint:* `prowler aws --checks s3_bucket_public_access --endpoint-url http://localstack:4566`

## Success criteria — you're done when

- [ ] prowler scan completes and outputs at least five FAIL findings against the LocalStack environment
- [ ] Top-five finding list is documented with check ID, ARN, severity, CIS control, and ATT&CK technique ID
- [ ] At least one finding has been manually verified (not just taken from prowler output)
- [ ] At least one remediation has been applied and the scan re-run confirms the finding is resolved
- [ ] Remediation plan covers all five findings with owner and approach

## Deliverables

Commit to your portfolio repo (not to `plaintext-labs`):
- `findings-summary.md` — top-five finding table: check ID, resource, severity, CIS control, ATT&CK technique, remediation note, owner
- `remediation-notes.md` — prose remediation plan with priorities and rationale
- `audit.sh` — the automation script from **Automate & own it** below

Do **not** commit: full prowler JSON output (too large), any LocalStack state, or any file ending in
`.key`, `.pem`, or containing strings matching real AWS key patterns.

## Automate & own it

**Required.** Write `audit.sh` — a script that:
1. Runs prowler against a target endpoint (accept `--endpoint-url` as an argument, defaulting to LocalStack)
2. Filters findings to FAIL + severity HIGH or CRITICAL
3. Outputs a Markdown table: check ID | resource | severity | CIS control

AI drafts the `jq` pipeline and the argument parsing; you validate that the jq filter produces the
right rows, that the severity filter handles all variants in the schema, and that the script exits
non-zero if any CRITICAL finding is found (so it can gate a CI pipeline).

```bash
# Starter scaffold — AI fills in the jq and logic
#!/usr/bin/env bash
ENDPOINT="${ENDPOINT_URL:-http://localhost:4566}"
OUTPUT=$(mktemp /tmp/prowler-XXXXXX.json)
prowler aws --endpoint-url "$ENDPOINT" -S -o "$OUTPUT"
# YOU: jq filter → Markdown table
# YOU: exit 1 if any .severity == "critical"
```

## AI acceleration

Prowler outputs hundreds of findings in a real account. Paste the JSON array into a model with the
prompt: "Group these findings by affected service, then within each group rank by blast-radius
severity. For each group, draft a one-paragraph remediation note in plain language." The model is
good at this synthesis. Your review must check: (1) that the blast-radius ranking matches your
knowledge of which resources hold sensitive data, and (2) that no finding is quietly re-labelled
"informational" without a documented rationale.

## Connects forward

The misconfigurations you found here are the same ones you'll gate in CI in Module 06 (IaC
Security) — you will write Terraform that would have prevented each of these from deploying. In
Module 15 (Cloud Logging & Detection) you will write detections for when an attacker *exploits* a
misconfiguration like the ones you just catalogued.

## Marketable proof

> "I ran an automated CIS benchmark audit against an AWS environment, triaged findings by blast
> radius, and produced a prioritised remediation plan mapping each gap to MITRE ATT&CK for Cloud."

## Stretch

- Run ScoutSuite against the same LocalStack environment and compare its findings against prowler's.
  Where do they overlap? What does each tool surface that the other misses?
- Add a `--baseline` flag to `audit.sh` that loads a previous scan's output and only reports *new*
  findings — the delta scan pattern used in continuous posture monitoring.
