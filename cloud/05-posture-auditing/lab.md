# Lab 05 — Audit, Triage, Remediate, Verify: Find the 2017 Bucket Before a Researcher Does

*Variant D · breach-driven, audit → remediate → verify. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs
[LocalStack](https://localstack.cloud/) (a local AWS API emulator) and a lab container with `prowler`
pinned — no cloud account or real credentials required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/05-posture-auditing
make up         # start LocalStack + seed a deliberately misconfigured account
make demo       # run prowler and show the HIGH/CRITICAL findings
make shell      # drop into the lab container (prowler + awslocal + jq)
make down       # stop when done
```

`make up` seeds the inherited "" account with the exact shapes from the case: a **public S3
bucket with a file in it** (the 2017 wave), a security group open to `0.0.0.0/0` on 22/3389, an IAM
access key that was never rotated, and a CloudTrail trail that exists but isn't logging.

**What this lab is — and isn't (read this).** LocalStack emulates the AWS *API surface* prowler reads,
so the findings are real findings against real config. It does **not** reproduce the 2017 exfiltration
(there's no public internet pointing at the bucket) — you're not stealing data, you're doing the audit
that would have caught it. Where a check depends on AWS state LocalStack doesn't model (e.g. root-MFA),
treat it as *assessed from config*, not exploited.

> Only audit accounts you own or have explicit written permission to test. Posture tools touch every
> resource; never point them at a tenant that isn't yours. Everything here is a local account you own.

## Scenario
Your org just acquired a startup and inherited its AWS account — never formally reviewed. You
must produce a first-pass posture report **before it's connected to the corporate network.** The
account is shaped like 2017: a public bucket sits in it right now. Your deliverable is a triaged
finding list mapped to CIS, a remediation that you **apply and verify**, and a guardrail that keeps the
worst finding from ever passing review again.

## Do

### Part 1 — Audit and triage (signal vs. noise)

1. [ ] **Inventory before you scan.** From the lab shell, list what's actually in the account —
   buckets, security groups, IAM users, trails — with `awslocal` (`awslocal s3 ls`,
   `awslocal ec2 describe-security-groups`, `awslocal iam list-users`). Note anything that looks wrong
   *by eye* (a public ACL, `0.0.0.0/0` ingress). You're building the asset context the scanner won't have.

2. [ ] **Run the linter.** Run `prowler aws --endpoint-url http://localstack:4566` and write JSON to
   `/tmp/findings.json`. **Predict first, then count:** how many FAIL findings do you expect, and which
   *one* is the 2017 bucket? Now count (`jq '[.[]|select(.status=="FAIL")]|length'`) and see how the raw
   number compares to "the one that matters." This gap — many findings, one verdict — *is* the module.

3. [ ] **Triage to the top five.** Don't read 400 lines; rank them. For each of your top five, record the
   check ID, the resource ARN, the prowler severity, and the **CIS control** it maps to. Then override the
   tool's order with *your* judgment: re-rank by **severity × exploitability × blast radius** using your
   step-1 context (the public bucket has a file with PII in it → top, regardless of the tool's label).
   *Hint:* `jq '[.[]|select(.status=="FAIL")]|sort_by(.severity)|reverse|.[0:5]' /tmp/findings.json`.

4. [ ] **Map blast radius to ATT&CK.** Annotate the top findings with the technique each *enables*, not
   just its severity: public bucket → **T1530** (Data from Cloud Storage); stale/over-privileged key →
   **T1078** (Valid Accounts). This is the column that turns "MEDIUM" into "this is the 2017 leak."

5. [ ] **Confirm the headline finding by hand.** Pick the public bucket. Verify prowler wasn't lying:
   `awslocal s3api get-bucket-acl` and `get-public-access-block`, and confirm an object reads without
   credentials. Understand *why* it's flagged — this is the literal Accenture/Verizon/INSCOM condition.

### Part 2 — Remediate and verify (the half a checkbox skips)

6. [ ] **Draft the remediation.** For each top-five finding write a one-line note: the fix, the owning
   team (S3 ACL → app team; IAM → security), and whether it's scriptable. At least two must have a real
   `awslocal` remediation you can run (block public access on the bucket; revoke the `0.0.0.0/0` ingress).

7. [ ] **Apply and re-scan — prove FAIL→PASS.** Remediate the public bucket (re-enable block-public-access
   and drop the public ACL), then **re-run that one check** and confirm the finding is gone.
   *Hint:* `prowler aws --check s3_bucket_public_access --endpoint-url http://localstack:4566`. A
   remediation you didn't re-scan is a wish, not a fix — this flip is the deliverable.

8. [ ] **(Stretch) Second opinion.** Run ScoutSuite against the same account and diff its findings against
   prowler's — where they agree, and what each catches that the other misses.

## Success criteria — you're done when
- [ ] prowler completes and returns at least five FAIL findings against the seeded account.
- [ ] Your top-five list is triaged — check ID, ARN, severity, CIS control, ATT&CK technique — and
  **re-ordered by your own blast-radius judgment** with a one-line rationale per finding (you can say why
  the public bucket outranks the stale key regardless of the tool's severity).
- [ ] You verified the public-bucket finding **by hand** (read an object with no credential), not just from prowler's output.
- [ ] You **applied one remediation and re-scanned**, showing that check flip FAIL→PASS.
- [ ] Your guardrail (below) **fails** the broken account and **passes** the fixed one, mapped to its CIS control.

## Deliverables
Commit to your **portfolio** repo (not `plaintext-labs`):
- `findings-summary.md` — the triaged top-five table (check ID · resource · severity · CIS control · ATT&CK · your re-ranked priority + rationale · owner).
- `remediation-notes.md` — the plan, plus the before/after evidence of the one finding you flipped FAIL→PASS.
- `check_public_bucket.py` (or `.sh`) — the guardrail from **Automate & own it**.

Do **not** commit: the full prowler JSON (too large), any LocalStack state, `/tmp/legacy-key.json`, or
any `*.key`/`*.pem`/real-key-pattern file.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your verdict is "no bucket in this account may
be publicly readable" — the exact control whose absence *was* the 2017 wave. Encode it as a **benchmark
check that fails the bad state and passes the fix**, mapped to its CIS control. Write `check_public_bucket.py`
(or a small shell check) that, given the account, **fails (exit non-zero)** if any bucket has public
ACLs or block-public-access disabled — printing the bucket and the control it violates, e.g.
**CIS AWS 2.1.x — "Ensure S3 buckets are not publicly accessible"** <!-- VALIDATE exact CIS control number against the current AWS Foundations Benchmark --> — and **passes (exit zero)** once you've remediated. Run it against the seeded account (red), apply your fix, and run it again (green). Have a model draft the
boto3/`awslocal` calls and the assertion; review every line and confirm it fails for the *right* reason
(the public ACL, not an unrelated bucket). This is your triage verdict made un-recurrable — and in
module 06 you'll lift this exact check into a CI gate that blocks the merge before the bucket ever ships.

## AI acceleration
Paste the prowler JSON array into a model: *"Group these findings by affected service, then within each
group rank by blast-radius severity, and draft a one-paragraph remediation per group."* It's genuinely
good at that synthesis. Your review owns the two things it can't: (1) the **priority order** against your
real asset criticality — does its ranking know the public bucket holds PII and the "stale key" is on a
dead user? — and (2) that **no finding gets quietly re-labelled "informational"** without a written
rationale. Then paste your guardrail and ask it to craft a bucket config that sneaks past — if it can,
your check is too narrow.

## Connects forward
Every finding here is a later module. The over-broad grants tie back to **02 (IAM)** and the
public-bucket verdict is the same one you rendered in **01**. The guardrail you wrote is lifted, almost
verbatim, into the CI gate of **06 (IaC Security)** — where it blocks the misconfiguration *before*
deploy, not after. And when an attacker actually exploits a posture gap like this, **15 (Logging &
Detection)** is where you write the detection for it.

## Marketable proof
> "I ran an automated CIS-benchmark audit against a cloud account, triaged a noisy finding set down to
> the few that mattered by blast radius (not raw count), remediated the worst and **re-scanned to prove
> the fix held**, and encoded that verdict as a benchmark guardrail — mapped to its CIS control — that
> fails the misconfiguration and passes the fix. I can explain why the 2017 S3 wave was one ACL at scale."

## Stretch
- Add a `--baseline` mode to your guardrail that loads a prior scan and reports only **new** findings —
  the delta-scan pattern of continuous posture monitoring.
- Extend the guardrail to a second 2017-class control (e.g. no `0.0.0.0/0` on sensitive ports), so it
  covers the security-group finding too — a direct preview of module 04's network guardrail.
