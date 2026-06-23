# Lab 14 — Detonate the Chain: Generate the Telemetry a Defender Has to Catch

*Variant D · breach-driven, purple-team detonation. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[LocalStack](https://localstack.cloud/) to simulate AWS locally — no cloud account, no real credentials.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/14-cloud-attack-techniques
make up        # start LocalStack + the lab container (awslocal, stratus-red-team, pacu)
make demo      # detonate all three techniques and print the CloudTrail-shaped event each fires
make shell     # drop into the lab container to detonate manually
make down      # stop everything when done
```

`make demo` runs `simulate.sh`, which fires attacker-like API calls against LocalStack and prints the
CloudTrail JSON each call generates. That JSON — the **captured telemetry** — is this lab's product.

> **Authorization — read this. This is offensive tooling.** Stratus Red Team and Pacu detonate *real*
> attack techniques. Run them **only** against this LocalStack range or an AWS account you own and have
> deliberately stood up as a target — never a production account, never one you don't own, never a
> shared or employer account without explicit written permission. The blast-radius rule LastPass's
> attacker ignored is the one you enforce on yourself: dedicated test environment, no production
> resources, everything torn down after (`make down`). On any real account, treat Stratus's `--cleanup`
> as mandatory, not optional.

## Scenario
You are the **purple team**. The target account's blue team is about to build cloud detections, and they
have nothing real to test against. Your job is to *be the LastPass attacker* in a safe range: you've been
handed a leaked long-lived key (`AKIAIOSFODNN7EXAMPLE`, found in a public repo) and an enumerated session.
Walk the same three moves — valid-account role assumption → bulk data pull → exfil staging — and **capture
the telemetry each generates.** Your deliverable is the evidence package the blue team detonates their
detections against in module 15. You are not fixing anything here. You are manufacturing real signal.

Each step runs the same rhythm: **Predict** (commit to a loudness call before you fire) → **Detonate** →
**Capture** (save the events) → **Map** (ATT&CK + the distinguishing fields).

## Do

1. [ ] **Orient on the foothold.** Review `data/pacu-session.json`: which IAM identity does the leaked key
   belong to, what's its attached policy, and which finding hints at a path to a more powerful role?
   (Look for `iam:PassRole` / `sts:AssumeRole` against a broad trust policy.) This is your starting reach —
   the equivalent of the DevOps engineer's vault keys.

2. [ ] **Rank the three before you fire (the loudness call).** Without detonating yet, write your prediction:
   of T1078.004 (`AssumeRole`), T1530 (mass `GetObject`), and T1537 (`PutBucketReplication`/copy-out),
   **which leaves the loudest CloudTrail trail and which is nearly silent?** Commit to an order. You'll
   grade it in step 6.

3. [ ] **Detonate T1078.004 — Valid Cloud Accounts.** Fire the role assumption
   (`simulate.sh --technique assume-role`, or interactively `awslocal sts assume-role`). **Capture** the
   event. Which `eventName` marks the assumption? In `userIdentity`, what changes between the original
   key's calls (`type: IAMUser`) and the assumed-role calls (`type: AssumedRole`)? This is LastPass's
   entry move and it is a **management-plane** call — note that it's recorded by default.

4. [ ] **Detonate T1530 — Data from Cloud Storage.** Run the bulk download
   (`simulate.sh --technique s3-download`), which `GetObject`s across every object in the sensitive bucket.
   **Capture** the events. Now the key observation: a single `GetObject` is normal traffic — fifty in
   thirty seconds from an assumed-role identity with a `python-boto3` user-agent is not. What *combination*
   of fields (identity · rate · user-agent · object breadth) separates this from the app's normal reads?
   And critically: **is `GetObject` even in CloudTrail by default?** (It's a data-plane event — note
   whether your account would have captured it at all.)

5. [ ] **Detonate T1537 — Transfer Data to Cloud Account.** Run the exfil-staging technique
   (`simulate.sh --technique s3-exfil`), which adds a replication rule / copies objects to a second bucket
   standing in for the attacker's account. **Capture** the events. Which field exposes the **external
   destination account ID** (here `999999999999`, not the target account's)? This is the move that turned LastPass's
   read access into customer data leaving the building.

6. [ ] **Grade your loudness ranking.** Hold your step-2 prediction against the captured events. The
   default-logging reality: `AssumeRole` and `PutBucketReplication` are **management-plane — loud, recorded
   without any extra config**; the mass `GetObject` is **data-plane — silent unless S3 data events were
   turned on.** If you ranked the bulk download as "loud," you just felt the gap that let LastPass's
   exfiltration run for weeks. Note which technique the blue team most needs you to have captured, and why.

7. [ ] **Build the ATT&CK mapping.** For each of the three, write one row: technique ID, the triggering
   `eventName`(s), the *minimum* set of fields a detection rule needs to fire reliably without drowning in
   false positives, and the plane (management vs. data) so the blue team knows whether the log even exists.

## Success criteria — you're done when
- [ ] You've detonated all three techniques and **saved the captured CloudTrail JSON** for each (this is
  the artifact module 15 consumes).
- [ ] You can explain what `userIdentity.type: AssumedRole` indicates vs. `IAMUser`, and why the
  assumed-role identity is itself a signal.
- [ ] Your loudness ranking is graded against real events, and you can state in one sentence why the mass
  `GetObject` is the silent one (data-plane, off by default).
- [ ] Your `attack-mapping.md` has a row per technique with the minimum detection signature *and* the
  log-plane note.

## Deliverables
`detonation-log.md` + the captured events (`events/*.json`) + `attack-mapping.md` — the evidence package:
the ordered detonation narrative, the raw CloudTrail-shaped events each technique fired, and the
per-technique ATT&CK mapping with detection fields. Commit these alongside your detonation harness (below).
Do **not** commit credentials, real account IDs, or any data pulled from a real account — this package is
synthetic by design.

## Automate & own it
**Required — and for this module the right automation is the detonation harness itself, not a guardrail.**
This is a pure attack module: you don't fix anything, you make the attack *repeatable and safe* so the
blue team can re-run it on demand. Write a small script (`detonate.py` or extend `simulate.sh`) that:
1. detonates the three techniques **in kill-chain order** (access → collect → stage);
2. captures each technique's CloudTrail-shaped events into a single timestamp-ordered JSON array — your
   **synthetic CloudTrail log**;
3. prints a one-line summary per technique (T-ID · triggering `eventName` · `sourceIPAddress` · plane);
4. **cleans up** after itself (the `--cleanup` discipline) so the range is reusable and nothing leaks.

Have a model draft it; then verify against the *running* container that every API call actually fires and
every field your summary reads is present in the real output. A CloudTrail field the model invented but
the event doesn't contain is a hallucination — strip it, because module 15 will write a detection against
this log and a phantom field is a detection that never fires. You own every line. This synthetic log *is*
the hand-off to module 15.

## AI acceleration
Feed `data/pacu-session.json` (or your captured events) to a model: "Which ATT&CK Cloud techniques does
this expose, and what are the highest-signal API calls?" Use it as a first-pass triage — then validate
each claimed technique against its ATT&CK card's detection guidance. Models routinely confuse
`iam:ListRoles` (benign enumeration) with `sts:AssumeRole` (the actual technique), and will assert a
detection works without noticing the underlying event is data-plane and was never logged. You are the one
who knows the difference.

## Connects forward
This is the source module for Phase 3. Module 15 (Cloud Logging & Detection) takes your synthetic
CloudTrail log and writes Sigma rules against it — predicting which of your events fires and which is
invisible, then tuning out false positives. Module 16 (Cloud IR) hands you a richer corpus and asks you to
reconstruct this exact chain from the defender's side. The capstone re-litigates a full breach end to end,
and your detonation harness is the "simulate the attack" beat of it.

## Marketable proof
> "I run a purple-team detonation of the cloud kill chain — valid-account role assumption, bulk storage
> exfiltration, transfer to an external account — map each move to ATT&CK for Cloud, and capture the
> telemetry a detection engineer needs. I can say which techniques CloudTrail records by default and which
> are silent without S3 data events, and I hand the blue team a safe, repeatable harness with built-in
> cleanup."

## Stretch
- Add a fourth technique from the [Stratus AWS list](https://stratus-red-team.cloud/attack-techniques/list/)
  — e.g. exfiltrating an EBS or RDS snapshot to another account (a real LUCR-3 / data-staging move) — and
  extend the mapping.
- Run the chain through Pacu instead of `simulate.sh` to see *chained* reasoning (enumerate → assume →
  re-enumerate) versus Stratus's atomic detonation, and note how the CloudTrail trail differs.
- Hand your synthetic log straight to module 15's detection script and confirm the loud techniques fire —
  and that the silent `GetObject` doesn't, until you "enable data events."
