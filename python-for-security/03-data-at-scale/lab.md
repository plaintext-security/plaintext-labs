# Lab 03 — Stream a Real Feed, Query It Columnar, Log It Structured

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/03-data-at-scale/`: the `sift` project from Module 02, the `make` step
that fetches the pinned Malware-Traffic-Analysis.net 2024-07-30 "You dirty rat!" infection PCAP
(checksum-verified, zip password `infected_20240730`) and runs **Suricata** (ET Open) over it to produce a
real **`eve.json`**, pointers to the secondary corpora (**Loghub**, CC BY 4.0, bundleable; a live
**URLhaus** pull), and `polars`/`duckdb`/`structlog` installed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/03-data-at-scale
make up      # build the container; fetch+checksum the PCAP, run Suricata → eve.json
make shell   # work on sift
make demo    # streams eve.json, runs the columnar triage query, emits JSON logs
make down
```

Reproducible at zero cost; the PCAP is **fetched, never mirrored** (checksum-verified) and Suricata
generates `eve.json` on the runner. The secondary corpora (Loghub, or a live URLhaus pull) are fetched on
demand.

## Scenario

`sift` currently validates one alert at a time. Now it has to handle a **real** feed at scale — the
`eve.json` Suricata emits over a genuine RAT-infection capture. The bundled capture is modest, so the demo
**replays it** to hundreds of thousands of newline-delimited events (regenerate from a busier capture for
true volume). You'll make `sift` stream it without exhausting memory, answer triage questions with a
columnar engine instead of Python loops, and emit structured logs a SIEM could ingest.

> Only test systems you own or have explicit written permission to test. This lab processes a public,
> pre-captured infection PCAP and its Suricata output locally — you are not attacking a live target.

## Do

1. [ ] **Feel the failure first.** Load the whole `eve.json` with `json.load()` /
   `read().splitlines()` into a list and watch memory climb (or OOM). This is the copilot's default —
   see it break before you fix it.
2. [ ] **Stream the parse.** Rewrite ingestion as a generator that reads `eve.json` line-by-line,
   validates each line into Module 02's EVE `AlertEvent` model, and `yield`s it. Memory stays flat
   regardless of feed size.
3. [ ] **Answer triage questions with a columnar query.** Use `duckdb` (SQL over the file) or `polars`
   (lazy frame) over real EVE fields — e.g. top 20 `alert.signature` by count, the loudest-talker
   `dest_ip`s, and per-hour alert volume derived from `timestamp` — no hand-rolled `dict` counting.
4. [ ] **Structure the logs.** Configure `structlog` for JSON output; replace every `print()` in `sift`
   with a structured event over real EVE fields
   (`log.info("triaged", signature=..., dest_ip=..., verdict=...)`).
5. [ ] **Prove it scales.** Run the streaming path over the full `eve.json` (or a large slice) and show
   memory stays bounded while the in-memory version from step 1 does not.
6. [ ] **Automate & own it.** Commit the streaming ingest, the columnar triage query, and the `structlog`
   config into `sift`. In the commit note, record what the copilot generated and the scale bug you caught
   (the slurp, the `print`, or an unbounded aggregation).

## Success criteria — you're done when
- [ ] `sift` streams `eve.json` — memory stays flat on the full feed.
- [ ] At least one triage question over real EVE fields (e.g. top 20 `alert.signature`) is answered by a
  `polars`/`duckdb` query, not a Python loop.
- [ ] All of `sift`'s output goes through `structlog` as **JSON events with fields** (no bare `print`).
- [ ] You can show the in-memory approach failing (or ballooning) where the streaming one holds.

## Deliverables
The updated `sift` repo: streaming ingest module, the columnar triage query, the `structlog` config, and
a short note on the memory difference (numbers, not vibes). Do **not** commit the PCAP or the generated
`eve.json` — reference them and regenerate in the lab.

## AI acceleration
Ask the copilot to "process this `eve.json` and report the top alert signatures." It will almost
certainly slurp the file and `print` the answer. Your job is the review: make it stream, push the
aggregation into `duckdb`/`polars`, and log structured. The caught bug is the whole point — the code
*worked* on a 10-line sample and would have died on the real feed.

## Connects forward
The streaming + structured-log foundation is what Module 04 enriches concurrently and Module 09 measures.
Your `structlog` JSON is exactly the kind of telemetry Track 02 (Defensive) parses and detects on — you're
producing one side of a seam you'll consume from the other.

## Marketable proof
> "I build Python security tooling that streams a real Suricata `eve.json` with flat memory, runs triage
> queries (top signatures, top talkers, per-hour volume) in `duckdb`/`polars`, and emits `structlog` JSON
> a SIEM can ingest — and I catch the in-memory scale bugs an AI copilot ships."

## Stretch (optional)
- Write the triaged output as Parquet and query it back with `duckdb` — feel the columnar speedup vs
  reading the raw `eve.json`.
- Add a `--since` window to the triage query and bind a request-id into the `structlog` context so every
  log line for one run is correlatable.
- [ ] **Dissect `http`, then triage it columnar.** *Objective:* extend Module 02's growing typed union
  (which added `dns`) with an `HttpEvent` member for `event_type:"http"`, pinning `http.hostname`,
  `http.url`, and `http.status`; then answer a triage question over the new event type with a columnar
  query — e.g. top 20 `http.hostname` by request count, or the count of non-200 `http.status`. *Acceptance:*
  every `http` line validates into the union (no longer quarantined as an unknown type), and one
  `duckdb`/`polars` query returns a ranked `http.hostname` (or `http.status`) table over the real feed.
  This is the rung of the dissector thread for this module — the dissector earns its keep by feeding a
  columnar triage query, exactly this module's skill.
