# Lab 15 — Predict What Fires: Detecting the Module-14 Detonation

*Variant D · breach-driven, predict-what-fires. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/15-cloud-logging-detection
make up         # build the Python 3.12 detection container
make demo       # run the bundled detector over the seed CloudTrail events
make shell      # drop into the container to work
make down       # stop when done
```

The environment carries the detection script (`detect.py`), `sigma-cli`, and all seed data — including a
CloudTrail export shaped like the **module-14 detonation** (an `AssumeRole`, a `CreateUser` →
`AttachUserPolicy` admin escalation, a burst of `GetObject` reads, a no-MFA `ConsoleLogin`) plus a normal
workday of benign traffic, and a sample GuardDuty finding. No AWS account needed.

> Only test systems you own or have explicit written permission to test. This lab uses bundled synthetic
> data shaped like real CloudTrail; no live account or credentials are involved.

## Scenario
You are the target account's detection engineer. The team detonated the attack chain from module 14 in a
lab account and forwarded the CloudTrail export. The CISO's question is the one Capital One and LastPass
both failed: *the log existed — would anything have fired?* Your deliverable is a **tuned Sigma rule with
an explicit false-positive analysis** — detection-as-code that catches the attack and stays quiet on the
99.99% that's benign.

Each step runs the same rhythm: **Predict** (commit before you look) → **Do** (gather evidence) →
**Reveal** (check your call) → **Record** (one line toward the deliverable).

## Do

### Part 1 — Predict the gap, then prove it

1. [ ] **Predict what the default log captured.** From module 14 you detonated three things: an
   `AssumeRole` (T1078.004), a `CreateUser`+`AttachUserPolicy` escalation (T1098), and a bulk `GetObject`
   exfil (T1530). **Predict** which of the three is *not* in a default CloudTrail at all. Write it down.

2. [ ] **Map the events.** Open `data/cloudtrail/events.json` and classify every record as **management**
   or **data** plane (hint: `eventSource` + the `eventName` — config-changing/reading calls vs. object
   reads/writes). **Reveal:** the `GetObject` records are *data events* — present here only because the
   export had them on; in a **default** account they wouldn't exist. **Record:** T1530, the LastPass exfil
   move, is invisible by default — note "were S3 data events enabled?" as your first IR question.

3. [ ] **Find the loud one worth detecting.** Among the *management* events, locate the `CreateUser`
   immediately followed by `AttachUserPolicy` attaching `AdministratorAccess`. This is the T1098
   escalation — loud, control-plane, logged for free. **Record:** this is the sequence you'll write a rule for.

### Part 2 — Write the detection, then tune it

4. [ ] **Run the bundled detector.** `make demo` runs `detect.py` over the seed events. Note each finding:
   rule, severity, technique, triggering event. Read the bundled `data/sigma_rule.yml`
   (`CreateUser`→`AttachUserPolicy`) and confirm how it references the *nested* fields
   (`requestParameters.policyArn`, `userIdentity`) and its temporal `condition`.

5. [ ] **Write your Sigma rule — and make it too broad on purpose first.** Author
   `my_escalation_rule.yml` for the escalation sequence, but start with the naive version: fire on **any**
   `CreateUser`. **Predict:** how many seed events does that match? **Do:** convert/run it and count.
   **Reveal:** it fires on legitimate user-creation in the benign traffic too — the week-two failure mode
   from the README. **Record:** raw recall is not detection.

6. [ ] **Tune against benign activity (the actual craft).** Add the qualifying context that makes it
   precise: require the *sequence* (`CreateUser` **followed by** `AttachUserPolicy` with an admin-class
   `policyArn`) **within a short window**, and exclude your known-CI `sourceIPAddress`/automation
   principal. Re-run. **Success is binary:** it fires on the attacker's escalation and on **zero** benign
   events. If a benign event still trips it, tighten — that loop *is* the job.

7. [ ] **Write the FP analysis.** In `detection-analysis.md`, state explicitly **what benign activity this
   rule must NOT fire on** and why your conditions exclude each (e.g. CI provisioning users, IaC pipelines
   attaching scoped policies, an admin onboarding a teammate). This is the judgment the rule encodes.

8. [ ] **Reproduce in a native detector, and rule on coverage.** Open `data/guardduty-finding.json`: which
   seed event does it correspond to, and what enrichment (geo/ASN/threat-intel) does it add that raw
   CloudTrail lacks? Then, for each technique in Part 1, decide: would GuardDuty/Defender/SCC catch it
   natively, or is Sigma filling a gap? **Record** one line each — including that the T1530 data-plane
   exfil is a gap *for both* if data events were off.

## Success criteria — you're done when
- [ ] You correctly predicted (and proved by classifying events) that the **T1530 bulk download is
  invisible in a default CloudTrail** — data events, off by default.
- [ ] Your `my_escalation_rule.yml` is valid Sigma and **fires on the attacker's escalation sequence and on
  zero benign events** in the seed data.
- [ ] `detection-analysis.md` contains the explicit FP analysis (what it must NOT fire on, and why) and the
  native-vs-open coverage call per technique.
- [ ] You scored your Part-1 prediction and can state in one sentence why "alert on any `CreateUser`" is a
  bad detection.

## Deliverables
- `my_escalation_rule.yml` — your tuned Sigma rule for the T1098 escalation sequence.
- `detection-analysis.md` — the false-positive analysis (the benign activity it must not fire on) + the
  per-technique native-vs-open coverage table.

Commit both alongside the seed data. Do not commit raw exported logs, credentials, or real account data.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your detection is a *judgment* about attacker
behaviour; ship it as a **tuned rule that fires on the bad state and stays silent on benign traffic**, and
make that property *testable*. Add your rule to `detect.py` (or wire `sigma-cli` to evaluate it) and write
a tiny harness that runs it against **two** fixtures: the attack export (must fire ≥1) and a benign-only
export (must fire **0**) — exit non-zero if either fails. That FP gate is the deliverable: it encodes "this
detection earned its place by being precise, not just by catching the attack." Have a model draft the
Sigma and the harness; review every line, run it, and confirm the benign fixture stays at zero for the
*right* reason (your qualifying conditions, not a lucky field absence). A rule without an FP gate is a
week-two mute waiting to happen.

## AI acceleration
Describe the detection in plain English ("escalation: a user is created then granted admin within five
minutes, not from our CI IP") and have a model draft the Sigma rule and the Python matcher. It will get the
syntax and common field names right — and it will write a generic, too-broad rule, because it doesn't know
your baseline. Run its draft against the benign fixture: watch it false-fire, then tighten it yourself and
rewrite its `falsepositives` block from what you actually observed. The model can author; only you can tune
against *your* noise. Then ask it to craft a benign event that sneaks past your rule — if it can, your FP
analysis is incomplete.

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
- Use `sigma-cli` to compile your rule to a backend (`sigma convert -t splunk ...`) and note what a proper
  CloudTrail pipeline must remap (nested `requestParameters` fields) versus the default mapping.
- Write a *second* rule for the data-plane gap: detect bulk `GetObject` (T1530) — then state honestly the
  precondition that makes it useless in most real accounts (S3 data events were never enabled).
