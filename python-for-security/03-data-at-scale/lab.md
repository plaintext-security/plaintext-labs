# Lab 03 — Stream a Real Feed, Query It Columnar, Log It Structured

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/03-data-at-scale` (the `sift`
> project from Module 02, a committed real Suricata **`eve.json`** from the MTA 2024-07-30 STRRAT
> infection capture, and `polars`/`duckdb`/`structlog` installed). This lab **adds one production stage
> to the same `sift`**: it streams a real EVE feed in bounded memory, answers triage questions with a
> columnar engine, and emits SIEM-ingestible JSON logs. Target: **~2–3 hrs.**
> *Intermediate-plus: the steps state objectives; you derive the streaming/`duckdb`/`structlog` code (with the copilot).*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **This lab grows `sift`, it doesn't replace it.** | You take Module 02's validated-alert reader and make it survive a *real* feed — same tool, one new stage. |
| 2 | **Stream the parse; never slurp the feed.** | A generator that reads line-by-line and `yield`s keeps memory flat whether `eve.json` is 100 lines or 100 million. |
| 3 | **Parse, don't trust — at every hop.** | Each streamed line is validated into a typed model as it flows; unknown `event_type`s are quarantined, not crashed on. |
| 4 | **Columnar beats loops.** | `duckdb`/`polars` answer "top signatures / loudest talker / per-hour volume" in vectorized C over larger-than-memory data — not a `dict` counter. |
| 5 | **Logs are data — structure them.** | `structlog` JSON with fields is searchable, correlatable, alertable; `print()` is none of those. Your logs are Track 02's detection input. |
| 6 | **The copilot ships the scale bug.** | `json.load()` + `print()` *works* on a 10-line sample and dies on the real feed. Catching that is the whole exercise. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) (streaming pipeline, row-vs-columnar, dissector dispatch) and the
> `polars`/`duckdb`/`structlog` docs.

---

## Warm-up — answer before you build (2 min)

1. Why does `json.load(open("eve.json"))` fail on a large EVE feed when a generator doesn't?
2. What can you do with `log.info("triaged", signature=sig, dest_ip=str(ip), verdict=v)` that you
   *cannot* do with `print(f"triaged {sig}")`?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/03-data-at-scale
make up      # build the lab container (Python + polars/duckdb/structlog + sift)
make shell   # work on sift; the real data/eve.json is mounted
make demo    # reference: streams eve.json (replayed ~200× → ~175k events), duckdb triage, structlog JSON
make down
```

The real `data/eve.json` is a committed, curated corpus (~875 genuine Suricata events from the STRRAT
capture); the demo **replays** it to ~175k newline-delimited events so streaming and columnar queries
genuinely earn their place. To reproduce it from source — or point at a busier PCAP for true
hundreds-of-thousands volume — run `make gen` on the host (it fetches + checksum-verifies the PCAP and
runs Suricata; see `PROVENANCE.md`). `make reset` tears the environment down clean.

> **Authorization note.** Everything runs locally against a public, pre-captured infection PCAP and its
> Suricata output — you are not attacking a live target. Only test systems you own or have explicit
> written permission to test.

---

## Build it — objective, then a signal (intermediate-plus: you drive the code)

### Step 1 — Feel the failure first (the copilot's default)

**Concept (30 sec):** Flight-card #6. Load the whole feed into a list — `json.load()` /
`read().splitlines()` — and watch memory climb (or OOM) as the demo replays to ~175k events. See it
break before you fix it, so the streaming win is *measured*, not asserted.

**Do:** run the in-memory approach over the replayed `eve.json` and record its peak RSS.

> **▸ On track if:** you have a number — the in-memory version's memory grows with the feed (and on a
> big enough replay, falls over).

### Step 2 — Stream the parse (and keep "parse, don't trust")

**Concept (30 sec):** Flight-card #2 + #3. A generator reads one line, validates it into Module 02's
EVE model, and `yield`s it — memory stays flat, and every line is still typed on the way through.

**Do:** rewrite `sift`'s ingest as a line-at-a-time generator that validates each line and dispatches
on `event_type`; quarantine unknown types instead of crashing.

> **▸ On track if:** `sift` streams the **full** `eve.json` in **bounded** memory — peak RSS is flat
> versus Step 1's growing number — and no malformed/unknown line takes the run down.

### Step 3 — Answer triage questions columnar

**Concept (30 sec):** Flight-card #4. Analytical questions belong in a columnar engine, not a Python
loop. `duckdb` reads the nested EVE JSON directly; `alert.signature` is a struct field access.

**Do:** with `duckdb` (SQL over the file) or `polars` (lazy frame), answer at least: top 20
`alert.signature` by count, the loudest-talker `dest_ip`, and per-hour `alert` volume from `timestamp`
— no hand-rolled `dict` counting.

> **▸ On track if:** a single columnar query returns a ranked table over real EVE fields (the STRRAT
> signatures surface at the top) — and you did **not** write a counting loop.

### Step 4 — Structure the logs

**Concept (30 sec):** Flight-card #5. `structlog` turns prose into queryable JSON events with fields.

**Do:** configure `structlog` for JSON output; replace every `print()` in `sift` with a structured
event over real EVE fields (`log.info("triaged", signature=..., dest_ip=..., verdict=...)`).

> **▸ On track if:** all of `sift`'s output is JSON events with fields (no bare `print`), and you can
> pipe them to `jq` and filter by `signature` or `verdict`.

### Step 5 — Prove it scales, side by side

**Concept (30 sec):** Flight-card #6. The claim is only real with the comparison in hand.

**Do:** run the streaming path over the full feed and put its bounded peak RSS next to Step 1's.

> **▸ On track if:** you have both numbers — streaming holds flat where the in-memory version balloons
> (numbers, not vibes).

---

## Prove the control (your finish line)

Commit the grown `sift` and confirm the stage holds end to end:

- [ ] `sift` **streams** `eve.json` — peak memory stays flat on the full replayed feed.
- [ ] At least one triage question over real EVE fields (e.g. top 20 `alert.signature`) is answered by a
  `polars`/`duckdb` query, **not** a Python loop.
- [ ] All of `sift`'s output goes through `structlog` as **JSON events with fields** (no bare `print`).
- [ ] You can show the in-memory approach ballooning where the streaming one holds — **with numbers.**
- [ ] Unknown/malformed lines are quarantined, not fatal (the "parse, don't trust" rail held).

---

## Recall check — close the doc, answer from memory (3 min)

1. Why does a generator keep memory flat where `json.load()` does not?
2. Give a triage question over EVE that's one line of `duckdb`/`polars` and twenty lines of hand-rolled Python.
3. Name two things structured JSON logs let you do that `print()` prose does not.

---

## Deliverables

The updated **`sift`** repo: the streaming-ingest module, the columnar triage query, the `structlog`
config, and a short note on the memory difference (numbers, not vibes). Do **not** commit the PCAP or a
regenerated `eve.json` — reference them and regenerate in the lab.

## Automate & own it

**Required.** Commit the streaming ingest, the columnar triage query, and the `structlog` config into
`sift`. In the commit/PR note, record what the copilot generated and the **scale bug you caught** — the
slurp (`json.load`), the `print`, or an unbounded aggregation. The bug is the point: the code *worked*
on a 10-line sample and would have died on the real feed. Reviewing that gap is the skill.

## Definition of done (`data-at-scale` ✅)

- [ ] `sift` streams the full `eve.json` in bounded memory, with the in-memory baseline measured beside it.
- [ ] A columnar triage query (top signatures / loudest talker / per-hour volume) is committed, no loop.
- [ ] Every output line is `structlog` JSON; unknown event types are quarantined, not fatal.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

The streaming + structured-log foundation is what **Module 04** enriches concurrently and **Module 09**
measures. Your `structlog` JSON is exactly the kind of telemetry **Track 02 (Defensive)** parses and
detects on — you're producing one side of a seam you'll consume from the other.

## Marketable proof

> "I build Python security tooling that streams a real Suricata `eve.json` with flat memory, runs triage
> queries (top signatures, top talkers, per-hour volume) in `duckdb`/`polars`, and emits `structlog` JSON
> a SIEM can ingest — and I catch the in-memory scale bugs an AI copilot ships."

## Stretch (optional)

- Write the triaged output as Parquet and query it back with `duckdb` — feel the columnar speedup vs
  reading the raw `eve.json`.
- Add a `--since` window to the triage query and bind a request-id into the `structlog` context so every
  log line for one run is correlatable.
- **Dissect `http`, then triage it columnar.** *Objective:* extend Module 02's growing typed union
  (which added `dns`) with an `HttpEvent` member for `event_type:"http"`, pinning `http.hostname`,
  `http.url`, and `http.status`; then answer a triage question over the new event type with a columnar
  query — e.g. top 20 `http.hostname` by request count, or the count of non-200 `http.status`.
  *Acceptance:* every `http` line validates into the union (no longer quarantined as an unknown type),
  and one `duckdb`/`polars` query returns a ranked `http.hostname` (or `http.status`) table over the real
  feed. This is the rung of the dissector thread for this module — the dissector earns its keep by feeding
  a columnar triage query, exactly this module's skill.
