# Lab 18 — Catch the Drift: Telemetry Health & Detection Decay

*Hands-on lab · [← Back to the module concept](README.md)*

!!! warning "Lab environment status — to be built & validated (Phase 2)"
    The Docker environment for this lab is **not yet built or validated**. The `plaintext-labs/defensive/18-detection-drift/`
    directory currently holds this `lab.md` and the build spec below; the `docker-compose.yml`, `Makefile`,
    seed data, and `demo` target are **Phase 2 work**. Until `make up && make demo && make down` is green on a
    clean Linux runner, treat the commands below as the intended shape, not a tested path. (No `.ci-demo`
    marker is added until then — see the honor-system note in the repo's `CLAUDE.md`.)

## Setup
This will be a **reference lab** — a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Planned shape:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/18-detection-drift
make up        # start the log ingest + a tiny "estate" of sources emitting events
make demo      # baseline → inject drift → detect the delta → reconcile, end to end
make shell     # work inside the container
make down      # stop it
```

Planned contents:

- A small **estate** of telemetry sources (e.g. 3–4 simulated hosts) emitting JSONL events to an
  ingest at a steady rate, plus a declared **baseline manifest** (`baseline/sources.yml`) listing
  the sources you expect, their expected interval, and a 7-day volume average.
- A handful of **Sigma detections** (carried over from module 08's shape) and a small **held-out
  corpus** (`corpus/`) of labelled known-bad + known-good events for re-scoring.
- A **drift injector** (`drift/inject.py`) that can: silently kill a source, *degrade* a source to a
  fraction of its volume, and rename a field in the event schema so a rule rots.
- Starter scaffolds you complete: `health/heartbeat.py` and `health/rescore.py`.

> Everything runs locally against bundled data you own. No external targets, no authorization needed.

## Scenario
Meridian Financial's SOC stood up its detection stack last quarter and signed off as "fully covered."
It is now a month later. Overnight, three things happened that nobody noticed: a workstation's agent
cert expired and it stopped logging, a busy server's collector started choking and now ships a tenth of
its events, and a Windows update renamed a field that one of your best rules depends on. Every dashboard
is still green. Your job: build the steady-state loop that *would* have caught all three, then prove you
can reconcile back to a known-good baseline.

## Do
1. [ ] **Declare the baseline.** Run `make demo` once to see the loop end to end, then open
   `baseline/sources.yml`. Record, for each source, the heartbeat interval you expect and a volume
   floor (a sensible fraction of its baseline rate). Run `make baseline` to snapshot the *current*
   per-rule scores against the held-out corpus — this is your t=0 detection effectiveness.
2. [ ] **Build the heartbeat + volume check.** Complete `health/heartbeat.py` so it reports, per
   source: last-seen timestamp, whether it's overdue, and whether its recent volume has dropped below
   the floor. *Hint:* a binary up/down check is not enough — the degraded source is still "up."
3. [ ] **Inject drift.** Run `make drift` (wraps `drift/inject.py`). It silently (a) stops one source,
   (b) degrades another to ~10% volume, and (c) renames a field one rule matches on. Do **not** look at
   which — find them.
4. [ ] **Detect telemetry drift.** Run your heartbeat check. It should flag the dead source *and* the
   degraded one. Confirm the binary "is it up?" view would have missed the degraded one.
5. [ ] **Detect detection drift.** Complete `health/rescore.py` to re-fire every rule against the
   held-out corpus and diff per-rule recall vs. your t=0 baseline. The field-rename should surface as a
   rule whose recall fell to zero while it still "runs" without error.
6. [ ] **Report the delta.** Emit one drift report: expected-vs-observed sources (table), and any rule
   whose score regressed, with the suspected cause for each.
7. [ ] **Reconcile.** For each finding, take the right action and *prove steady-state*: redeploy/repair
   the sources, fix the rotted rule's field and re-score to baseline, and — for the source that turns
   out to be intentionally decommissioned — **prune the baseline** so it stops alarming. Re-run the loop:
   it should report no drift.

## Success criteria — you're done when
- [ ] Your heartbeat check flags **both** the dead source and the degraded (low-volume) source.
- [ ] Your re-score surfaces the rotted rule as a recall regression (and you've identified the renamed field).
- [ ] Your drift report names all three injected drifts with a plausible, evidence-backed cause for each.
- [ ] After reconciliation the loop reports **clean** — and the decommissioned source no longer alarms.
- [ ] You can state your chosen heartbeat interval and volume floor and *why* those numbers (not a vibe).

## Deliverables
`health/heartbeat.py` + `health/rescore.py` (your completed detectors), the `baseline/sources.yml`
you tuned, the **drift report** (`drift-report.md`), and a **`reconciliation-runbook.md`**: the
decision tree for each drift class (source dead vs. degraded vs. decommissioned; rule rotted) and the
exact action each demands. **Commit all of these.** Lab artifacts (raw event dumps, the injector's
state) stay out of commits.

## Automate & own it
**Required.** Wrap the loop into one scheduled command — `make drift-check` — that runs the heartbeat,
the re-score, and emits the report with a non-zero exit when drift is present, and wire it to run on a
schedule (a cron entry or a GitHub Actions `schedule:` trigger committed alongside). Have a model draft
the runner and the schedule; **you read every line**, you set the thresholds against your real baseline,
and you confirm it actually exits non-zero on injected drift before trusting it. A steady-state loop that
nobody scheduled is a script, not a control.

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
