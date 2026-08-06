# Lab 14 — Detonate the Chain: Generate the Telemetry a Defender Has to Catch

> **Hands-on lab.** Environment: `plaintext-labs/cloud/14-cloud-attack-techniques` (runs on **floci**, a
> free local AWS emulator — no cloud account). Objective: **detonate the three-move cloud kill chain
> (T1078.004 → T1530 → T1537) and capture the CloudTrail-shaped telemetry each leaves.** Target: **~90
> min**, one finish line. This telemetry is the literal input to modules 15 and 16.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **A cloud attack is a login, not an exploit.** | Every move is a signed, *authorized* API call — no malware, no zero-day. You already have the creds. |
| 2 | **Management-plane calls are in CloudTrail by default.** | `AssumeRole`, `PutBucketReplication` are recorded with no extra config — loud. |
| 3 | **Data-plane calls are silent by default.** | `GetObject` isn't logged unless S3 **data events** are on — the gap that hid LastPass's bulk pull. |
| 4 | **The kill chain is access → collect → stage.** | T1078.004 (assume role) → T1530 (mass read) → T1537 (transfer out). Three moves, one story. |
| 5 | **The signal is a *combination*, not one field.** | T1530 = assumed-role identity · high rate · `python-boto3` UA · object breadth — never "a GetObject happened." |
| 6 | **A detonation is only worth it if it yields a *detection spec*.** | "I ran some S3 commands" is useless to module 15; a T-ID + eventName + fields + plane is a rule. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [loudness question](README.md#the-loudness-question--think-before-the-lab) and the
> [attack-chain diagram](README.md#the-case).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Of the three moves — `AssumeRole`, mass `GetObject`, `PutBucketReplication` — **which one is nearly
   silent in a default account, and why?**
2. What turns a raw detonation log into a **"detection spec"** module 15 can actually build a rule on?

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[floci](https://github.com/floci-io/floci), a free MIT-licensed local AWS emulator, to run the attacker's
API calls for real — no cloud account, no real credentials.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/14-cloud-attack-techniques
make up      # start floci + the lab container (aws, stratus-red-team, pacu)
make demo    # detonate all three techniques; print the CloudTrail-shaped event each fires
make shell   # drop into the lab container to detonate manually (./simulate.sh --technique …)
make down    # stop everything when done
```

`make demo` runs `simulate.sh`, which seeds a breach-shaped account (a `DataPipelineRole` with
`AmazonS3FullAccess`, a sensitive `financial-reports-prod` bucket, and an `attacker-staging-bucket`), fires
attacker-like API calls against floci, and prints the CloudTrail JSON each call generates. **That JSON —
the captured telemetry — is this lab's product.**

> **▸ On track if:** `make demo` prints three banners (`T1078.004`, `T1530`, `T1537`), and under each a
> CloudTrail JSON block plus a `KEY FIELDS TO DETECT` list. If you see all three, the range is live.

!!! warning "Where the emulator stops — read before you trust a field"
    floci runs the attacker's *API calls* for real, but **no emulator delivers real CloudTrail or
    GuardDuty.** The events here are faithfully *shaped* by `simulate.sh` (synthetic by design), not
    emitted by a real trail — and nothing in this lab actually *fires an alert*. To see genuine
    CloudTrail/GuardDuty telemetry and a live GuardDuty detection, run the identical techniques against an
    **AWS account you own** (the real-AWS fidelity route). The captured JSON is field-accurate to a real
    trail, which is what lets module 15 write rules against it.

!!! danger "Authorization — this is offensive tooling. Read it."
    Stratus Red Team and Pacu detonate **real** attack techniques. Run them **only** against:

    - **this local floci range** (the default — nothing leaves your machine), or
    - an **AWS account you personally own** and have deliberately stood up as a disposable target, or
    - an **intentionally vulnerable environment** built for this (e.g. CloudGoat in your own account).

    **Never** a production account, never one you don't own, never a shared or employer account without
    explicit written permission. The blast-radius discipline LastPass's attacker ignored is the one you
    enforce on *yourself*: dedicated test environment, no production resources, everything torn down after
    (`make down`). On any real account, treat Stratus's `--cleanup` as **mandatory**, not optional.

---

## Scenario

You are the **purple team**. The target account's blue team is about to build cloud detections, and they
have nothing real to test against. Your job is to *be the LastPass attacker* in a safe range: you've been
handed a leaked long-lived key (`AKIAIOSFODNN7EXAMPLE`, found in a public repo) belonging to a `ci-deploy`
user, plus an enumerated session (`data/pacu-session.json`). Walk the same three moves — valid-account role
assumption → bulk data pull → exfil staging — and **capture the telemetry each generates.** Your deliverable
is the evidence package the blue team detonates their detections against in module 15. You are not fixing
anything here. You are manufacturing real signal.

Each step runs the same rhythm: **Predict** (commit to a loudness call before you fire) → **Detonate** →
**Capture** (save the events) → **Map** (ATT&CK + the distinguishing fields).

---

## Build it — read a little, do a little

### Step 1 — Orient on the foothold

**Concept (30 sec):** Flight-card #1. You start with valid credentials, not an exploit — the whole edge
is knowing what reach they buy.

**Do it:** review `data/pacu-session.json`: which IAM identity does the leaked key belong to, what's its
attached policy, and which finding hints at a path to a more powerful role? (Look for `iam:PassRole` /
`sts:AssumeRole` against a broad trust policy.) This is your starting reach — the equivalent of the DevOps
engineer's vault keys.

> **▸ On track if:** you can name the foothold identity and point to the finding that says it can reach
> `DataPipelineRole`. **Record:** starting principal + the role it can assume.

### Step 2 — Rank the three before you fire (the loudness call)

**Concept (30 sec):** Flight-card #2 & #3. Management plane logged by default; data plane silent by default.

**Do it:** *without detonating yet*, write your prediction — of T1078.004 (`AssumeRole`), T1530 (mass
`GetObject`), and T1537 (`PutBucketReplication`/copy-out), **which leaves the loudest CloudTrail trail and
which is nearly silent?** Commit to an order. You'll grade it in Step 6.

> **▸ On track if:** you have a written 1-2-3 ranking with a one-line reason each. Being wrong here is the
> point — the reveal only sticks if you committed first.

### Step 3 — Detonate T1078.004: Valid Cloud Accounts

**Concept (30 sec):** Flight-card #4. This is LastPass's entry move and a **management-plane** call —
recorded by default.

**Do it:** `make shell`, then `./simulate.sh --technique assume-role` (or interactively `aws sts
assume-role`). **Capture** the emitted event.

> **▸ On track if:** the CloudTrail block shows `"eventName": "AssumeRole"`, `eventSource:
> sts.amazonaws.com`, and `userIdentity.type: "IAMUser"` — an *IAM user* (not a service) assuming a role
> from `sourceIPAddress 203.0.113.42`. That user-assuming-a-role-from-an-odd-IP shape **is** the tell.
> **Record:** owner move = access; plane = management (loud, recorded without extra config).

### Step 4 — Detonate T1530: Data from Cloud Storage (the silent one)

**Concept (30 sec):** Flight-card #3 & #5. A single `GetObject` is normal; fifty in thirty seconds from an
assumed-role identity is not — and the log may not even exist.

**Do it:** `./simulate.sh --technique s3-download` — it `GetObject`s across every object in
`financial-reports-prod`. **Capture** the events. Then answer: what *combination* of fields (identity ·
rate · user-agent · object breadth) separates this from the app's normal reads? And critically: **is
`GetObject` even in CloudTrail by default?**

> **▸ On track if:** the blocks show `"eventName": "GetObject"` with `userIdentity.type: "AssumedRole"`
> (arn `assumed-role/DataPipelineRole/attacker-session`) and `userAgent: python-boto3…`. You can state that
> **this is a data-plane event — silent unless S3 data events were turned on.** **Record:** move = collect;
> plane = **data (off by default)**; signature = the field *combination*, not any one field.

!!! note "Sample-vs-real caveat"
    On floci the `GetObject` calls run and the shaped event is printed — but in a *real* default account
    this event would **not** appear in CloudTrail at all. That absence is the lesson: "I didn't see it in
    CloudTrail" almost always means "the log was never collected," not "it didn't happen." Detonate it
    anyway, so the blue team discovers the blind spot before an attacker does.

### Step 5 — Detonate T1537: Transfer Data to Cloud Account

**Concept (30 sec):** Flight-card #4. The move that turned read access into customer data *leaving the
building* — and a **management-plane** call that names the destination.

**Do it:** `./simulate.sh --technique s3-exfil` — it adds a replication rule / copies objects to
`attacker-staging-bucket`, standing in for the attacker's account. **Capture** the events.

> **▸ On track if:** you see `"eventName": "PutBucketReplication"` whose
> `requestParameters.Destination.Account` is **`999999999999`** — *not* the target account
> (`123456789012`) — plus a `PutObject` into the exfil bucket. That foreign account ID is the exfil tell.
> **Record:** move = stage-out; plane = management (loud); tell = destination account ID.

### Step 6 — Grade your loudness ranking

**Do it:** hold your Step-2 prediction against the captured events. The default-logging reality:
`AssumeRole` and `PutBucketReplication` are **management-plane — loud, recorded without any extra config**;
the mass `GetObject` is **data-plane — silent unless S3 data events were turned on.**

> **▸ On track if:** you can name which prediction you missed (most people rank the bulk download "loud")
> and state, in one sentence, why the mass `GetObject` is the silent one. **Note which technique the blue
> team most needs you to have captured, and why** — it's the silent one.

---

## Prove the control (your finish line)

**One detonated technique, proven detectable.** Because detection itself lives in module 15 — and floci
has no GuardDuty — your finish line here is to prove the telemetry can *drive* a detection: take the
loud **T1078.004** event you captured and show its distinguishing fields are all present, so a rule would
fire. A one-line assertion is enough:

```bash
# the AssumeRole event carries every field a detection needs → it WOULD fire
jq -e 'select(.eventName=="AssumeRole" and .userIdentity.type=="IAMUser" and .sourceIPAddress=="203.0.113.42")' events/assume-role.json
```

You're done when:

1. The assertion **exits 0** on the `AssumeRole` event (the loud technique is detectable), **and**
2. You can show the **T1530** `GetObject` event and state that on a *real* default account the same
   assertion would have **nothing to run against** — the log was never collected. Proving the loud one
   fires *and* the silent one is a blind spot is the whole point of the detonation.

!!! tip "Real-AWS fidelity route (optional)"
    To watch this actually get *detected*, replay the three techniques against an AWS account you own with a
    trail (and S3 data events) enabled; GuardDuty flags the anomalous role use — exactly how LastPass's
    activity was eventually caught. floci proves the *signal shape*; a real account proves the *alert*.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why is a cloud attack described as "a login, not an exploit" — what was *not* present in any step?
2. Of the three techniques, which is nearly silent in a default account, and why (name the plane)?
3. What fields turn a raw `GetObject` log into a T1530 detection spec that won't drown in false positives?

---

## Deliverables

`detonation-log.md` + the captured events (`events/*.json`) + `attack-mapping.md` — the evidence package:
the ordered detonation narrative, the raw CloudTrail-shaped events each technique fired, and a per-technique
ATT&CK mapping (technique ID · triggering `eventName`(s) · the *minimum* fields a detection needs · the
plane, so the blue team knows whether the log even exists). Commit these alongside your detonation harness
(below). **Do not commit** credentials, real account IDs, or any data pulled from a real account — this
package is synthetic by design.

## Automate & own it

**Required — and for this module the right automation is the detonation harness itself, not a guardrail.**
This is a pure attack module: you don't fix anything, you make the attack *repeatable and safe* so the blue
team can re-run it on demand. Write a small script (`detonate.py`, or extend `simulate.sh`) that:

1. detonates the three techniques **in kill-chain order** (access → collect → stage);
2. captures each technique's CloudTrail-shaped events into a single timestamp-ordered JSON array — your
   **synthetic CloudTrail log**;
3. prints a one-line summary per technique (T-ID · triggering `eventName` · `sourceIPAddress` · plane);
4. **cleans up** after itself (the `--cleanup` discipline) so the range is reusable and nothing leaks.

Have a model draft it; then verify against the *running* container that every API call actually fires and
every field your summary reads is present in the real output. A CloudTrail field the model invented but the
event doesn't contain is a hallucination — strip it, because module 15 writes a detection against this log
and a phantom field is a detection that never fires. You own every line. This synthetic log *is* the
hand-off to module 15.

## Definition of done (`cloud-attack-techniques` ✅)

- [ ] You've detonated all three techniques and **saved the captured CloudTrail JSON** for each (the
  artifact module 15 consumes).
- [ ] You can explain what `userIdentity.type: AssumedRole` indicates vs. `IAMUser`, and why the
  assumed-role identity is itself a signal.
- [ ] Your loudness ranking is graded against real events, and you can state in one sentence why the mass
  `GetObject` is the silent one (data-plane, off by default).
- [ ] The finish-line assertion **fires** on the `AssumeRole` event, and you can show the `GetObject` blind
  spot alongside it.
- [ ] `attack-mapping.md` has a row per technique with the minimum detection signature *and* the log-plane note.
- [ ] You can explain all six flight-card facts cold.

## AI acceleration

Feed `data/pacu-session.json` (or your captured events) to a model: "Which ATT&CK Cloud techniques does this
expose, and what are the highest-signal API calls?" Use it as first-pass triage — then validate each claimed
technique against its ATT&CK card's detection guidance. Models routinely confuse `iam:ListRoles` (benign
enumeration) with `sts:AssumeRole` (the actual technique), and will assert a detection works without noticing
the underlying event is data-plane and was never logged. You are the one who knows the difference.

## Connects forward

This is the source module for Phase 3. Module 15 (Cloud Logging & Detection) takes your synthetic CloudTrail
log and writes Sigma rules against it — predicting which of your events fires and which is invisible, then
tuning out false positives. Module 16 (Cloud IR) hands you a richer corpus and asks you to reconstruct this
exact chain from the defender's side. The capstone re-litigates a full breach end to end, and your detonation
harness is the "simulate the attack" beat of it.

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
