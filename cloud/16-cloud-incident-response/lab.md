# Lab 16 — Reconstruct the Incident: build the timeline, scope the blast, automate the triage

> **Hands-on lab.** Environment: `plaintext-labs/cloud/16-cloud-incident-response` (a Python 3.12 triage
> container over bundled CloudTrail + VPC flow logs — no AWS account). Objective: **reconstruct a
> defensible incident timeline from an immutable API log, scope the blast radius past the obvious key, and
> encode the reconstruction so the next responder doesn't re-derive it.** Target: **~90 min**, one finish line.

*Variant D · breach-driven, predict-what-fires / reconstruct. [← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The log is the crime scene.** | No disk, no memory — CloudTrail is ground truth. First question is always *"is the trail intact?"* |
| 2 | **Merge on time — the super-timeline move.** | CloudTrail + flow logs share exactly one field, *time*. Sort on it, tag by phase, and the raw log becomes a narrative. |
| 3 | **The `userIdentity` type change *is* the escalation.** | `IAMUser dev-alice` → `AssumedRole DataPipelineRole` is the privilege hop, visible in one field. |
| 4 | **Two planes corroborate.** | Control-plane `GetObject`s + a data-plane large outbound to an external IP = a *defensible* exfil finding, not a guess. |
| 5 | **The `StopLogging` gap is evidence.** | 02:18 → 08:35 (~6h 17m) of blindness — its start, end, and duration are data, not absence of it. |
| 6 | **Containment ≠ eradication — scope past the obvious key.** | The naive revoke leaves the planted second key and the replication rule live. This is the LastPass gap. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [reconstruction, revealed](README.md#the-reconstruction-revealed) and the
> [containment order table](README.md#the-reconstruction-revealed).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. You're handed a raw CloudTrail export. What is the **first** question you ask of it — before reading a
   single event — and why does cloud IR start there and not with the events themselves?
2. The first-incident responders removed the attacker's access and saw no further activity. Why is that
   **not eradication** — what survives an eviction?

---

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

`data/cloudtrail/incident.json` holds **17 CloudTrail events** spanning the full attack chain;
`data/vpc/flowlogs.csv` holds VPC flow logs including large outbound transfers to an external IP.
`triage.py` is the reconstruction tool you'll read, run, and **extend** — treat it as a junior analyst,
not the verdict.

> **▸ On track if:** `make demo` prints a banner (`APP FINANCIAL — INCIDENT TIMELINE`), a phase-grouped
> timeline ending in a `Remediation (SOC)` block, an **IOCs** section, and a **CONTAINMENT CHECKLIST** —
> the environment is live and the reconstruction ran end to end.

> **Authorization note.** Only test systems you own or have explicit written permission to test. This lab
> uses bundled synthetic data modelled on real cloud-IR cases; no real account or credentials are involved.

---

## Scenario

It is 08:45 UTC on 2024-11-14. The target account's SOC got a GuardDuty alert at 08:40 — **six hours after
the fact** — for `UnauthorizedAccess:IAMUser/TorIPCaller`. You're handed a raw CloudTrail export and the
flow logs and told: reconstruct the incident, determine what was exfiltrated, find any persistence the
attacker left, and have a timeline + IOC set ready for the executive briefing in 90 minutes. **The LastPass
parallel is your watch-out:** the obvious containment (kill the known key) is the one that left a door open
last time. Scope past it.

The trail was **stopped at 02:18 UTC and re-enabled at 08:35 UTC** by the SOC. You have complete logs for
02:14–02:18 (the attack window) and from 08:30 onward (remediation). The hours between are the gap.

Each step runs the same rhythm: **Predict** (commit before you look) → **Do** (reconstruct the evidence) →
**Reveal** (check your call) → **Record** (one line in the timeline/report).

---

## Build it — read a little, do a little

### Part 1 — Reconstruct the timeline (the super-timeline move)

#### Step 1 — Ask the first question before you read an event

**Concept (30 sec):** Flight-card #1 and #5. Cloud IR is reconstruction from an immutable API log — so
before any event, you ask whether the record is *whole*. A `StopLogging` gap is not missing data; the gap
itself is evidence.

**Predict, then do:** commit a guess — is the trail intact? Then open `data/cloudtrail/incident.json` (or
read the `make demo` timeline) and find the event that answers it, the timestamp it fires, and where the
gap opens and closes.

> **▸ On track if:** you find `StopLogging` on `main-trail` at **02:18:05** (in the `Defense Evasion` block)
> and `StartLogging` at **08:35:00** (in the `Remediation` block). **Record:** the gap runs 02:18–08:35,
> **~6h 17m** blind — bounds and duration are your first timeline rows, and the gap is evidence, not absence.

#### Step 2 — Triage by hand, then check the tool

**Concept (30 sec):** The tool is a junior analyst. Run your own reconstruction first, then read
`triage.py`'s output as a *check* — noting both what you missed and what the tool missed.

**Do it:** from the raw JSON establish the attacker's source IP, the initially-compromised principal, and
the order of events. Then `make demo` and compare.

> **▸ On track if:** you land on source IP **`203.0.113.42`** and initial principal **`dev-alice`
> (`AKIAIOSFODNN7EXAMPLE`)**, and you notice the tool's blind spot: its **IOC access-key list shows only
> `AKIAIOSFODNN7EXAMPLE` and `AKIAI8SFODNN7EXAMPLE`** — it flags the *SOC analyst's own* key as an IOC
> (false positive) and **never lists the planted `AKIAI7SFODNN7EXAMPLE`** (false negative). That gap is the
> lab. **Record:** what the tool got wrong, both directions.

#### Step 3 — Reconstruct the attack chain, phase by phase

**Concept (30 sec):** Flight-card #2 and #3. Every event already carries its timestamp — your job is to
sort on it and tag each with its kill-chain phase, then confirm the tag against its ATT&CK-for-Cloud
technique. The `userIdentity` **type** change is the escalation, in one field.

**Predict, then do:** before you find it, predict the escalation hop — how does a *dev* key reach the
`financial-reports-prod` bucket? Then walk the sorted timeline and build a row per event.

> **▸ On track if:** you find the transition **`IAMUser dev-alice` → `AssumeRole DataPipelineRole` →
> `AssumedRole` (session `attacker-session-1731549362`)** at 02:16 — the `userIdentity` type flip *is* the
> privilege escalation, and it's what lets the next four `GetObject`s read the finance bucket. **Record:**
> the phase table row for each event (phase · eventName · time · ATT&CK ID · meaning), e.g. Initial Access
> `GetCallerIdentity` **T1078.004**, Enumeration `ListRoles`/`ListBuckets` **T1069.003 / T1530**,
> Priv-Esc `AssumeRole` **T1078.004**, Collection `GetObject`×4 **T1530**, Exfiltration
> `PutBucketReplication` **T1537**, Defense Evasion `StopLogging` **T1562.008**, Persistence
> `CreateAccessKey` **T1098**.

### Part 2 — Corroborate, scope, and contain

#### Step 4 — Corroborate exfil across both planes

**Concept (30 sec):** Flight-card #4. CloudTrail tells you *what API was called by whom*; flow logs tell
you *how many bytes left, to where*. Together they turn a hunch into a verdict.

**Do it:** in the flow-log output from `make demo`, find the outbound flow(s) to the attacker IP
`203.0.113.42` and line them up in time with the CloudTrail `GetObject`s.

> **▸ On track if:** you flag the **`LARGE OUTBOUND to known attacker IP`** rows — `10.0.2.55 → 203.0.113.42`
> of **18,547,200 B** and **13,893,120 B** accepted — and note the **43,008,000 B `REJECT`** that was
> *blocked* (attempted, not exfiltrated). **Record:** control-plane `GetObject`s + data-plane ~32 MB
> accepted outbound to an external IP = a **defensible exfiltration finding**; the flow log adds volume and
> direction CloudTrail alone can't give.

#### Step 5 — Find the persistence — scope past the obvious key (the LastPass lesson)

**Concept (30 sec):** Flight-card #6. Containment ≠ eradication. The attacker plants footholds *before* the
trail stops; a naive revoke of the known key evicts nothing.

**Predict, then do:** if the SOC disables only the original key `AKIAIOSFODNN7EXAMPLE`, is the attacker out?
Then hunt the events between escalation and `StopLogging`.

> **▸ On track if:** you find **two** persistence mechanisms planted before 02:18 — `CreateAccessKey` on
> `dev-alice` minting **`AKIAI7SFODNN7EXAMPLE`** (in the event's `responseElements`, which is exactly why
> `triage.py`'s IOC list misses it), and the `PutBucketReplication` rule to **external account
> `999999999999`** (`attacker-staging-exfil-bucket`). **Record:** both mechanisms, and confirm the
> containment list must address all three — original key, planted key, replication rule.

#### Step 6 — Write the impact assessment

**Do it:** four objects were read from `financial-reports-prod` (three quarterly earnings PDFs + a
`2024-compensation.xlsx`) and a replication rule was added. In one paragraph state: what is **confirmed
exfiltrated** (in CloudTrail + corroborated by flow volume), what **may have** gone via the replication
rule before it was removed, and the **regulatory notification** implication (financial + compensation data
→ state privacy law / GDPR).

> **▸ On track if:** your containment order reads **revoke both keys → close the exfil channel (delete the
> replication rule) → block `203.0.113.42` → preserve evidence → restore logging, then re-scope** — the
> order in the module's containment table, not the tool's default checklist. **Record:** the impact
> paragraph.

### Part 3 — Automate the reconstruction

#### Step 7 — Extend `triage.py` to surface the gap automatically

**Do it:** add `print_gap_analysis()` that detects a `StopLogging` event, computes the duration to the
matching `StartLogging`, and prints a warning with the gap bounds and length. Run `make demo` and confirm
the gap appears — this turns "is the trail intact?" from a manual check into one the tool always makes.

> **▸ On track if:** `make demo` now prints a gap warning showing **02:18:05 → 08:35:00, ~6h 17m** — the
> tool now asks the first question for you.

---

## Prove the control (your finish line)

One finish line, two artifacts that must agree with the evidence:

1. **The investigation timeline** — `timeline.md`: a row per attacker event (phase · eventName · time ·
   ATT&CK ID · meaning), sorted on *time*, with the `StopLogging` gap called out as its own rows. Every row
   must trace to an event in `incident.json` or a flow in `flowlogs.csv`.
2. **The containment action list, built from the evidence** — an ordered list that names **all three**
   footholds (`AKIAIOSFODNN7EXAMPLE`, the planted `AKIAI7SFODNN7EXAMPLE`, and the replication rule to
   `999999999999`) plus blocking `203.0.113.42` — i.e. it scopes *past* the obvious key. If your list
   matches `triage.py`'s default checklist, you haven't scoped past the tool's blind spot yet.

Score your three README "Call it" predictions against the reveals; note which you missed — especially Q1
(what survives an eviction).

---

## Recall check — close the doc, answer from memory (3 min)

1. Why didn't revoking the original key contain the incident — what did the attacker plant, and when?
2. Why is an `AssumeRole` + mass `GetObject` in CloudTrail a *defensible* exfil finding only once you pair
   it with the flow log?
3. What are the bounds and duration of the logging gap, and why is a gap *evidence* rather than missing data?

---

## Deliverables

- `timeline.md` — the attack-chain table (phase, eventName, timestamp, technique ID, meaning), with the
  `StopLogging` gap called out.
- `impact.md` — the impact assessment from Step 6 (confirmed vs. potential exfil, regulatory implication,
  containment order).
- `triage.py` — updated with `print_gap_analysis()` and the `--json` output below.
- Do **not** commit credentials, bucket contents, or any real account data.

## Automate & own it

**Required — judgment-as-code, the reconstruction made repeatable.** Extend `triage.py` with a `--json`
flag that emits the whole reconstruction as one structured JSON object: keys `timeline` (the ordered event
list), `iocs` (IPs, access keys, principals, buckets, external accounts), and `containment_checklist` (the
ordered action strings). This is the super-timeline move encoded — heterogeneous events merged and sorted on
time, then serialized so the next responder (or a SOAR runbook) consumes it without re-deriving it. Have a
model draft the `--json` flag and serialization; **review every line.** Before committing: run it, pipe
through `python -c "import json,sys; json.load(sys.stdin)"` to prove valid JSON, and verify the `iocs`
section contains **all** attacker-associated keys and IPs *and* the external replication account — including
the planted `AKIAI7SFODNN7EXAMPLE` that the tool's current IOC pass misses. Fixing that omission in your
serialization *is* the LastPass lesson turned to code. You own the logic and the verdict it encodes.

## Definition of done (`cloud-incident-response` ✅)

- [ ] You have a complete attack-chain table covering every attacker event, sorted on time, with an ATT&CK
  technique ID per row.
- [ ] You can name **both** keys and the replication rule, and your containment list addresses all three —
  i.e. you scoped past the obvious key and past the tool's IOC blind spot.
- [ ] Your exfil finding cites *both* planes (CloudTrail `GetObject`s + the flow-log outbound volume).
- [ ] `print_gap_analysis()` fires and prints the correct gap (~6h 17m), and `--json` emits valid JSON whose
  `iocs` include the planted key and external account.
- [ ] You scored your three README "Call it" predictions against the reveals — especially Q1.
- [ ] You can explain all six flight-card facts cold.

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
- Map the lab back to the anchor: write the one-paragraph parallel between the target account's persistence
  keys and LastPass's incident-1-data-as-incident-2-recon. Where is the "containment ≠ eradication" gap in each?
