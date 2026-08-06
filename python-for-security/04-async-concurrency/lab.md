# Lab 04 — A Bounded, Backoff-Aware Async Enricher

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/04-async-concurrency` (your `sift`
> project from Module 03 + a small **mock threat-intel API** that enforces a real rate limit — returns
> `429` with `Retry-After` past its quota). Objective: **add an async enrichment stage to the *same*
> `sift`** — pull the unique `src_ip` / `dest_ip` off your validated `AlertEvent`s and query the TI API
> for each, with **bounded** concurrency, **`Retry-After`-honoring backoff**, and **per-indicator
> partial-failure** handling. Target: **~2–3 hrs.**
> *Intermediate-plus: the steps state objectives; you derive the `asyncio`/`httpx`/backoff code (with the copilot).*

*[← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This lab grows `sift`, it does not start a new tool.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Async is for waiting, not computing.** | Enrichment is I/O-bound — hundreds of ms *waiting on the network*; async overlaps the waits and collapses wall-clock. |
| 2 | **Unbounded `gather` is the herd; `Semaphore(K)` is the fix.** | *K* comes from the API's published rate limit, not your CPU — cap in-flight requests or get `429`'d / banned. |
| 3 | **A `429` is an instruction — obey it.** | Honor `Retry-After` with `await asyncio.sleep` (never `time.sleep` — it blocks the loop); else exponential backoff **with jitter**. |
| 4 | **Design for partial failure.** | Every indicator returns `Ok`/`Err`; `asyncio.gather` without `return_exceptions` **cancels the whole batch** on the first raise. |
| 5 | **One reused `httpx.AsyncClient`.** | A single connection-pooled client for the batch — not `requests`, not a fresh client per call. |
| 6 | **Ephemeral async vs. durable queue.** | In-process `asyncio` loses in-flight work on a crash; `huey` makes each enrich a persisted, retryable job that survives a restart. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) (semaphore, backoff, partial failure, task-queue distinction) and
> the HTTPX / `tenacity` / `huey` primary sources.

---

## Warm-up — answer before you build (2 min)

1. What is the maximum number of simultaneous requests `await asyncio.gather(*[enrich(i) for i in
   indicators])` makes — and why is that the **bug**, not the feature?
2. On a `429` with `Retry-After: 30`, what does a respectful client do — and why is `time.sleep(30)`
   inside a coroutine wrong even though the *duration* is right?

---

## Setup

This is a **reference lab** — a one-command environment: your `sift` project plus a **mock TI API**
container that returns `429` with a `Retry-After` header past its quota, so you can prove your bound and
backoff work *without* burning a real API key. The indicators aren't invented — you derive them from the
unique `src_ip` / `dest_ip` off the validated `AlertEvent`s in `eve.json`. The bundled capture yields a
handful of unique IPs — enough for the bound and backoff to bite; regenerate `eve.json` from a larger
PCAP when you want thousands.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/04-async-concurrency
make up      # start the sift toolchain + the rate-limited mock TI API
make shell   # drop into the project
make demo    # runs the async enricher against the mock API and prints the concurrency/backoff report
make down    # stop when done
```

> **Authorization note.** Everything runs locally against the bundled mock API — only test systems you
> own or have written permission to test. Never point this enricher at a real threat-intel API until
> you've confirmed your bound respects its published rate limit.

---

## Build it — objective, then a signal (intermediate-plus: you drive the code)

### Step 1 — Derive the indicators, then feel the pain

**Concept (30 sec):** Flight-card #1. The sync loop is *safe* but serializes every network wait — that's
the toil you're eliminating. Measure it before you fix it.

**Do:** extract the unique `src_ip` / `dest_ip` from your parsed `AlertEvent`s (dedup — the same IP
recurs across alerts). Run the shipped **sync** enricher (`httpx.get` in a `for` loop) over that IP set
and time it.

> **▸ On track if:** you have a deduped indicator list off the `AlertEvent`s **and** a recorded sync
> wall-clock to beat.

### Step 2 — Spec it, then watch the copilot build the herd

**Concept (30 sec):** Flight-card #2 + #4. Write the contract, then make the failure-class visible on
purpose before you fix it.

**Do:** spec the async enricher (reuse one `httpx.AsyncClient`; bound to *K*; honor `Retry-After` then
backoff with jitter; every indicator returns `Ok`/`Err`; batch always completes). Then ask your copilot
to "enrich all indicators concurrently" and run *its* version against the mock.

> **▸ On track if:** the copilot's draft emits `asyncio.gather` with **no** semaphore and **no** `429`
> handling — and you watched it get rate-limited against the mock. You've seen the herd fail on purpose.

### Step 3 — Bound the concurrency

**Concept (30 sec):** Flight-card #2. At most *K* requests in flight, ever. *K* comes from the mock's
documented rate limit.

**Do:** add an `asyncio.Semaphore(K)` — each enrich coroutine does `async with sem:` around its
`await client.get(...)`. Instrument a max-in-flight counter.

> **▸ On track if:** `sift` enriches the indicator list concurrently and the observed max-in-flight
> **never exceeds *K*** — you have the counter/log to prove it, and the shared results are updated
> without a race.

### Step 4 — Handle the `429` respectfully

**Concept (30 sec):** Flight-card #3. The server told you to slow down; obey with the loop-friendly sleep.

**Do:** on `429`, read `Retry-After` and `await asyncio.sleep(...)` for it (**not** `time.sleep`); if
absent, exponential backoff with jitter, capped at a max retry budget. Hand-roll it or use `tenacity`.

> **▸ On track if:** under the mock's rate limit the backoff **fires** (you can see the retries in the
> log), no `time.sleep` sits inside a coroutine, and the batch still finishes with **zero** unhandled
> `429`s.

### Step 5 — Survive partial failure

**Concept (30 sec):** Flight-card #4. One bad call must not sink 499 good ones.

**Do:** make every task return a result object, not raise. Force a subset to fail (bad indicators /
injected timeouts) and log the failures as structured `sift` events (from Module 03).

> **▸ On track if:** a forced subset of failures does **not** cancel the batch — every indicator comes
> back `Ok` or `Err`, and the failures are recorded as structured events.

### Step 6 — Prove it's faster *and* polite

**Concept (30 sec):** Flight-card #1–#3 together. Fast alone is the herd; the win is fast *and* bounded.

**Do:** re-time the bounded async enricher vs. Step 1's sync loop. Emit a report: wall-clock, max
concurrency observed, retries fired, indicators failed.

> **▸ On track if:** the bounded async run is **measurably faster** than the sync loop **and** shows
> zero `429`-induced failures.

---

## Prove the control (your finish line)

Wire the enricher into `sift` as `sift enrich` and confirm the control holds — you're done when:

- [ ] `sift enrich` is measurably **faster** than the sync loop over the full indicator list.
- [ ] Observed concurrency **never exceeds *K*** — the counter/log proves it, and no race corrupts the shared results.
- [ ] Under the mock's rate limit the run shows the backoff **firing** and finishes with **zero** unhandled `429`s.
- [ ] A forced subset of failures does **not** sink the batch — every indicator returns `Ok` or `Err`.
- [ ] No `time.sleep` inside a coroutine; **one reused** `httpx.AsyncClient`; the implementation satisfies the spec.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why does async win for enrichment but *not* for a CPU-bound hashing loop?
2. Where does the correct *K* come from — and why can't you fix the herd by "just setting a high limit"?
3. `sift` dies after enriching 6,000 of 10,000 indicators. With the in-process async batch, what happens
   to the other 4,000 — and how does moving enrichment onto a `huey` task queue change the answer?

---

## Deliverables

The `sift enrich` module: the bounded async enricher (`httpx.AsyncClient` + `asyncio.Semaphore` +
backoff), the typed per-indicator result model, the enrichment spec, and the timing/concurrency report
proving the bound and backoff hold. Commit all of it. **Do not** commit any real TI API key — load it via
`pydantic-settings` (Module 02); the lab uses the mock. Lab *artifacts* (raw API responses, logs) stay
out of commits.

## Automate & own it

**Required.** Commit the enricher as `sift enrich`, wired into the pipeline behind the Module 02 pydantic
models. In the PR, note the copilot's herd version, the **bound** and **backoff** you added, and the one
blocking `time.sleep` (or unbounded `gather`) you had to fix. Ask the model "what's the max concurrent
requests here?" — if it can't answer with a *number*, the bound isn't there. Reviewing the AI's
concurrency is where this class of risk lives.

## Definition of done (`async-concurrency` ✅)

- [ ] `sift enrich` is committed: bounded async enricher + typed result model + spec + timing/concurrency report.
- [ ] The bound holds (max in-flight ≤ *K*), the backoff fires under the mock's `429`, and partial failure never sinks the batch.
- [ ] You can explain all six flight-card facts cold — including async-ephemeral vs. task-queue-durable.

## Connects forward

The reused-client, bounded-concurrency muscle returns in **Module 06** when `sift` becomes a `FastAPI`
service (async endpoints, shared client lifespan) and in **Module 07**'s MCP server, whose tools call
this same enricher. Rate-limit-respect and backoff reappear anywhere `sift` talks to an external API —
including the LLM in Module 07, which has its *own* `429`s.

## Marketable proof

> "I build async enrichment pipelines in Python that call threat-intel APIs with bounded concurrency,
> `Retry-After`-honoring backoff, and per-item partial-failure handling — fast enough to scale, polite
> enough not to get the key banned."

## Stretch (optional)

- Replace the semaphore with an `anyio` task group + capacity limiter and compare the ergonomics of
  structured concurrency (cancellation propagates cleanly) against raw `asyncio`.
- Add a token-bucket rate limiter (requests-per-second, not just in-flight count) so you respect a
  *per-second* quota even when individual calls are fast — the case a semaphore alone doesn't cover.
- **Dissect `tls` and enrich on JA3/SNI — concurrently.** Grow the discriminated union one more member:
  add a `TlsEvent` for `event_type: "tls"` (pin `tls.sni` and `tls.ja3.hash`, `extra="ignore"` the rest),
  extending the union you started in M02 (`dns`) and grew in M03 (`http`); unknown event types still
  quarantine rather than crash. Then run the *same* bounded async enricher over these new indicators —
  look up each unique `tls.ja3.hash` (a client fingerprint that often outs a malware family regardless of
  IP) and each `tls.sni` against the mock TI API, concurrently and under the same semaphore + backoff.
  **Acceptance:** every `tls` line validates into a `TlsEvent` or is quarantined; the JA3/SNI enrichment
  reuses your bound (max in-flight never exceeds *K*) and honors `429` — no second, unbounded code path.
- **Make it durable — move enrichment onto a `huey` task queue.** `pip install huey`, wrap `enrich` in
  `@huey.task(retries=3)` on a `SqliteHuey` (no extra service to run), start the `huey_consumer` as a
  separate process, and enqueue the indicator list. **Kill the consumer mid-run, then restart it** — prove
  the queued jobs resume and nothing is lost. Then write down the trade-off you just felt: in-process async
  (fast, ephemeral, one batch) vs. a task queue (durable, retryable, continuous), and *when the queue is
  worth its weight*. **Forward-pointer:** when a durable job grows into a long-running, multi-step
  *workflow* (enrich → approve → contain → ticket) that must survive restarts across every step, you
  graduate to durable execution (**Temporal**) — that's SOAR-as-code in the **Automation track**, not here.
