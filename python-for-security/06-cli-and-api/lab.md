# Lab 06 — One Core, Two Surfaces: a `typer` CLI and a `FastAPI` Service

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/06-cli-and-api` (a container with
> `uv`, `typer`, `fastapi`, and `uvicorn`, seeded with the `sift` core you grew through M5 — the pydantic
> EVE `AlertEvent` model, the triage layer, the async enricher — plus a few bundled `eve.json` records,
> clean and malformed). Objective: **add two thin surfaces to the *same* `sift` — a `typer` CLI an analyst
> runs and a `FastAPI` service a pipeline calls — sharing one core with zero duplicated logic.** Target:
> **~2–3 hrs.**
> *Intermediate-plus: the steps state objectives; you derive the `typer`/`FastAPI` code (with the copilot).*

*[← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **One core, two surfaces.** | The pydantic models + core functions *are* `sift`; CLI and API are adapters over them. |
| 2 | **A surface is thin.** | Get input into a model, call a core function, render out — no business logic in the adapter. |
| 3 | **`typer` and `FastAPI` share a shape.** | Both derive their interface (args, request schema) from your type annotations. |
| 4 | **The API edge is a second untrusted edge.** | Typing a body `event: AlertEvent` reuses the M2 model — a bad EVE line → `422`, not a crash. |
| 5 | **Zero duplicated logic is the bar.** | The scoring/triage code appears **exactly once** in the repo; both surfaces `import` it. |
| 6 | **Both surfaces agree because they share the core.** | `sift triage` on the CLI and `POST /triage` on the API return byte-identical results. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea), the Typer and FastAPI request-body tutorials, and the Cosmic
> Python "thin adapters over a stable core" chapter.

---

## Warm-up — answer before you build (2 min)

1. If a teammate adds a new severity rule, which files must change so the CLI and the API stay in agreement?
2. When a `POST /triage` arrives with `alert.severity` outside Suricata's `1..3` range, *what* rejects it,
   *what* does the client get back, and why did you get that for free?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/06-cli-and-api
make up      # build the container with the M5 sift core preinstalled
make shell   # drop into the project
make demo    # runs the CLI and the API against the same eve.json alert and diffs the two results
make down    # stop when done  (make reset to also drop the image + volumes)
```

> **Authorization note.** Everything runs locally in the lab container against bundled sample data —
> only test systems you own or have explicit written permission to test.

The lab **builds on the custom `sift` core** you've grown across the track: the whole lesson is the
*shared-core architecture*, which means importing the same functions from two adapters — something a
black-box image can't teach. It is reproducible at zero cost.

---

## Build it — objective, then a signal (intermediate-plus: you drive the code)

### Step 1 — Write the spec first

**Concept (30 sec):** Flight-card #1 + #5. The spec is the contract you review the copilot against —
here it names the *architecture*, not the feature.

**Do:** spec the increment — *expose the existing `sift` core through a `typer` CLI and a `FastAPI`
service; both import the same models and the same core function; zero duplicated business logic; the API
validates request bodies against the EVE `AlertEvent` model.*

> **▸ On track if:** the spec says "two thin adapters over the existing core," not "add a CLI and add an
> API" — it forbids re-implementation up front.

### Step 2 — Isolate the core

**Concept (30 sec):** Flight-card #2. A surface can only stay thin if the logic is already a clean,
import-able function.

**Do:** confirm the triage/enrich logic is reachable as plain functions (`from sift.core import triage,
enrich`) with **no** CLI or HTTP concerns mixed in; if M5 left any I/O or arg-parsing inside them, lift it
out — the surfaces will own that.

> **▸ On track if:** `triage(event) -> TriageResult` imports and runs from a bare Python REPL, with no
> `typer`/`fastapi`/`sys.argv` anywhere in its call path.

### Step 3 — Build the `typer` adapter

**Concept (30 sec):** Flight-card #3. A type-annotated function *becomes* a CLI — parameter types drive
parsing and `--help`.

**Do:** add a `sift triage <eve.json>` command that reads a real EVE record, validates it into an
`AlertEvent` with `model_validate_json`, calls `triage`, and prints the result as JSON. Keep it to a
handful of lines: parse, delegate, render.

> **▸ On track if:** the command is a thin shell — it validates into the model, delegates to the **same**
> `triage` you isolated in Step 2, and contains no scoring branch of its own.

### Step 4 — Build the `FastAPI` adapter

**Concept (30 sec):** Flight-card #3 + #4. The *same* typed-function-to-interface move, now over HTTP —
and the request body is a second untrusted edge.

**Do:** add a `POST /triage` endpoint whose body parameter is typed `event: AlertEvent` and whose return
is typed as your `TriageResult` model; do **not** parse or validate by hand — let FastAPI do it against
your model. Serve it with `uvicorn`.

> **▸ On track if:** the same `sift` core answers both `sift triage` on the CLI and `POST /triage` on the
> API, and the endpoint delegates to the identical `triage` function — no logic re-typed inside it.

### Step 5 — Prove the validation payoff (the second edge holds)

**Concept (30 sec):** Flight-card #4. Parse-don't-trust was never about one edge.

**Do:** `POST` a malformed EVE line — a truncated/non-JSON body, an `alert.severity` outside `1..3`, or a
non-`alert` `event_type` your model doesn't accept — and watch the response.

> **▸ On track if:** you get a clean `422` with a precise error *before* your code runs, and it's the
> **same `AlertEvent` model** rejecting it that guards the CLI — reject an invalid request through the
> shared model, on both surfaces.

### Step 6 — Grep for duplication, then collapse it

**Concept (30 sec):** Flight-card #5. This is the whole review move — trace the business logic.

**Do:** search both adapters for any scoring/triage decision (an `if severity > ...` inside an
`@app.command()` or `@api.post()`). If the copilot duplicated it, delete the copy and delegate to the core.

> **▸ On track if:** the scoring/triage logic appears **exactly once** in the repo (in the core), and both
> adapters reach it only through `import`.

---

## Prove the control — your finish line

Run the same EVE `alert` record through **both** surfaces from **one** core and show they can't disagree:

- [ ] `sift triage <eve.json>` and `POST /triage` return **byte-for-byte identical** results from the same
      EVE record (`make demo` diffs them and asserts equality).
- [ ] A malformed EVE line `POST`ed to `/triage` returns a `422` validated against `AlertEvent` — the same
      model that guards the CLI — not a crash.
- [ ] The triage/scoring logic appears **exactly once** in the repo; both adapters import it.
- [ ] Both adapters are thin: each parses input into a model, delegates to the core, and renders out.

---

## Recall check — close the doc, answer from memory (3 min)

1. Name the three jobs of a "thin" surface, in order.
2. When `POST /triage` gets a bad EVE body, *what* validates it and *what* does the caller receive?
3. Why can the CLI and the API never drift apart in this design — what single fact guarantees it?

---

## Deliverables

The two adapter modules (`cli.py` and `api.py`, or your project's equivalent), the updated `sift` package
exposing the shared core, the migration/increment **spec**, and the demo/regression check that asserts CLI
and API agreement — committed to your `sift` repo. Do **not** commit any real API keys, `.env`, or live TI
responses; the enricher's secrets handling stays as configured in M2/M4.

## Automate & own it

**Required.** Commit the two adapters plus a small `make demo` (or script) that runs **both** surfaces
against one alert and **asserts** the results match — a regression guard against future divergence. In the
commit/PR, note where the copilot tried to duplicate the triage logic (it will scaffold `typer` and
`FastAPI` in separate passes and re-implement scoring inside each) and how you collapsed it to a single
delegate call. That collapse is the whole lesson.

## Definition of done (`cli-and-api` ✅)

- [ ] Both surfaces are live over the **same** `sift` core, with zero duplicated business logic.
- [ ] `make demo` proves the CLI and the API return identical results, and a bad EVE line `422`s on the API.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

This "one core, N surfaces" pattern is exactly what **Module 07** extends: the MCP server becomes a
*third* surface over the same core, so an LLM can call `sift`'s enrich/triage as tools. Because the logic
already lives in one typed place, adding MCP is another thin adapter — not a third re-implementation.

## Marketable proof

> "I expose one validated Python core through multiple surfaces — a `typer` CLI and a `FastAPI` service
> that share the same pydantic models with zero duplicated logic — so the analyst's tool and the SOAR
> pipeline's API can never drift apart, and every HTTP request is validated against the same models."

## Stretch (optional)

- **Dissector rung — one filter, both surfaces.** By now the discriminated union has grown well past
  `alert`: M02 added `dns`, M03 `http`, M04 `tls`, M05 `flow`/`fileinfo`. Expose an **`event_type` filter
  as a *shared* concept across both adapters** — a `--event-type` option on the `typer` CLI and an
  `?event_type=` query parameter on the API — so a caller streams a mixed `eve.json` and triages only the
  chosen dissected type (e.g. just `dns`, or just `http`). Prove the two-surfaces-one-core discipline
  holds: the filter predicate lives **once** in the core (a function over the union), and both surfaces
  merely pass the selected type into it — the CLI flag and the query param must produce **byte-for-byte
  identical** filtered output, and an unrecognised `event_type` is rejected the same way on both surfaces.
  *Acceptance:* `sift triage mixed.eve.json --event-type dns` and `POST /triage?event_type=dns` return the
  same records, and neither surface re-implements the filter.
- Add FastAPI's auto-generated OpenAPI docs to the deliverable and generate a typed client from them —
  showing the API is consumable by other services without hand-written glue.
- Make the CLI call the *running API* over HTTP (instead of importing the core directly) behind a flag,
  and confirm the verdict is still identical — a preview of surface-vs-transport separation.
