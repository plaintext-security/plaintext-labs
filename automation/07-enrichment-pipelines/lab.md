# Lab 07 — Enrichment & Data Pipelines

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate.** You build and operate a durable two-stage enrichment pipeline: a
collector produces alerts into a queue, and the **processor you write** consumes the queue, enriches
each alert, and routes it to a store or a dead-letter directory. The deliverable is the *operating,
scheduled pipeline* — proved durable under a deliberate failure — plus the monitoring tool that gives
it visibility. No grader; you verify your own work against the observable success criteria below.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/07-enrichment-pipelines
make up        # starts collector + processor + mock threat-intel API (three containers)
make demo      # runs the pipeline for ~30 seconds and shows the processed output
make shell     # shell into the processor container
make down
```

Three containers share one Docker volume (`shared/`): a **collector** that writes a new alert JSON to
`shared/pending/` every 5 seconds; a **processor** that reads `shared/pending/`, queries the mock
threat-intel API, enriches each alert, and writes it to `shared/processed/` (or `shared/errors/` on
failure); and the **mock threat-intel API reused from Module 04**. The collector ships complete; the
processor is yours to write.

> **Note on the mock API:** the threat-intel service is a deterministic local stand-in, not a live
> feed — it returns a verdict per source IP so the pipeline is reproducible offline at zero cost. The
> *pipeline mechanics* you build (durability, dead-lettering, idempotency, observability) are real and
> transfer verbatim; only the enrichment source is a substitute. Point the same processor at a real
> feed (VirusTotal, AbuseIPDB, an internal CMDB) and only the `enrich_alert()` call changes.

## Scenario
A SOC's SIEM emits roughly 12 alerts per minute, and analysts are enriching each one by hand. You're
building the pipeline that enriches every alert with threat-intel *before* it reaches the analyst
queue — and, more importantly, building it so it doesn't lose alerts when the intel API blinks or the
processor restarts. `make demo` shows the pipeline running live: alerts flowing from collector through
processor, enriched and stored.

## Do
Build the processor, operate the pipeline, then prove it's durable by breaking it on purpose.

**Understand the producer and the queue**
1. [ ] `make demo` — watch the pipeline run for ~30 seconds. How many alerts does the collector
   generate, and how many land enriched in `shared/processed/`? `ls shared/pending/` and
   `ls shared/processed/` to see the queue and the store directly.
2. [ ] Read `collector/collector.py`. See how it generates a realistic alert and writes it as
   `pending/<uuid>.json`, and note the `schedule.every(5).seconds.do(generate_alert)` loop. The
   filename *is* the alert's UUID — you'll rely on that for idempotency.

**Build the processor — the consumer**
3. [ ] Write `processor/processor.py` as a `schedule` loop that, every few seconds, processes every
   `*.json` in `shared/pending/`. For each file:
   - Load it. If it's **malformed JSON**, log the error and move it to `shared/errors/` — do **not** let
     one bad file crash the loop. (Hint: catch `json.JSONDecodeError` around `json.loads()`.)
   - Call the mock enrichment API for the alert's `source_ip`, add the returned verdict to the alert
     JSON, and **write `shared/processed/<uuid>.json` first, then delete the file from `pending/`** —
     in that order. (This ordering is the durability guarantee — see step 7.)
   - On an enrichment **timeout** (`httpx.TimeoutException`), move the file to `shared/errors/` rather
     than deleting it (the dead-letter queue), so it's visible and drainable, not lost.
   - Log every processed event in the exact format `[PROCESSED] {uuid} verdict={verdict} duration={ms}ms`,
     and log every error too. (The reused enrichment call from Module 04 lives in `enrich_alert()`.)
4. [ ] `make down && make up && make demo` with your processor in place. Confirm enriched files appear
   in `shared/processed/` and each carries the verdict added by your code.

**Operate it — and prove durability under failure**
5. [ ] **Kill the intel API mid-flight:** with the pipeline running, `docker compose stop threat-api`.
   Watch your processor move timed-out alerts to `shared/errors/` instead of dropping them. Then
   `docker compose start threat-api` and confirm the pipeline resumes **without manual intervention**.
6. [ ] **Drop a poison message:** write a file containing `not-json` into `shared/pending/`. Confirm the
   loop logs it and moves it to `shared/errors/` — and keeps processing everything else.
7. [ ] **Prove at-least-once:** reason through (or test) what happens if the processor is killed
   *after* writing `processed/<uuid>.json` but *before* deleting the `pending/` copy. The alert is
   re-processed on restart and, because the output is keyed by the same UUID, the second pass
   overwrites the same `processed/` file — a harmless duplicate, never a lost alert. Confirm your code
   doesn't create two divergent outputs for one UUID (idempotency).

**Reconcile the counts**
8. [ ] After a clean `make demo`, confirm `processed + errors == generated` — no alert is unaccounted
   for. An alert is either enriched or dead-lettered; none silently vanishes.

## Success criteria — you're done when
- [ ] `processor.py` enriches alerts and writes them to `shared/processed/`, each with the verdict added.
- [ ] Timed-out alerts and malformed files go to `shared/errors/`, **not** `shared/processed/`, and a
      single bad file never crashes the loop.
- [ ] The processed log line is exactly `[PROCESSED] {uuid} verdict={verdict} duration={ms}ms`.
- [ ] After `docker compose stop threat-api` then `start`, the pipeline resumes on its own.
- [ ] Output is keyed by UUID so re-processing the same alert is idempotent (no divergent duplicates).
- [ ] `processed + errors == generated` — every alert is accounted for.

## Deliverables
Commit `processor/processor.py` and `monitor.py` (below). The `shared/` volume contents (pending,
processed, errors) are runtime artifacts — **not** committed. The artifact is the *operating, durable
pipeline*: a producer, your durable consumer, and the visibility tool over it.

## Automate & own it
**Required — the observability that makes the pipeline operable.** Add a standalone `monitor.py` that
reads `shared/processed/` and `shared/errors/` every 10 seconds and prints a live summary: total
processed, total errored, average enrichment duration, and the last 5 verdicts. This is the
**Tool-Build** beat of the module — treat it as a small reusable tool, not a throwaway: give it a
clear `--help`, a `--interval` flag, and a one-line README in the lab dir. Have a model draft it, then
**review every line and prove it's honest** — run it alongside a live `make demo` and confirm its
counts match what `ls shared/processed/ | wc -l` and `ls shared/errors/ | wc -l` report. A monitor
that disagrees with the directory is worse than none. Commit `monitor.py` alongside the processor.

## AI acceleration
Ask a model to write the directory-polling loop with error handling — then attack its blind spots,
because they're all in the failure modes. Drop a malformed file in `pending/`: does it crash, or
log-and-skip? Stop the API: does the alert vanish, or land in `errors/`? Check the ordering: does it
delete the input before writing the output (silent loss on a crash) or after (durable)? Re-feed the
same UUID: does it duplicate divergently? The model's first draft lets `json.loads()` raise unhandled
and usually deletes-then-writes; you own the version that survives the disk being full and the API
being down. (See Module 10 — *Reviewing AI-Generated Automation* — for this review discipline made into
its own lab.)

## Connects forward
This pipeline is the data flow the SOAR playbook in **Module 08** extends: instead of writing the
enriched alert to `shared/processed/`, the processor triggers a response workflow — the queue becomes
the trigger. The dead-letter and observability patterns are the same ones detection-as-code (Module
09) and Track 12 (AI-augmented ops) build on; an AI-triage stage is just another processor on the same
durable queue.

## Marketable proof
> "I've built and operated a durable enrichment pipeline: a collector produces to a pending queue, a
> processor enriches and stores with at-least-once delivery, timeouts and poison messages route to a
> dead-letter directory instead of being dropped, and a monitoring tool gives live visibility into
> throughput and errors — all in about 100 lines of Python, with the failure modes proven by breaking
> it on purpose."

## Stretch
- Add a `backfill.py` that drains `shared/errors/` back through the processor on demand — the manual
  retry for the dead-letter queue once the upstream recovers.
- Replace the directory queue with Redis (`redis-py`): same produce→consume interface, with
  `redis-cli MONITOR` and list-length as the backlog metric. Note what you gain (atomic pop,
  cross-host) and what you lose (the `ls`-able transparency of a directory).
- Add a tiny retry-with-backoff on the enrichment call before dead-lettering — and decide honestly when
  a retry helps (transient timeout) versus when it just delays the inevitable (the API is down).
