# Lab 06 — One Core, Two Surfaces: a `typer` CLI and a `FastAPI` Service

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/06-cli-and-api/`: a container with `uv`, `typer`, `fastapi`, and
`uvicorn` installed, seeded with the `sift` core you built through M5 (the pydantic `Alert`/`Indicator`
models, the triage layer, and the async enricher) plus a few bundled sample alerts.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/06-cli-and-api
make up      # build the container with the M5 sift core preinstalled
make shell   # drop into the project
make demo    # runs the CLI and the API against the same alert and diffs the two results
make down    # stop when done
```

The lab **builds on the custom `sift` core** you've grown across the track because the lesson is the
*shared-core architecture* — you must be able to import the same functions from two adapters, which a
black-box image can't teach. It is reproducible at zero cost.

## Scenario

`sift` works, but it only runs one way: an analyst types a command. The SOC now wants it **as a service**
too — a SOAR playbook should be able to `POST` an alert and get the same triage verdict the analyst sees.
Your job is to add both surfaces *without* forking the logic. The trap is the obvious one: write a
`typer` CLI, then write a `FastAPI` app, and copy the triage code into both. You'll instead expose the
existing core through two thin adapters and prove they never disagree.

> Only test systems you own or have explicit written permission to test. Everything here runs locally in
> the lab container against bundled sample data.

## Do

1. [ ] **Write the spec first.** Spec the increment: "expose the existing `sift` core through a `typer`
   CLI and a `FastAPI` service; both import the same models and the same core function; zero duplicated
   business logic; the API validates request bodies against the `Alert` model." This is the contract you
   review the copilot against.
2. [ ] **Isolate the core.** Confirm the triage/enrich logic is importable as plain functions
   (`from sift.core import triage, enrich`) with *no* CLI or HTTP concerns mixed in. If M5 left any I/O or
   argument-parsing in those functions, lift it out now — the surfaces will own that.
3. [ ] **Build the `typer` adapter.** Add a `sift triage <alert.json>` command that reads the file,
   validates it into an `Alert` with `model_validate_json`, calls `triage`, and prints the verdict as
   JSON. Keep it to a handful of lines — parse, delegate, render.
4. [ ] **Build the `FastAPI` adapter.** Add a `POST /triage` endpoint whose body parameter is typed
   `alert: Alert` and whose return is typed as your `Verdict` model. Do **not** parse or validate by
   hand — let FastAPI do it against your model. Serve it with `uvicorn`.
5. [ ] **Prove the validation payoff.** `POST` a malformed alert (missing a required field, wrong type).
   Confirm you get a clean `422` with a precise error *before* your code runs — and that it's the *same*
   `Alert` model rejecting it that guards the CLI.
6. [ ] **Prove the two surfaces agree.** Run the same sample alert through the CLI and through the API and
   diff the two verdicts — they must be byte-for-byte identical, because it's one core function.
7. [ ] **Grep for duplication.** Search the adapters for any scoring/triage logic. The business logic must
   appear **exactly once** (in the core). An `if`-branch that scores an alert inside a command or endpoint
   is a bug — fix it by delegating.
8. [ ] **Automate & own it.** Commit the two adapters plus a small `make demo` (or script) that runs both
   surfaces against one alert and asserts the results match — a regression guard against future
   divergence. In the PR, note where the copilot tried to duplicate the logic and how you collapsed it.

## Success criteria — you're done when
- [ ] `sift triage <alert.json>` and `POST /triage` produce **identical** verdicts from the same input.
- [ ] The triage/scoring business logic appears **exactly once** in the repo; both adapters import it.
- [ ] A malformed request to `POST /triage` returns a `422` validated against the `Alert` model, not a crash.
- [ ] Both adapters are thin — each command/endpoint parses input, delegates to the core, and renders out.
- [ ] Your `make demo` (or equivalent) runs both surfaces and **asserts** they agree.

## Deliverables
The two adapter modules (`cli.py` and `api.py`, or your project's equivalent), the updated `sift` package
exposing the shared core, and the demo/regression check that asserts CLI and API agreement — committed to
your `sift` repo. Do **not** commit any real API keys, `.env`, or live TI responses; the enricher's
secrets handling stays as configured in M2/M4.

## AI acceleration
Prompt the copilot with "add a CLI and a REST API to `sift`" and inspect what it generates: it will very
likely scaffold `typer` and `FastAPI` in separate passes and re-implement the triage logic inside each.
Review by *tracing the business logic* — it must live once, in the core, imported by both. The high-value
catch is the duplicated (and subtly divergent) scoring branch inside an endpoint or command. Collapse it
to a delegate call; that collapse is the whole lesson.

## Connects forward
This "one core, N surfaces" pattern is exactly what Module 07 extends: the MCP server becomes a *third*
surface over the same core, so an LLM can call `sift`'s enrich/triage as tools. Because the logic already
lives in one typed place, adding MCP is another thin adapter — not a third re-implementation.

## Marketable proof
> "I expose one validated Python core through multiple surfaces — a `typer` CLI and a `FastAPI` service
> that share the same pydantic models with zero duplicated logic — so the analyst's tool and the SOAR
> pipeline's API can never drift apart, and every HTTP request is validated against the same models."

## Stretch (optional)
- Add FastAPI's auto-generated OpenAPI docs to the deliverable and generate a typed client from them —
  showing the API is consumable by other services without hand-written glue.
- Make the CLI call the *running API* over HTTP (instead of importing the core directly) behind a flag,
  and confirm the verdict is still identical — a preview of surface-vs-transport separation.
