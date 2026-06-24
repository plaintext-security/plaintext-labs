# Lab 18 — Catch the Drift: Telemetry Health & Detection Decay

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/18-detection-drift
make up           # build the Python container
make demo         # drift check at t=0 (CLEAN) then t=30 (3 drifts, non-zero exit)
make baseline     # snapshot t=0 health + per-rule recall — your known-good
make drift-check  # the scheduled control: re-run the loop, non-zero exit if drift
make shell        # work inside the container
make down         # stop it
```

What ships:

- A small **estate** of telemetry sources (4 simulated `corp.local` hosts:
  `WIN10-01`, `FS01`, `DC01`, `LEGACY03`) and a declared **baseline manifest**
  (`baseline/sources.yml`) — per source, the heartbeat interval and volume floor you
  expect. This is the "expected" half you tune.
- A healthy event stream (`data/events_t0.jsonl`) and a **drifted** one one month
  later (`data/events_t30.jsonl`) — the drift is *baked into the fixtures*, not
  printed in the manifest, so you have to detect it.
- A held-out **labelled corpus** (`corpus/corpus_t0.jsonl`, `corpus/corpus_t30.jsonl`)
  of known-bad + known-good events for re-scoring, plus the Sigma detection that rots
  under schema drift (`rules/encoded_powershell.yml`, carried over from module 08).
- The **drift harness** `drift_check.py` — it runs both checks (telemetry heartbeat +
  volume, and detection re-score against the corpus) and exits non-zero when drift is
  present. `make demo` shows it catching all three injected drifts.

> Everything runs locally against bundled data you own. No external targets, no authorization needed.

## Scenario
A corporate SOC stood up its detection stack last quarter and signed off as "fully covered."
It is now a month later. Overnight, three things happened that nobody noticed: a workstation's agent
cert expired and it stopped logging, a busy server's collector started choking and now ships a tenth of
its events, and a Windows update renamed a field that one of your best rules depends on. Every dashboard
is still green. Your job: build the steady-state loop that *would* have caught all three, then prove you
can reconcile back to a known-good baseline.

## Do
1. [ ] **See the loop end to end.** Run `make demo`. It runs the harness twice: at
   **t=0** against the healthy estate (verdict CLEAN, exit 0), then at **t=30**
   against the drifted estate (3 drifts, non-zero exit). Read the t=30 output but
   don't trust the labels yet — work out *why* each line fired.
2. [ ] **Declare and snapshot the baseline.** Open `baseline/sources.yml` and study the
   declared `heartbeat_interval_s` and `volume_floor` per source. Tune them against
   what *you* judge sensible (too tight pages on jitter; too loose never catches a
   degraded collector) and justify each number. Run `make baseline` to snapshot t=0
   health + per-rule recall — this is your known-good.
3. [ ] **Read the harness.** Open `drift_check.py` and trace its two checks: the
   telemetry heartbeat+volume check (`--baseline` vs. `--events`) and the detection
   re-score (`--rule` fired against `--corpus`, diffed vs. `--baseline-recall`).
   Confirm you understand *how* a degraded-but-up source is distinguished from a dead
   one — a binary up/down check would miss it.
4. [ ] **Detect telemetry drift.** Run the check against the t=30 events
   (`make drift-check`). It should flag **both** the dead source and the
   degraded (low-volume) one. Identify which host is which from the output.
5. [ ] **Detect detection drift.** The same run re-scores `rules/encoded_powershell.yml`
   against `corpus/corpus_t30.jsonl`. Find the rule whose recall fell to zero while it
   still parses and runs — then open the corpus and the rule and identify the **renamed
   field** that rotted it.
6. [ ] **Report the delta.** Emit one drift report: expected-vs-observed sources
   (table) and the rule whose score regressed, with the suspected cause for each of the
   three drifts.
7. [ ] **Reconcile and prove steady-state.** For each finding, take the right action:
   fix the rotted rule's field and re-score to baseline; and for `LEGACY03` (which turns
   out to be intentionally decommissioned) set `decommissioned: true` in
   `baseline/sources.yml` so it stops alarming. Re-run `make drift-check` against the
   reconciled state and confirm the rule recall is back to baseline and the
   decommissioned source no longer fires.

## Success criteria — you're done when
- [ ] The check flags **both** the dead source and the degraded (low-volume) source — and
  you can state which host is which.
- [ ] The re-score surfaces the rotted rule as a recall regression and you've named the
  renamed field (`CommandLine` → `ProcessCommandLine`).
- [ ] Your drift report names all three drifts with a plausible, evidence-backed cause for each.
- [ ] After reconciliation the rule re-scores to baseline and the decommissioned source no longer alarms.
- [ ] You can state your chosen heartbeat interval and volume floor and *why* those numbers (not a vibe).

## Deliverables
The tuned `baseline/sources.yml` (with `LEGACY03` reconciled), the fixed
`rules/encoded_powershell.yml`, a **drift report** (`drift-report.md`), and a
**`reconciliation-runbook.md`**: the decision tree for each drift class (source dead
vs. degraded vs. decommissioned; rule rotted) and the exact action each demands.
**Commit all of these.** Lab artifacts (raw event dumps) stay out of commits.

## Automate & own it
**Required.** `make drift-check` already runs the loop with a non-zero exit on drift —
turn it into a *scheduled control*. Wire it to run on a schedule (a cron entry or a
GitHub Actions `schedule:` trigger committed alongside) and have it emit the drift
report as an artifact, paging only when the exit is non-zero. Have a model draft the
schedule + report wiring; **you read every line**, you set the thresholds in
`baseline/sources.yml` against your real baseline, and you confirm it actually exits
non-zero on the t=30 fixtures before trusting it. A steady-state loop that nobody
scheduled is a script, not a control.

## AI acceleration
Let a model draft the heartbeat logic, the volume-baseline query, and the report formatter — it's good
at that scaffolding. Then do the part it can't: set the interval and volume floor against *your* baseline
(an AI's default will either scream nightly or never fire), and reject its narrated root causes unless the
evidence is in the report. Ask it to "summarise what drifted" and watch it invent a confident cause — that
is the lesson. The model drafts the loop; you own every threshold and every verdict.

## Connects forward
This loop consumes the held-out corpus from **module 09 (detection testing & tuning)** and keeps the
**module 10 (ATT&CK coverage)** map honest over time — a coverage map is a snapshot that rots without
this. The detect→diff→reconcile pattern is the same one config-management and cloud-posture drift use;
you'll meet it again in the automation and cloud tracks. It also pairs with **module 17 (KEV-driven
defense)**, which is feed-drift: this module is the *internal* drift KEV doesn't cover.

## Marketable proof
> "I run detection coverage as a steady-state practice: a scheduled drift loop that heartbeats my log
> sources by volume, re-scores my detections against a held-out corpus, and reconciles drift to a
> declared baseline — so my t=0 coverage is still my t=30 coverage."

## Stretch
- Add a **graceful-baseline** feature: distinguish a source that legitimately goes quiet on a schedule
  (a nightly batch host) from one that failed, so you don't page on the expected silence.
- Track the per-rule recall as a time series across several drift/reconcile cycles and plot the decay —
  the visual case for why "set and forget" fails.
