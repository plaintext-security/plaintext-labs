# Lab 15 — Predict What Fires: Detecting the Module-14 Detonation

> **Hands-on lab** (Variant D · breach-driven, predict-what-fires).
> [← Back to the module concept](README.md). Environment:
> `plaintext-labs/cloud/15-cloud-logging-detection` — a Python 3.12 detection container with
> `sigma-cli`, a `detect.py` matcher, a shipped Sigma rule, an eval gate, and a bundled CloudTrail
> export shaped like the module-14 detonation (no AWS account, fully offline). Objective: **write a
> Sigma rule that fires on the seeded escalation and stays silent on benign traffic, and prove it with
> the eval gate.** Target: **~90 min**, one finish line.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **CloudTrail splits into two planes: management (free, default) vs. data (off by default).** | `s3:GetObject` bulk exfil (**T1530**) leaves *no record* in a default account — the loudest attacker move is invisible. |
| 2 | **Precision, not recall, is the product.** | A detection is a hypothesis scored on a **99.99%-benign** stream; catching the attack is the easy 5%. |
| 3 | **A rule muted by week two is no coverage at all.** | "Alert on any `CreateUser`" fires on the attack *and* on every legitimate provisioning — so it gets muted. |
| 4 | **Sequence + qualifying context turns benign atoms into a signal.** | `CreateUser` **followed by** `AttachUserPolicy(admin)` **within 5 min** from a non-CI IP is almost never legitimate. |
| 5 | **Native detector = baseline; Sigma = the gap; both tuned before trust.** | GuardDuty is one-click and enriched; Sigma is readable, fresh, and yours — neither is trusted until tuned on *your* noise. |
| 6 | **A detection earns its place by being *testable*.** | The FP gate: fire on every held-out attack (recall floor `1.0`) and on **zero** benign near-miss (fp ceiling `0.0`). |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [what fires, revealed](README.md#what-fires-revealed).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Module 14 detonated three things: an `AssumeRole`, a `CreateUser`+`AttachUserPolicy` escalation, and a
   bulk `GetObject` exfil. **Which one is *not* in a default CloudTrail at all — and what setting would
   have captured it?**
2. You write a rule: *alert on any `CreateUser`.* It fires perfectly on the attack. **What happens to it
   by week two, and why?**

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/15-cloud-logging-detection
make up                    # build the Python 3.12 detection container
make demo                  # detector + eval gate: GREEN on the good rule, RED on both regressions
make shell                 # drop into the container to author your rule
make eval                  # score the shipped Sigma rule against the held-out corpus (exit 0 = pass)
make eval-bad              # watch the gate go RED on the over-broad and too-narrow regressions
make detect FILE=data/cloudtrail/events.json   # run the detector over any events file
make down                  # stop when done
```

The container carries `detect.py` (a hard-coded matcher), `data/sigma_rule.yml` (the shipped rule),
`data/cloudtrail/events.json` (the 19-event demo export), `data/guardduty-finding.json` (a native
detector sample), and `eval_corpus/` (a held-out labelled corpus `heldout.json` plus two *regressed*
rules the eval gate is designed to fail). Everything runs offline; there is no grade target — Plaintext
is an honor system.

> **▸ On track if:** `make demo` ends with `=== Verdict ===` and
> `PASS: gate is GREEN on the good rule and RED on both regressions — the gate works.` The env is live.

> **Authorization note.** Only test systems you own or have explicit written permission to test. This lab
> uses bundled synthetic data shaped like real CloudTrail; no live account or credentials are involved.

---

## Scenario

You are the target account's detection engineer. The team detonated the module-14 attack chain in a lab
account and forwarded the CloudTrail export. The CISO's question is the one Capital One and LastPass both
failed: *the log existed — would anything have fired?* Your deliverable is a **tuned Sigma rule with an
explicit false-positive analysis** — detection-as-code that catches the attack and stays quiet on the
99.99% that's benign. Each step runs the same rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Step 1 — Predict the gap, then prove it (management vs. data plane)

**Concept (30 sec):** Flight-card #1. Management events are logged for free; data events are off by
default. That split decides what a detector can *ever* see.

**Predict, then do:** commit which of the three module-14 moves is invisible by default. Then open
`data/cloudtrail/events.json` and classify each of the 19 records as **management** or **data** plane
(hint: `eventSource` + `eventName` — config calls vs. object reads/writes).

> **▸ On track if:** the `s3:GetObject` records — the burst at `09:21:03/07/11` from `203.0.113.42`
> right after the `AssumeRole`, and the `14:11:08` read from `185.220.101.55` — are the **data events**,
> present here only because this export had them on. In a **default** account they wouldn't exist.
> **Record:** T1530 (the LastPass exfil move) is invisible by default — your first IR question is
> *"were S3 data events enabled for this bucket?"*

### Step 2 — Find the loud one worth detecting (the escalation)

**Concept (30 sec):** Flight-card #4. The escalation is *management* plane — logged for free — and its
signal is the **sequence**, not either event alone.

**Do it:** among the management events, find the `CreateUser` immediately followed by `AttachUserPolicy`
granting an admin policy.

> **▸ On track if:** you find `CreateUser` at `10:05:22Z` and `AttachUserPolicy` at `10:05:31Z` — **9
> seconds apart**, same user, granting `AdministratorAccess`, both from `203.0.113.42`. **Record:** this
> T1098 sequence is the rule you'll write.

### Step 3 — Run the bundled detector and read the shipped Sigma rule

**Do it:** `make demo` (part A) runs `detect.py` over the seed export; then read `data/sigma_rule.yml`.

> **▸ On track if:** the detector prints `--- 5 finding(s) total ---`, the first being
> `[CRITICAL] IAM_PRIVESC_CREATEUSER_ATTACHPOLICY` →
> *"New IAM user 'backup-svc-restore' created and granted 'AdministratorAccess' within 9s from IP
> 203.0.113.42"* (plus the AssumeRole-from-`eu-west-2`, the Tor-node `GetObject`, the root no-MFA login,
> and the `0.0.0.0/0` security-group open). And in `data/sigma_rule.yml` you can point to the two nested
> selections (`create_user`, `attach_policy` with `requestParameters.policyArn|contains:
> [AdministratorAccess, PowerUserAccess, IAMFullAccess]`), the `timeframe: 5m`, and
> `condition: create_user followed by attach_policy`. **Record:** the admin-policy filter is what keeps
> this precise.

### Step 4 — Watch the gate: too-broad and too-narrow both go RED

**Concept (30 sec):** Flight-card #2 and #6. Recall is cheap; the gate makes both failure modes
mechanical — over-broad costs precision, over-narrow costs recall.

**Do it:** `make eval` (the good rule), then `make eval-bad` (the two regressions).

> **▸ On track if:** `make eval` prints `Recall … 100.0%` and `FP-rate … 0.0%`, both
> `REGRESSION GATE [PASS]`, and **exits 0**. `make eval-bad` shows the **over-broad** rule (admin-policy
> filter dropped) false-firing on `BEN-01, BEN-06` → `FP-rate 33.3%`, `GATE [FAIL]: fp_rate`; and the
> **too-narrow** rule (`AdministratorAccess` only) missing `ATK-02, ATK-03` → `Recall 50.0%`,
> `GATE [FAIL]: recall`. **Record:** this is the false-positive/false-negative economics as code.

### Step 5 — Author your rule, and make it too broad on purpose first

**Do it:** in `make shell`, write `my_escalation_rule.yml`. Start naive — fire on **any** `CreateUser` —
then grade it against the held-out corpus:
`python3 eval_corpus/eval.py --rule my_escalation_rule.yml --gate recall=1.0 --gate fp_rate=0.0`.

> **▸ On track if (naive):** the scorecard shows `FP-rate` **above 0.0%** (it fires on benign
> user-creation) and the gate **FAILs on fp_rate** — the week-two mute, reproduced. Now add the
> qualifying context: the *sequence* (`CreateUser` **followed by** `AttachUserPolicy` with an admin-class
> `policyArn`) within a short `timeframe`, and exclude your known-CI `sourceIPAddress`. Re-grade.
> **▸ On track if (tuned):** `Recall 100.0%` **and** `FP-rate 0.0%` — fires on all **4** held-out attacks,
> silent on all **6** benign — both gates PASS, exit 0. If a benign case still trips it, tighten; that
> loop *is* the job. **Record:** raw recall is not detection — precision is.

### Step 6 — Reproduce in a native detector, and rule on coverage

**Do it:** open `data/guardduty-finding.json`; map it to a seed event; then decide, per technique, whether
native coverage catches it or Sigma is filling a gap.

> **▸ On track if:** the finding is `UnauthorizedAccess:IAMUser/TorIPCaller`, `Severity 8.0`, on a
> `GetObject` from `185.220.101.55` (ASN `F3 Netze` — a Tor exit node) — it corresponds to the
> **14:11:08 sensitive-bucket read** and adds geo/ASN/Tor enrichment raw CloudTrail lacks. **Record:**
> per technique, native-vs-Sigma-gap — and note the T1530 data-plane exfil is a gap **for both** if S3
> data events were off.

---

## Prove the control (your finish line)

One binary gate, two artifacts:

1. **The rule fires on known-bad, stays quiet on known-good.**
   `python3 eval_corpus/eval.py --rule my_escalation_rule.yml --gate recall=1.0 --gate fp_rate=0.0`
   exits **0** — `Recall 100.0%` (all 4 held-out attacks) **and** `FP-rate 0.0%` (zero of 6 benign). If it
   doesn't hit both, it isn't tuned yet.
2. **The gate flips.** Break your rule the way the regressions do (drop the admin-policy filter) and watch
   it go RED on `fp_rate` — the same behaviour `make eval-bad` demonstrates. A gate that can't fail can't
   protect you.

Score your three README "Call it" predictions against the reveals; note which you missed.

---

## Recall check — close the doc, answer from memory (3 min)

1. Which module-14 technique is *not* in a default CloudTrail, and what setting would have captured it?
2. A rule that alerts on every `CreateUser` fires perfectly on the attack — why is it a bad detection by
   week two, and what qualifying context fixes it?
3. Native detector vs. Sigma-over-CloudTrail: name one thing each does better — and the one blind spot
   they *share*.

---

## Deliverables

- **`my_escalation_rule.yml`** — your tuned Sigma rule for the T1098 escalation sequence.
- **`detection-analysis.md`** — the false-positive analysis (the benign activity it must *not* fire on and
  why each condition excludes it) + the per-technique native-vs-open coverage call.

Commit both alongside the seed data. *Do not commit raw exported logs, credentials, or real account data.*

## Automate & own it

**Required — judgment-as-code, not keystroke scripting.** Your detection is a *judgment* about attacker
behaviour; ship it as a rule whose "fires on bad, silent on benign" property is **testable and gated**.
The env already ships the harness (`eval_corpus/eval.py`, invoked by `make eval`): wire *your*
`my_escalation_rule.yml` into it and prove it passes `--gate recall=1.0 --gate fp_rate=0.0` for the
**right** reason (your qualifying conditions, not a lucky field absence). Then add one *new* benign
near-miss to the corpus that a naive rule would trip on, and confirm your tuned rule stays at zero. Have a
model draft the Sigma and any glue; review every line, run it, and confirm the benign cases stay silent. A
rule without an FP gate is a week-two mute waiting to happen — the gate is the deliverable.

## Definition of done (`cloud-logging-detection` ✅)

- [ ] You correctly predicted (and proved by classifying events) that the **T1530 bulk download is
  invisible in a default CloudTrail** — data events, off by default.
- [ ] `make demo` ends `PASS: gate is GREEN on the good rule and RED on both regressions`, and you can
  explain *why* the over-broad rule fails on `fp_rate` and the narrow one on `recall`.
- [ ] `my_escalation_rule.yml` scores `recall=1.0` **and** `fp_rate=0.0` on the held-out corpus (4 attacks
  caught, 0 of 6 benign fired) and the gate exits 0.
- [ ] `detection-analysis.md` states the explicit FP analysis and the per-technique native-vs-open call.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

Module 16 (Cloud Incident Response) hands you the full incident corpus — initial access to exfiltration —
and asks you to reconstruct the timeline; the rules you tuned here define what *should* have fired during
it, and the data-plane blind spot you found is exactly why the LastPass second-incident exfil was so hard
to scope. The capstone's detection half is this rule plus a native detector, proven to fire on the
simulation and stay silent on benign traffic.

## Marketable proof

> "Given cloud attack telemetry, I predict which actions the default log even captured (the S3 data-plane
> blind spot included), write a Sigma detection for the technique worth catching, and **tune it against
> benign activity** — shipping detection-as-code with an explicit false-positive analysis and an FP gate
> that proves it fires on the attack and not on the noise."

## Stretch

- Use `sigma-cli` to compile your rule to a backend (`sigma convert -t splunk …`) and note what a proper
  CloudTrail pipeline must remap (nested `requestParameters` fields) versus the default mapping.
- Write a *second* rule for the data-plane gap: detect bulk `GetObject` (T1530) — then state honestly the
  precondition that makes it useless in most real accounts (S3 data events were never enabled).
- Add the new benign near-miss from *Automate & own it* to `eval_corpus/heldout.json` and confirm the gate
  still passes — extending the corpus is how a real detection team hardens a rule against regressions.
