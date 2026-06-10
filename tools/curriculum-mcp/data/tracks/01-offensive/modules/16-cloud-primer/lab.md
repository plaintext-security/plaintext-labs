# Lab 16 — Cloud Attack Primer

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/16-cloud-primer
python3 check.py        # verify connectivity + print the walkthrough guide
```

No Docker required. You need Python 3.8+, the AWS CLI, and a free-tier AWS account
for CloudGoat scenarios (Part B). Part A (flaws.cloud) requires no account.

## Scenario

Meridian Financial has migrated part of their infrastructure to AWS.  
You have been authorised to practice against two targets:

1. **flaws.cloud** — a public, intentionally vulnerable S3 bucket challenge (levels 1–6).
2. **CloudGoat** — a Terraform-provisioned deliberately-vulnerable AWS environment you deploy into your own account.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

### Part A — flaws.cloud (no account needed)

1. [ ] Run `python3 check.py` and read the printed level walkthrough summary.

2. [ ] Work through flaws.cloud **levels 1–3**:
   - Level 1: Use `nslookup` or `dig` to resolve the domain; what service does it point to?
   - Level 2: Enumerate the public bucket contents. What AWS CLI command lists them?
   - Level 3: Find the exposed credential in the bucket; what AWS service does it belong to?

3. [ ] Levels 4–6 require AWS credentials. If you have an account:
   - Configure `aws configure` with a dedicated IAM user (no production credentials).
   - Use `aws s3 ls` and `aws sts get-caller-identity` as directed per level.

### Part B — CloudGoat scenario (your AWS account)

4. [ ] Install CloudGoat and run a scenario:
   ```bash
   pip install cloudgoat
   cloudgoat config profile   # point to your non-production profile
   cloudgoat create iam_privesc_by_rollback
   ```

5. [ ] Run the scenario. Your goal:
   - Enumerate what IAM permissions you start with.
   - Find the privilege-escalation path.
   - Document the specific API calls you used.

6. [ ] Tear down when done to avoid charges:
   ```bash
   cloudgoat destroy iam_privesc_by_rollback
   ```

### Part C — Map the attack chain

7. [ ] Match each technique to the flaws.cloud or CloudGoat step that demonstrated it:
   - IAM credential exposure via S3
   - Bucket enumeration via anonymous access
   - Privilege escalation via IAM policy version rollback
   - Credential exfiltration from instance metadata service (IMDS)

8. [ ] Tie it back: explain how a web SSRF (module 08) reaching `169.254.169.254` would
   yield the same IAM credentials you found in levels 3–4.

## Success criteria — you're done when

- [ ] You completed flaws.cloud levels 1–3 and can explain the misconfiguration at each.
- [ ] `python3 check.py` ran without errors.
- [ ] You documented the API calls and findings from the CloudGoat scenario (or levels 4–6).
- [ ] You can connect SSRF → metadata endpoint → IAM credentials in your own words.

## Deliverables

`cloud-notes.md`: for each level or scenario step — the finding, the AWS API call used,
the misconfiguration root cause, and the 1-line remediation. This is also the capstone
artifact reference for the cloud sections of the offensive track.

## Automate & own it

**Required.** Write `enumerate_account.sh` that, given an AWS profile name:
- Runs `aws sts get-caller-identity`
- Runs `aws s3 ls` to list accessible buckets
- Runs `aws iam list-attached-user-policies` for the current user
- Outputs a short triage summary (who am I, what buckets, what policies?)

AI drafts it; you audit the IAM calls and verify the output matches manual checks.
Commit `enumerate_account.sh` and `cloud-notes.md`.

## AI acceleration

Paste the IAM policy JSON from a scenario step to a model and ask it to enumerate
every privilege-escalation path that policy enables. Compare its output to the
CloudGoat walkthrough — where was it right? Where did it miss a path?

## Connects forward

Cloud misconfigurations (SSRF hitting IMDS, exposed S3, IAM overpermission) are the
real-world equivalents of modules 07–08. Track 05 (Cloud & Container Security) does
posture, IaC scanning, and Kubernetes in depth — this is the on-ramp.

## Marketable proof

> "I've exploited intentionally-vulnerable AWS environments: enumerated open buckets,
> retrieved IAM credentials, and escalated to admin via policy version rollback. I can
> document findings and tear down the environment to avoid charges."

## Stretch

- Complete flaws.cloud levels 4–6. Level 6 involves IMDS — compare the manual
  `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/` to your
  SSRF exploit from module 08.
- Run `pacu` against your CloudGoat environment: `run iam__enum_permissions`.
  Compare Pacu's automatic enumeration to your manual steps.
