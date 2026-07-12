# Lab 04 — A Bounded, Backoff-Aware Async Enricher

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/04-async-concurrency/`: your `sift` project from Module 03, plus a
small **mock threat-intel API** container that enforces a real rate limit (returns `429` with a
`Retry-After` header past its quota) so you can prove your bound and backoff work *without* burning a real
API key. A bundled indicator list (a few thousand entries) is included.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/04-async-concurrency
make up      # start the sift toolchain + the rate-limited mock TI API
make shell   # drop into the project
make demo    # runs the async enricher against the mock API and prints the concurrency/backoff report
make down    # stop when done
```

The lab **runs against a shipped mock API** — a small custom target — because the lesson is *rate-limit
behavior under bounded concurrency*, and a mock that deterministically returns `429` is the only way to
make the herd and the backoff *legible and reproducible* at zero cost.

## Scenario

`sift` can now parse a large feed into typed indicators. The next job is enrichment: for each indicator,
ask a threat-intel API "is this known-bad, and what's the reputation?" The naive version — a sync loop, or
`asyncio.gather` over everything — either takes an hour or gets your key banned in seconds against the
mock's rate limit. You'll build the enricher that's both *fast* and *polite*.

> Only test systems you own or have explicit written permission to test. Everything here runs locally
> against the bundled mock API — never point this enricher at a real threat-intel API until you've
> confirmed your bound respects its published rate limit.

## Do

1. [ ] **Feel the pain first.** Run the shipped **sync** enricher (`httpx.get` in a `for` loop) over the
   indicator list and time it. Record the wall-clock — this is the toil you're eliminating.
2. [ ] **Write the spec.** Spec the async enricher: reuse one `httpx.AsyncClient`; concurrency bounded to
   *K* (default from the mock's documented rate limit); on `429`, honor `Retry-After` then exponential
   backoff *with jitter*; every indicator returns a typed result (`Ok`/`Err`); the batch always completes.
3. [ ] **Watch the copilot build the herd.** Ask your copilot to "enrich all indicators concurrently."
   Confirm it emits `asyncio.gather` with **no** semaphore and **no** `429` handling. Run it against the
   mock and watch it get rate-limited (or banned). This is the failure-class — see it fail on purpose.
4. [ ] **Bound the concurrency.** Add an `asyncio.Semaphore(K)` so at most *K* requests are in flight;
   each enrich coroutine does `async with sem:` around its `await client.get(...)`. Instrument a
   max-in-flight counter and prove it never exceeds *K*.
5. [ ] **Handle the `429` respectfully.** On `429`, read `Retry-After` and `await asyncio.sleep(...)` for
   it (**not** `time.sleep`, which blocks the loop); if absent, exponential backoff with jitter, capped at
   a max retry budget. Use `tenacity` or hand-roll it — either way, prove the backoff *fires* under the
   mock's rate limit and the batch still finishes.
6. [ ] **Survive partial failure.** Make every task return a result object, not raise. Force a subset to
   fail (bad indicators / injected timeouts) and prove the *other* results all come back — no
   `gather`-cancels-the-batch. Log the failures as structured `sift` events (from Module 03).
7. [ ] **Prove it's faster *and* polite.** Re-time the bounded async enricher vs. step 1's sync loop, and
   show zero `429`-induced failures in the final run. Report: wall-clock, max concurrency observed, retries
   fired, indicators failed.
8. [ ] **Automate & own it.** Commit the enricher as `sift enrich`, wired into the pipeline behind the
   Module 02 pydantic models. In the PR, note the copilot's herd version, the bound and backoff you added,
   and the one blocking `time.sleep` (or unbounded `gather`) you had to fix.

## Success criteria — you're done when
- [ ] The async enricher is measurably faster than the sync loop over the full indicator list.
- [ ] Observed concurrency **never exceeds *K*** — you have the counter/log to prove it.
- [ ] Under the mock's rate limit, the run shows the backoff **firing** and finishes with **zero** unhandled `429`s.
- [ ] A forced subset of failures does **not** sink the batch — every indicator returns `Ok` or `Err`.
- [ ] No `time.sleep` inside a coroutine; one reused `httpx.AsyncClient`; the spec is satisfied by the implementation.

## Deliverables
The `sift enrich` module: the bounded async enricher (`httpx.AsyncClient` + `asyncio.Semaphore` + backoff),
the typed per-indicator result model, the enrichment spec, and the timing/concurrency report proving the
bound and backoff hold. Commit all of it. Do **not** commit any real TI API key — load it via
`pydantic-settings` (Module 02); the lab uses the mock.

## AI acceleration
Delegate the `async`/`await` scaffolding to the copilot, then review for exactly two omissions: the
concurrency **bound** and the `429` **backoff**. The high-value catches: an `asyncio.gather` with no
semaphore (the herd), a `time.sleep` inside a coroutine (blocks the whole loop), a `gather` without
`return_exceptions` (one failure cancels the batch), and a fresh `AsyncClient` per call (throws away the
pool). Ask the model "what's the max concurrent requests here?" — if it can't answer with a number, the
bound isn't there.

## Connects forward
The reused-client, bounded-concurrency muscle returns in Module 06 when `sift` becomes a `FastAPI` service
(async endpoints, shared client lifespan) and in Module 07's MCP server, whose tools call this same
enricher. Rate-limit-respect and backoff reappear anywhere `sift` talks to an external API — including the
LLM in Module 07, which has its *own* `429`s.

## Marketable proof
> "I build async enrichment pipelines in Python that call threat-intel APIs with bounded concurrency,
> `Retry-After`-honoring backoff, and per-item partial-failure handling — fast enough to scale, polite
> enough not to get the key banned."

## Stretch (optional)
- Replace the semaphore with an `anyio` task group + capacity limiter and compare the ergonomics of
  structured concurrency (cancellation propagates cleanly) against raw `asyncio`.
- Add a token-bucket rate limiter (requests-per-second, not just in-flight count) so you respect a
  *per-second* quota even when individual calls are fast — the case a semaphore alone doesn't cover.
