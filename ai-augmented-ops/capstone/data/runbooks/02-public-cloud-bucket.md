# Runbook — Public cloud object-storage exposure

**Class:** Data from Cloud Storage (MITRE ATT&CK T1530). **Severity:** High → Critical if the
bucket holds PII/regulated data.

## Recognising it
- A posture scanner (prowler, ScoutSuite) flags an S3 bucket with a public ACL or with
  block-public-access disabled, and an object reads with **no credential**.
- This is the 2017 leak class: through 2017 a wave of public-bucket misconfigurations exposed data
  at Accenture, Verizon, the US Army INSCOM, and others — in each case "one ACL at scale," not a
  novel exploit.

## Immediate actions
1. **Confirm exposure by hand** — fetch an object anonymously to prove the finding is real, not a
   scanner false positive.
2. **Re-enable block-public-access** and remove the public ACL/policy on the bucket.
3. **Re-scan that one control** to prove the finding flips FAIL → PASS (a remediation you didn't
   re-scan is a wish, not a fix).
4. **Assess blast radius**: what was in the bucket, was it accessed (CloudTrail / access logs),
   and is disclosure notification triggered.

## Guardrail
Encode the verdict as a benchmark check that **fails** the public state and **passes** the fix,
mapped to its CIS control (AWS Foundations: "Ensure S3 buckets are not publicly accessible"), and
run it in CI so the misconfiguration is blocked *before* deploy, not after.
