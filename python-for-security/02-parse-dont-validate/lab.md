# Lab 02 — A Typed Input Boundary for `sift`

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/02-parse-dont-validate/`:

- **`sift_starter/`** — where `sift` stands after the copilot "helped": a working feed-triage draft
  (`triage.py`) that reads **Suricata EVE JSON** lines into dicts and trusts them — `.get()` defaults,
  `isinstance` patch-ups, shape-assuming indexing into `event["alert"]`, and an API key read straight from
  the environment. Fold it into your `sift` project from Module 01 (or work on it in place).
- **`data/eve.json`** — the curated EVE seed: clean `alert` events plus the malformed lines (a truncated
  non-JSON line, a record missing `dest_ip`, an `alert.severity` of `5` outside Suricata's `1..3`, an
  unhandled `event_type`, and a `signature_id` carrying a string where an `int` is required).
- **`sift_reference/`** — a finished boundary (`models.py`/`settings.py`). Build your own first; peek after.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/02-parse-dont-validate
make up      # build the lab container (python + pydantic/pydantic-settings)
make shell   # drop into the lab
make demo    # the contrast: the starter trusts garbage or dies; the boundary rejects every bad record
make down    # stop when done
```

The lab builds on the **custom `sift` target** you started in Module 01 — you edit the source to add the
boundary, which a black-box image can't teach. It is reproducible at zero cost.

## Scenario

`sift` currently reads the `eve.json` feed straight into dicts and reaches into them with `.get()` and
`if`-checks — the exact shape the copilot handed you (`sift_starter/triage.py`). It works on the clean
sample and falls apart on the real one: a truncated non-JSON line crashes the loader, a record missing
`dest_ip` is enriched against `None` and scored anyway, an `alert.severity` of `5` sails through Suricata's
`1..3` range unchecked, and a `dns` or `stats` line the code never expected gets treated as if it had an
`alert` object — `KeyError` three calls deep. Run `make demo` to watch all of that happen. You're going to
add a **typed boundary** — `EveBase` / `AlertDetails` / `AlertEvent` pydantic models — so each EVE line
becomes a validated domain object or gets rejected at the door, pinning the fields you consume while
ignoring the rest of the envelope, and move `sift`'s API key out of the code into `pydantic-settings`.

> Only test systems you own or have explicit written permission to test. Everything here runs locally in
> the lab container against bundled sample data.

## Do

1. [ ] **Find the trust.** Grep `sift_starter/triage.py` for `.get(`, `[` indexing, and `isinstance` on
   the raw feed — inventory every place it assumes an untrusted EVE line's shape (there are half a dozen,
   spread across `normalize`/`enrich`/`score`/`triage`, including the `event["alert"]["signature"]`
   reach). This is the `.get()`-soup you're replacing.
2. [ ] **Write the spec first.** Per the track's spec-driven workflow, spec the boundary: the fields you
   **pin and constrain** (`timestamp` → `datetime`, `src_ip`/`dest_ip` → `IPvAnyAddress`, the nested
   `alert.signature_id` → `int`, `alert.severity` → `Field(ge=1, le=3)`), which fields are *required*
   versus *legitimately optional* (some events omit `dest_ip` or `flow_id`), the decision to
   `extra="ignore"` the rest of the EVE envelope rather than `extra="forbid"` a real feed, the
   **reject-policy** (halt / quarantine / skip-and-log — pick one and justify it), and the acceptance
   checks (valid `alert` line → typed object; each malformed fixture → rejected).
3. [ ] **Model the domain.** Implement `EveBase`, `AlertDetails`, and `AlertEvent` as pydantic v2
   `BaseModel`s over the real EVE fields. Make them real types, not stringly-typed placeholders, and set
   the record-level policy to ignore-and-pin, not forbid — the constraint *is* the check:

   ```python
   from datetime import datetime
   from typing import Literal
   from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

   class EveBase(BaseModel):
       model_config = ConfigDict(extra="ignore")  # EVE has many envelope fields — ignore the rest
       timestamp: datetime
       src_ip: IPvAnyAddress | None = None
       dest_ip: IPvAnyAddress | None = None       # some events legitimately omit it — optional, not absent-crash
       proto: str | None = None

   class AlertDetails(BaseModel):
       model_config = ConfigDict(extra="ignore")
       signature: str
       signature_id: int                          # a string here is rejected, not fed downstream
       severity: int = Field(ge=1, le=3)          # Suricata severity is 1..3; 5 is rejected

   class AlertEvent(EveBase):
       event_type: Literal["alert"]               # the discriminant; other types have no member yet
       alert: AlertDetails
   ```

4. [ ] **Parse at the boundary.** Replace the ingest with a single `AlertEvent.model_validate(raw)` per
   line (after `json.loads`). Delete the downstream `.get()`/`isinstance` guards — the type now carries the
   invariant, so prove `pyright` is happy treating each record as an `AlertEvent`, not a dict.
5. [ ] **Decide what "reject" does.** Wrap the loader so a truncated / non-JSON line raises
   `json.JSONDecodeError` and a schema violation raises `ValidationError`, and catch *both* at the ingest
   loop to apply your spec's policy: skip-and-log with the offending line + `err.errors()` to a quarantine
   file (recommended for a triage tool), so one poisoned event doesn't halt the run *or* pass silently.
6. [ ] **Prove the boundary holds.** Run `sift` over `data/eve.json`: the valid `alert` lines become
   `AlertEvent` objects, and each malformed fixture is rejected with a precise reason — the truncated line,
   the missing `dest_ip` where downstream assumed it, the out-of-range `alert.severity`, the wrong-type
   `signature_id`, and the unhandled `event_type` (no union member → quarantined). Show the model now
   refuses a line the copilot's original `.get()` code trusted.
7. [ ] **Move secrets to `pydantic-settings`.** The starter's `enrich()` does
   `os.environ.get("SIFT_VT_API_KEY", "")` and silently carries on when the key is missing. Replace it
   with a `BaseSettings` object (`SecretStr` for the key, loaded from env / `.env`) so a missing key fails
   loudly at startup and the secret never lives in source or logs.
8. [ ] **Automate & own it.** Commit the increment — `sift` with a typed EVE input boundary and
   `pydantic-settings` — updating the spec and CI. In the commit/PR, note what the copilot generated, and
   the one thing it defaulted to that you had to fix: an unconstrained type it *annotated* but didn't
   *validate*, or an `extra="forbid"` that would have rejected every real EVE line.

## Success criteria — you're done when
- [ ] Every EVE line passes through **one** `AlertEvent.model_validate` boundary; downstream code receives typed `AlertEvent`s, not dicts (`pyright` confirms it).
- [ ] Fields carry **real constraints** — the missing `dest_ip`, the out-of-range `alert.severity` (5), the wrong-type `signature_id`, and the truncated non-JSON line are each rejected, not a downstream crash or a silent default.
- [ ] The record-level policy is `extra="ignore"` (a real EVE line with envelope fields still parses), and strictness comes from the **pinned/constrained** fields — you did not `extra="forbid"` the whole record.
- [ ] Your **reject-policy** is implemented and demonstrated: malformed lines are handled deliberately (quarantined/logged), valid ones flow through; the unhandled `event_type` is quarantined, not fatal.
- [ ] The API key loads via `pydantic-settings`; a missing key fails at startup, and no secret appears in source or logs.
- [ ] The spec is updated and the CI gate (ruff/pyright + the parse tests) is green.

## Deliverables
The updated `sift` repository: the `models.py` (`EveBase`/`AlertDetails`/`AlertEvent`) boundary, the
`pydantic-settings` config, the ingest loop with its reject-policy, the parse/reject tests, and the
updated spec. Commit all of it. Do **not** commit the real API key or any populated `.env` — only a
committed `.env.example`.

## AI acceleration
Have the copilot draft the models, the ingest refactor, and the adversarial fixtures from your spec — then
review the draft against it. The three high-value catches are the copilot's habit of *annotating without
constraining* (`dest_ip: str` where you specified an IP that must parse; a bare `severity: int` where
`1..3` is the rule), *defaulting instead of rejecting* (`.get("severity", 1)` sneaking back in as a "safe"
fallback), and *over-sealing the record* (`extra="forbid"` that rejects every genuine EVE line instead of
`extra="ignore"` plus pinned fields). Make the model generate the malformed inputs it thinks its own code
handles, then run them and watch which ones it actually lets through — that gap is the review.

## Connects forward
This boundary is the input edge of the track's *parse, don't trust* through-line, and it defines the EVE
data model every later module reuses. Module 03 streams a large `eve.json` through these same models at
scale; Module 04 enriches the validated `src_ip`/`dest_ip` (and dissected `dns`/`tls` indicators) against
threat-intel APIs concurrently; Module 07 applies the identical discipline to *LLM output* with
`instructor`; and Module 09 fuzzes this validator with `hypothesis` property tests. The typed object you
define here is the contract every later module builds on.

## Marketable proof
> "I put a typed pydantic boundary on real Suricata EVE JSON — parsing an alert feed into validated domain
> models that pin and constrain the fields I consume, reject malformed and adversarial lines at the edge,
> and quarantine unknown event types, with secrets loaded via pydantic-settings — so invalid states never
> reach the logic."

## Stretch (optional)
- **Dissector thread — rung 1: add a typed `dns` member (objective).** Right now any non-`alert`
  `event_type` is quarantined because the schema has no member for it. Grow the boundary into a
  **discriminated union** on `event_type`: add a second model (`DnsEvent`, `event_type: Literal["dns"]`,
  pinning `dns.rrname` / `dns.rrtype`) and parse each line through
  `TypeAdapter(EveEvent).validate_python(raw)` where `EveEvent = Annotated[Union[AlertEvent, DnsEvent],
  Field(discriminator="event_type")]`. **Acceptance check:** a `dns` line now parses into a typed
  `DnsEvent` (not quarantined), *and* a line whose `event_type` still has no union member (e.g. `stats`,
  `http`) is **quarantined** — the discriminated-union boundary holds, unknown types are never fatal.
  This is rung 1 of a dissector thread that grows one event type per module across the track (`http`,
  `tls`/`ja3`, `flow`/`fileinfo`) — keep the union in a place M03 can extend.
- Reproduce the anchor in miniature: show `yaml.load()` (unsafe) constructing an object from a crafted
  payload, then `yaml.safe_load` / your pydantic schema refusing it — the same "trusted input" bug at the
  RCE extreme.
