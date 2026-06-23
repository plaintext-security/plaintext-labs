# Lab 15 — Cloud Logging & Detection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — the environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/15-cloud-logging-detection
make up       # build the lab container
make demo     # run the detector, then prove the eval gate is GREEN on the good rule, RED on regressions
make eval     # score the Sigma rule against the HELD-OUT corpus and run the regression gate
make eval-bad # watch the gate go RED on the over-broad and too-narrow regressed rules
make shell    # drop into the container for interactive work
make down     # stop when done
```

The environment is a Python 3.12 container with the detection script (`detect.py`) and all seed
data pre-loaded. No AWS account needed.

## Scenario
Meridian Financial's CloudTrail has been forwarded to your analysis workstation as a JSON export.
The CISO wants to know: what did the attacker do, how would GuardDuty have detected it, and where
would GuardDuty have been silent? Your job is to build detections for the gaps.

The seed data in `data/cloudtrail/events.json` contains 19 events spanning a normal workday plus
several attacker actions — including an unusual `AssumeRole`, a mass S3 download, a suspicious
user-agent on a sensitive bucket, a root login without MFA, and a `CreateUser` + `AttachUserPolicy`
admin escalation sequence. A sample GuardDuty finding JSON is in `data/guardduty-finding.json`.

> Only test systems you own or have explicit written permission to test. This lab uses
> bundled synthetic data; no real AWS account or credentials are involved.

> **Honest gotcha — the mass S3 download in this seed data wouldn't normally be there.** S3
> object-level (data-plane) reads like `GetObject` are **not logged by CloudTrail by default**;
> you only see them if data events were explicitly enabled for that bucket, which costs money and
> most teams enable only for sensitive buckets. The held-out corpus reflects this honestly: it
> contains only **management-plane** events (IAM/STS/EC2 control-plane), because that is what a
> default trail actually captures. Where data-plane access matters, you detect it by its
> management-plane footprint, not by assuming the `GetObject` itself was logged.

## Do
1. [ ] **Map the events manually.** Open `data/cloudtrail/events.json` and skim all 19 records.
   Identify the events you consider suspicious. For each, note: the `eventName`, the
   `userIdentity.arn` or type, the `sourceIPAddress`, and why it looks anomalous. (Hint: look for
   API calls from unexpected IP ranges, unexpected regions, and unexpected user-agents.)

2. [ ] **Run the bundled detector.** `make demo` runs `detect.py` against the seed events. Note
   every finding it prints: rule name, severity, technique ID, and the triggering event details.
   Are there events you flagged in step 1 that the detector missed? Are there detector findings
   you didn't flag?

3. [ ] **Read the GuardDuty finding.** Open `data/guardduty-finding.json`. Which event from the
   CloudTrail seed data does this correspond to? What additional context does GuardDuty provide
   that isn't in the raw CloudTrail event (geolocation, ASN, threat intelligence enrichment)?
   What did GuardDuty *not* detect that the Python detector caught?

4. [ ] **Write your own Sigma rule.** Open `data/sigma_rule.yml` and read the bundled
   `CreateUser + AttachUserPolicy` rule. Now write a *new* Sigma rule for the suspicious
   `AssumeRole` from an unexpected region (the event at 09:20:15 from `eu-west-2`). Your rule
   should fire on `AssumeRole` where `awsRegion` is not in the expected set. Save it as
   `my_assumedrole_rule.yml` in the lab directory. (Hint: Sigma supports the `not` keyword and
   value lists in the detection condition.)

5. [ ] **Add your rule to `detect.py`.** Implement `rule_assumedrole_my_rule()` in `detect.py`
   (alongside the existing rules) and confirm it fires against the seed events with `make demo`.
   The existing `rule_assumedrole_unexpected_region()` function is the reference implementation —
   compare your Sigma logic to the Python logic and explain any differences.

6. [ ] **Compare detection approaches.** For each of the five rules in `detect.py`, write one
   sentence on whether GuardDuty would catch the same thing natively, and if not, why not. (Use
   the GuardDuty finding types list from the Learn path.)

7. [ ] **Score the rule against a held-out corpus.** "It fired in the demo" is not proof — the demo
   events are the ones the rule was written against. Run `make eval`: it interprets the actual
   `data/sigma_rule.yml` (selections, `followed by`, `timeframe`) over `eval_corpus/heldout.json` —
   a labelled set the rule was *never tuned on* — and prints a scorecard: precision, recall, and
   false-positive rate. The corpus is built around **near-misses** that separate a precise rule from
   a sloppy one: legitimate provisioning that attaches a *scoped* (non-admin) policy, an admin grant
   47 minutes later (outside the window) and to a different user, a `CreateUser` with no attach, an
   `IAMFullAccess`/`PowerUserAccess` escalation a too-narrow rule misses. Read the confusion matrix:
   recall is the floor (a miss is an undetected breach), the FP-rate is the economics (every benign
   alert costs an analyst minutes — push it down without dropping recall).

8. [ ] **Watch the gate go red, then green.** Run `make eval-bad` to score the two regressed
   fixtures in `eval_corpus/`: the **over-broad** rule (admin-policy filter dropped) keeps recall
   high but its FP-rate explodes on the benign provisioning near-misses; the **too-narrow** rule
   (`AdministratorAccess` only) looks precise but goes silent on `IAMFullAccess`/`PowerUserAccess` —
   recall collapses. The gate (`recall>=1.0`, `fp_rate<=0.0`) fails the build on either. `make demo`
   runs the contrast end to end: PASS on the good rule, FAIL on both regressions. A gate you have
   only ever watched pass is not a gate — the proof it works is seeing it go red.

## Success criteria — you're done when
- [ ] You can identify all five suspicious event categories in the seed data by hand.
- [ ] `make demo` fires findings for all five rules against the bundled events.
- [ ] You have written a Sigma rule (`my_assumedrole_rule.yml`) that is syntactically valid and
  correctly describes the detection logic.
- [ ] You can explain one case where GuardDuty provides coverage the Python detector doesn't, and
  one case where the open tool is needed.
- [ ] `make eval` scores the Sigma rule against the held-out corpus and the gate is GREEN (recall
  100%, FP-rate 0%); you can read the scorecard and say what each number means.
- [ ] You have *seen the gate go RED* — via `make eval-bad` or `make demo` — on the over-broad and
  too-narrow regressions, and can explain which metric each one breaks and why. A gate you've only
  watched pass isn't a gate.

## Deliverables
- `my_assumedrole_rule.yml` — your Sigma rule for the unexpected-region AssumeRole.
- `detection-analysis.md` — the comparison table from step 6: rule, GuardDuty coverage (Y/N),
  why the open tool adds/doesn't add value.
- The **held-out scorecard** (`make eval` output) and a one-line note on which regression breaks
  recall and which breaks the FP-rate — the proof the rule is measured, not vibes.

## Automate & own it
**Required — build the regression gate for *your* rule.** The lab ships a held-out corpus
(`eval_corpus/heldout.json`), a scorer (`eval_corpus/eval.py`), and a gate wired into `make eval` for
the bundled `CreateUser → AttachUserPolicy` rule. Your job is to extend that machinery to a detection
you write — so it can never silently regress. Pick a new technique (e.g. `DeleteTrail`/`StopLogging`,
T1562.008 — Impair Defenses; `CreateAccessKey` on a user you didn't create; an admin grant to an
*existing* user). Then: (a) add a small Sigma rule for it; (b) add held-out cases to the corpus —
**attack cases it must catch and benign near-misses it must NOT fire on** (the near-misses are the
point); (c) score it with `eval.py` and wire it into a gate. Have a model draft the rule and the
near-miss events — but *you* label every case (a model labelling its own test set is exactly the
contamination the held-out wall exists to prevent), and you confirm the gate goes GREEN on the good
rule and RED when you deliberately break it. You own the labels, the metric, and the threshold.

## AI acceleration
Describe your intended detection in plain English to a model: "I want to detect when someone calls
CreateAccessKey on a user other than themselves, from an external IP." Ask it to draft the Python
function body and the corresponding Sigma rule. Your job is to check: are the field names correct
against the actual CloudTrail JSON structure? Does the logic handle missing fields without
crashing? Does the false-positive section reflect your environment? Then *measure it* — don't trust
the draft on the demo. A model will cheerfully widen a rule "to catch more" and flood the queue, or
tighten it "to be precise" and go silent on a variant; the held-out scorecard (`make eval`) is what
surfaces both. Run it; read the numbers; fix it; own it.

## Connects forward
Module 16 (Cloud Incident Response) gives you a richer CloudTrail corpus — a full incident from
initial access to exfiltration — and asks you to build a timeline. The detection rules you wrote
here define what should have fired during the incident; the IR module asks you to explain why they
did or didn't.

## Marketable proof
> "I read raw CloudTrail JSON, write Sigma rules for sequence-based cloud attack techniques, score
> them against a held-out corpus (precision/recall/FP-rate), gate them in CI so they can't silently
> regress, and can articulate exactly where GuardDuty provides coverage and where open tooling fills
> the gap."

## Stretch
- Use the `sigma-cli` tool (installed in the container) to compile `data/sigma_rule.yml` to
  Splunk SPL: `sigma convert -t splunk -p sysmon data/sigma_rule.yml`. The output won't be
  perfectly valid for CloudTrail (Sysmon pipeline mismatch), but observe the structure and note
  what a proper CloudTrail Sigma pipeline would need to change.
- Extend `detect.py` to output its findings as structured JSON (one object per finding) rather
  than human-readable text. This makes it easy to feed findings into a downstream SIEM or alert
  management system.
