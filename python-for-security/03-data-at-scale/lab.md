# Lab 03 — Stream a Real Feed, Query It Columnar, Log It Structured

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/03-data-at-scale/`: the `sift` project from Module 02, a bundled
(trimmed) URLhaus sample plus a pointer to the full dump, and `polars`/`duckdb`/`structlog` installed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/03-data-at-scale
make up      # build the container with the sift project + data tooling
make shell   # work on sift
make demo    # streams the sample feed, runs the columnar triage query, emits JSON logs
make down
```

Reproducible at zero cost; the bundled sample runs offline, the full feed is fetched on demand.

## Scenario

`sift` currently validates one alert at a time. Now it has to handle a **real** feed: abuse.ch URLhaus,
a live catalog of malicious URLs that's millions of rows. You'll make `sift` stream it without exhausting
memory, answer triage questions with a columnar engine instead of Python loops, and emit structured logs
a SIEM could ingest.

> Only test systems you own or have explicit written permission to test. This lab reads a public threat
> feed and processes bundled data locally.

## Do

1. [ ] **Feel the failure first.** Load the full (or large sample) feed with `json.load()` /
   `read().splitlines()` into a list and watch memory climb (or OOM). This is the copilot's default —
   see it break before you fix it.
2. [ ] **Stream the parse.** Rewrite ingestion as a generator that reads line-by-line, validates each row
   into Module 02's `Alert` model, and `yield`s it. Memory stays flat regardless of feed size.
3. [ ] **Answer a triage question with a columnar query.** Use `duckdb` (SQL over the file) or `polars`
   (lazy frame) to compute, e.g., top 20 source domains by alert count and the per-hour volume — no
   hand-rolled `dict` counting.
4. [ ] **Structure the logs.** Configure `structlog` for JSON output; replace every `print()` in `sift`
   with a structured event (`log.info("triaged", indicator=..., verdict=..., source=...)`).
5. [ ] **Prove it scales.** Run the streaming path over the full dump (or a large slice) and show memory
   stays bounded while the in-memory version from step 1 does not.
6. [ ] **Automate & own it.** Commit the streaming ingest, the columnar triage query, and the `structlog`
   config into `sift`. In the commit note, record what the copilot generated and the scale bug you caught
   (the slurp, the `print`, or an unbounded aggregation).

## Success criteria — you're done when
- [ ] `sift` ingests the feed as a **stream** — memory stays flat on the full dump.
- [ ] At least one triage question is answered by a `polars`/`duckdb` query, not a Python loop.
- [ ] All of `sift`'s output goes through `structlog` as **JSON events with fields** (no bare `print`).
- [ ] You can show the in-memory approach failing (or ballooning) where the streaming one holds.

## Deliverables
The updated `sift` repo: streaming ingest module, the columnar triage query, the `structlog` config, and
a short note on the memory difference (numbers, not vibes). Do **not** commit the multi-hundred-MB feed
dump — reference it and fetch it in the lab.

## AI acceleration
Ask the copilot to "process the URLhaus feed and report the top sources." It will almost certainly slurp
the file and `print` the answer. Your job is the review: make it stream, push the aggregation into
`duckdb`/`polars`, and log structured. The caught bug is the whole point — the code *worked* on the
sample and would have died in production.

## Connects forward
The streaming + structured-log foundation is what Module 04 enriches concurrently and Module 09 measures.
Your `structlog` JSON is exactly the kind of telemetry Track 02 (Defensive) parses and detects on — you're
producing one side of a seam you'll consume from the other.

## Marketable proof
> "I build Python security tooling that streams multi-million-row threat feeds with flat memory, runs
> triage queries in `duckdb`/`polars`, and emits `structlog` JSON a SIEM can ingest — and I catch the
> in-memory scale bugs an AI copilot ships."

## Stretch (optional)
- Write the triaged output as Parquet and query it back with `duckdb` — feel the columnar speedup vs CSV.
- Add a `--since` window to the triage query and bind a request-id into the `structlog` context so every
  log line for one run is correlatable.
