# Lab 07 — Enrichment & Data Pipelines

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/07-enrichment-pipelines
make up        # starts collector + processor + mock API (three containers)
make demo      # runs pipeline for 30 seconds and shows processed output
make shell     # shell in processor container
make down
```

Three containers: a **collector** that writes a new alert JSON to `shared/pending/` every 5
seconds; a **processor** that reads from `shared/pending/`, queries the mock threat-intel API,
enriches the alert, and writes to `shared/processed/`; and the **mock threat-intel API** from
module 04. A shared Docker volume (`shared/`) connects collector and processor.

## Scenario
Meridian's SIEM generates ~12 alerts per minute. The team wants a pipeline that automatically
enriches each alert with threat-intel before it reaches the analyst queue. `make demo` shows
the pipeline running live — alerts flowing from collector through processor, enriched and stored.

## Do
1. [ ] `make demo` — watch the pipeline run for 30 seconds. How many alerts are generated?
   How many are enriched? Check `shared/processed/` for the enriched JSON files.
2. [ ] Read `collector/collector.py`. Understand how it generates a realistic alert JSON and
   writes it as `pending/<uuid>.json`. Note the `schedule.every(5).seconds.do(generate_alert)` pattern.
3. [ ] Write `processor/processor.py`:
   - Watch `shared/pending/` for new `.json` files (use `os.listdir()` in a `schedule` loop).
   - For each pending file: load it, call the mock enrichment API, add the verdict to the
     alert JSON, write to `shared/processed/<uuid>.json`, delete from `pending/`.
   - Log each event: `[PROCESSED] {uuid} verdict={verdict} duration={ms}ms`.
   - Handle timeout (`httpx.TimeoutException`): log the error, move the file to
     `shared/errors/` rather than deleting it.
4. [ ] Test resilience: `docker compose stop threat-api` — watch the processor move timed-out
     alerts to `shared/errors/`. `docker compose start threat-api` — watch the pipeline resume.
5. [ ] Verify: after `make demo`, count the files in `shared/processed/` and confirm they match
   the collector's output count (minus any errors).

## Success criteria — you're done when
- [ ] `processor.py` correctly enriches alerts and writes to `shared/processed/`.
- [ ] Timed-out alerts go to `shared/errors/` not `shared/processed/`.
- [ ] The log line format is `[PROCESSED] {uuid} verdict={verdict} duration={ms}ms`.
- [ ] After API restart, the pipeline resumes without manual intervention.

## Deliverables
`processor/processor.py`. Commit it. The shared volume contents are runtime artifacts — not
committed.

## Automate & own it
**Required.** Add a `monitor.py` script that reads from `shared/processed/` every 10 seconds and
prints a live summary: total processed, total errors, average enrichment time, and the last 5
verdicts. Have a model draft it; run it alongside the pipeline and verify the counts match.
Commit `monitor.py` as a standalone monitoring tool.

## AI acceleration
Ask a model to write the directory-polling loop with error handling. Then test it: what happens
when a `pending/` file is malformed JSON? Does it crash? Does it log the error and continue? An
enrichment pipeline that crashes on a malformed alert is less useful than one that logs and skips
it. The model's first draft usually lets `json.loads()` raise an unhandled exception.

## Connects forward
This pipeline is the data flow that the SOAR playbook in module 08 extends: instead of writing
to `shared/processed/`, the processor will trigger a workflow. The monitoring script pattern
also connects to Track 12 (AI-augmented ops).

## Marketable proof
> "I've built a durable enrichment pipeline: collector writes to a pending queue, processor
> enriches and stores, errors go to a dead-letter directory, and a monitoring script gives
> live visibility — all in about 100 lines of Python."

## Stretch
- Add a `backfill.py` script that processes all files in `shared/errors/` on demand — the
  manual drain for the dead-letter queue.
- Replace the directory queue with Redis using `redis-py` — same interface, better visibility
  via `redis-cli monitor`.
