# Lab 16 — Reconstruct the Incident: Build the Timeline, Scope the Blast, Automate the Triage

*Variant D · breach-driven, predict-what-fires / reconstruct. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — the environment ships one-command in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/16-cloud-incident-response
make up         # build the Python 3.12 triage container
make demo       # run triage.py — prints the reconstructed timeline, IOCs, containment checklist
make shell      # drop into the container for interactive analysis
make down       # stop when done
```

No AWS account needed. `data/cloudtrail/incident.json` holds 17 CloudTrail events spanning the full attack
chain; `data/vpc/flowlogs.csv` holds VPC flow logs including a large outbound transfer to an external IP.
`triage.py` is the reconstruction tool you'll read, run, and **extend**.

> Only test systems you own or have explicit written permission to test. This lab uses bundled synthetic
> data modelled on real cloud-IR cases; no real account or credentials are involved.

## Scenario
It is 08:45 UTC on 2024-11-14. The target account's SOC got a GuardDuty alert at 08:40 —
**six hours after the fact** — for `UnauthorizedAccess:IAMUser/TorIPCaller`. You're handed a raw CloudTrail
export and the flow logs and told: reconstruct the incident, determine what was exfiltrated, find any
persistence the attacker left, and have a timeline + IOC set ready for the executive briefing in 90
minutes. **The LastPass parallel is your watch-out:** the obvious containment (kill the known key) is the
one that left a door open last time. Scope past it.

The trail was **stopped at 02:18 UTC and re-enabled at 08:35 UTC** by the SOC. You have complete logs for
02:14–02:18 (the attack window) and from 08:30 onward (remediation). The hours between are the gap.

Each step runs the same rhythm: **Predict** (commit before you look) → **Do** (reconstruct the evidence) →
**Reveal** (check your call) → **Record** (one line in the timeline/report).

## Do

### Part 1 — Reconstruct the timeline (the super-timeline move)

1. [ ] **Ask the first question before you read an event.** Open `data/cloudtrail/incident.json`.
   **Predict:** is the trail intact? Find the event that answers it, the timestamp it fires, and where the
   gap begins and ends. **Reveal:** `StopLogging` at 02:18; `StartLogging` at 08:35. **Record:** the gap
   bounds and duration — the gap is evidence, not absence of it.

2. [ ] **Triage by hand, then check the tool.** Working the raw JSON, establish the attacker's source IP,
   the initially-compromised principal, and the *order* of events. Then run `make demo` and read
   `triage.py`'s sorted timeline as a **check on your reconstruction** — what did you miss, and what did the
   tool miss? Note both; the tool is a junior analyst, not the verdict.

3. [ ] **Reconstruct the attack chain, phase by phase.** This is the super-timeline: every event already
   carries its timestamp — your job is to sort by it and **tag each with its kill-chain phase** (Initial
   Access → Enumeration → Privilege Escalation → Collection → Exfiltration → Defense Evasion → Persistence
   → Remediation), then confirm each tag against its **ATT&CK-for-Cloud technique ID**. **Predict** the
   escalation hop before you find it: how does a *dev* key reach the financial-reports bucket?
   **Reveal:** the `IAMUser` dev-alice → `AssumeRole DataPipelineRole` → `AssumedRole` transition —
   the `userIdentity` type change *is* the privilege escalation. **Record** the table row for each event.

### Part 2 — Corroborate, scope, and contain

4. [ ] **Corroborate exfil across both planes.** In the flow-log output from `make demo`, find the outbound
   flow(s) to the attacker IP `203.0.113.42`: total bytes out, and the CloudTrail event(s) they line up
   with in time. **Record** the verdict: control-plane `GetObject`s + data-plane large outbound to an
   external IP = a defensible exfiltration finding, not a guess. Note what the flow log adds that CloudTrail
   alone can't (volume, direction).

5. [ ] **Find the persistence — scope past the obvious key (the LastPass lesson).** **Predict:** if the SOC
   disables only the original key `AKIAIOSFODNN7EXAMPLE`, is the attacker out? **Reveal:** a second key
   (`CreateAccessKey` on dev-alice → `AKIAI7SFODNN7EXAMPLE`) and an `S3 PutBucketReplication` to external
   account `999999999999` were planted *before* the trail stopped. Eviction of the known key is *not*
   eradication. **Record** both persistence mechanisms and confirm the containment checklist addresses each.

6. [ ] **Write the impact assessment.** Four objects were read from `financial-reports-prod` (three
   quarterly earnings PDFs + a compensation spreadsheet) and a replication rule was added. In one paragraph:
   what is **confirmed exfiltrated** (in CloudTrail), what **may have** gone via the replication rule before
   it was removed, and the **regulatory notification** implication (financial + compensation data → state
   privacy law / GDPR). State containment in order: revoke creds → close exfil channel → restore logging →
   scope impact.

### Part 3 — Automate the reconstruction

7. [ ] **Extend `triage.py` to surface the gap automatically.** Add `print_gap_analysis()` that detects a
   `StopLogging` event, computes the duration to the matching `StartLogging`, and prints a warning with the
   gap bounds and length. Run `make demo` and confirm the gap (~6h 17m) appears. This turns "is the trail
   intact?" from a manual check into a check the tool always makes.

## Success criteria — you're done when
- [ ] You have a complete attack-chain table (phase, eventName, timestamp, ATT&CK technique ID, what it
  means) covering every attacker event — sorted on time, the join key.
- [ ] You can name **both** keys the attacker used or created **and** the replication rule, and confirm the
  containment checklist addresses all three — i.e. you scoped past the obvious key.
- [ ] Your exfil finding cites *both* planes (CloudTrail `GetObject`s + the flow-log outbound volume).
- [ ] `print_gap_analysis()` fires and prints the correct gap duration.
- [ ] You scored your three "Call it" predictions from the README against the reveals — especially Q1
  (what survives an eviction).

## Deliverables
- `timeline.md` — the attack-chain table (phase, eventName, timestamp, technique ID, meaning), with the
  `StopLogging` gap called out.
- `impact.md` — the impact assessment from step 6 (confirmed vs. potential exfil, regulatory implication,
  containment order).
- `triage.py` — updated with `print_gap_analysis()` and the JSON output below.
- Do **not** commit credentials, bucket contents, or any real account data.

## Automate & own it
**Required — judgment-as-code, the reconstruction made repeatable.** Extend `triage.py` with a `--json`
flag that emits the whole reconstruction as one structured JSON object: keys `timeline` (the ordered event
list), `iocs` (IPs, access keys, principals, buckets, external accounts), and `containment_checklist` (the
ordered action strings). This is the super-timeline move encoded — heterogeneous events merged and sorted on
time, then serialized so the next responder (or a SOAR runbook) consumes it without re-deriving it. Have a
model draft the `--json` flag and the serialization; **review every line.** Before committing: run it, pipe
through `python -c "import json,sys; json.load(sys.stdin)"` to prove valid JSON, and verify the `iocs`
section contains **all** attacker-associated keys and IPs *and* the external replication account — the
persistence the obvious triage misses. You own the logic and the verdict it encodes.

## AI acceleration
Paste the `make demo` timeline into a model: "Map each event to ATT&CK-for-Cloud, flag anything out of
expected order, and list the persistence mechanisms and any missing containment steps." Use it as a
second opinion against your Part 1–2 analysis. It will reliably tag the common techniques — and reliably
stumble on temporal reasoning: watch for it treating the persistence key's later use as the same session,
or missing that the replication rule is a *second* exfil channel. Note every discrepancy and explain why
your reconstruction is right. That review discipline is what keeps AI-assisted IR from declaring "contained"
the way the first LastPass response did.

## Connects forward
This is the **respond** half the capstone integrates. Module 14 gave you the attacker's TTPs and the
telemetry they generate; Module 15 gave you the detection that should have fired at 02:14 instead of an
alert at 08:40; this module gives you the reconstruction that turns raw logs into a defensible timeline,
IOC set, and containment plan. The cloud capstone runs all three end to end: reproduce the chain, render
the verdict memo, close every hop as code, detect it, and **write the IR timeline** — this lab's output is
that timeline.

## Marketable proof
> "I reconstruct cloud incidents from raw CloudTrail and VPC flow logs — a super-timeline sorted on the one
> shared key, time — into a defensible narrative: per-phase chain with ATT&CK IDs, two-plane exfil
> corroboration, full IOC set, and an ordered containment plan that scopes *past* the obvious compromised
> key to the persistence the attacker planted. I automated the whole reconstruction into a triage tool that
> emits structured JSON, and I can explain exactly where the detection gap was."

## Stretch
- Feed `data/cloudtrail/incident.json` to a real `hayabusa json-timeline` invocation (if installed) and
  diff its output against `triage.py` — what does each surface that the other misses?
- Re-implement the reconstruction as Athena-style SQL using Python's in-memory `sqlite3`: load the records
  into a table and run `SELECT eventTime, eventName, sourceIPAddress FROM events WHERE sourceIPAddress =
  '203.0.113.42' ORDER BY eventTime`. This mirrors the production CloudTrail → S3 → Athena IR pattern.
- Map the lab back to the anchor: write the one-paragraph parallel between the target account's persistence keys and
  LastPass's incident-1-data-as-incident-2-recon. Where is the "containment ≠ eradication" gap in each?
