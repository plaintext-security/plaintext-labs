# Lab 02 — A Typed Input Boundary for `sift`

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/02-parse-dont-validate` (a container
> with `python` + `pydantic`/`pydantic-settings`, the trusting `sift_starter/triage.py`, a curated Suricata
> `data/eve.json` with adversarial lines, and a finished `sift_reference/`). This lab **adds a typed
> EVE-JSON input boundary to `sift`** — the same alert-triage tool you started in Module 01 — so malformed
> and adversarial Suricata events are rejected at the door instead of becoming a bug three calls deep.
> Target: **~2–3 hrs.** *Intermediate-plus: the steps state objectives; you and your copilot derive the
> pydantic/ingest code.*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **"Parse, don't validate" — the type *is* the check.** | Convert each untrusted EVE line to a typed `AlertEvent` *once* at the boundary; the invariant then holds everywhere downstream. |
| 2 | **Pin, don't forbid, on a real feed.** | `extra="ignore"` the sprawling EVE envelope; strictness comes from the *constrained* fields you actually consume. |
| 3 | **Domain rules become types.** | `IPvAnyAddress`, `Field(ge=1, le=3)` make a malformed record *unrepresentable*, not merely flagged. |
| 4 | **Reject-policy is *your* decision.** | halt / quarantine / skip-and-log — catch `ValidationError` where you can act on `.errors()`, not three layers up. |
| 5 | **Secrets are a boundary too.** | `pydantic-settings` `BaseSettings`/`SecretStr`: a missing key fails loud at startup and never lives in source. |
| 6 | **This adds the input edge to `sift`.** | Same tool as M01; M03 streams a big feed through these models, M04 enriches the validated IPs. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea), the pydantic Models/Fields/Validators docs, and the anchor CVE
> (`CVE-2017-18342`, `yaml.load()` RCE).

---

## Warm-up — answer before you build (2 min)

1. What does converting a line to a typed `AlertEvent` *at the boundary* buy you that scattering
   `if`-checks downstream does not?
2. Real EVE has dozens of envelope fields. Why is `extra="forbid"` on the whole record the wrong call, and
   what do you use *instead* to stay strict about the fields you consume?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/02-parse-dont-validate
make up      # build the lab container (python + pydantic/pydantic-settings)
make shell   # drop into the lab with sift_starter/, data/eve.json, sift_reference/
make demo    # the contrast: the starter trusts garbage or dies; the boundary rejects every bad record
make down    # stop when done
```

The lab builds on the **custom `sift` target** you started in Module 01 — you edit the source to add the
boundary, which a black-box image can't teach. Fold `sift_starter/` into your `sift` repo (or work in
place), and peek at `sift_reference/` only after you've built your own. Reproducible at zero cost.

> **Authorization note.** Everything runs locally in the lab container against bundled sample data — only
> test systems you own or have explicit written permission to test.

---

## Build it — objective, then a signal (intermediate-plus: you drive the code)

### Step 1 — Find the trust

**Concept (30 sec):** Flight-card #1. The most dangerous line in a security tool is the one that trusts
its input. Inventory where `sift` currently does.

**Do:** grep `sift_starter/triage.py` for `.get(`, `[` indexing, and `isinstance` on the raw feed — map
every place it assumes an untrusted EVE line's shape (there are half a dozen, across
`normalize`/`enrich`/`score`/`triage`, including the `event["alert"]["signature"]` reach).

> **▸ On track if:** you have a written list of every spot that touches a raw dict as if its fields were
> already the right type and shape — that `.get()`-soup is exactly what you're replacing.

### Step 2 — Write the spec first

**Concept (30 sec):** Flight-card #1 + the track's spec-driven workflow. The spec is the contract you
review the copilot's models *against*.

**Do:** spec the boundary — the fields you **pin and constrain** (`timestamp` → `datetime`,
`src_ip`/`dest_ip` → `IPvAnyAddress`, `alert.signature_id` → `int`, `alert.severity` →
`Field(ge=1, le=3)`), which are *required* vs *legitimately optional* (some events omit `dest_ip` or
`flow_id`), the decision to `extra="ignore"` the envelope rather than `extra="forbid"`, and the
**reject-policy** (pick one: halt / quarantine / skip-and-log — and justify it).

> **▸ On track if:** the spec names the typed contract, the required-vs-optional split, and the acceptance
> checks (valid `alert` line → typed object; each malformed fixture → rejected) — not just "add pydantic."

### Step 3 — Model the domain

**Concept (30 sec):** Flight-card #2 + #3. Make them *real types*, not stringly-typed placeholders; the
constraint *is* the check. Record-level policy is ignore-and-pin, not forbid.

**Do:** implement `EveBase`, `AlertDetails`, `AlertEvent` as pydantic v2 `BaseModel`s over the real EVE
fields. The shape (the API here *is* the lesson):

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

class EveBase(BaseModel):
    model_config = ConfigDict(extra="ignore")  # EVE has many envelope fields — ignore the rest
    timestamp: datetime
    src_ip: IPvAnyAddress | None = None
    dest_ip: IPvAnyAddress | None = None        # some events legitimately omit it — optional, not absent-crash
    proto: str | None = None

class AlertDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")
    signature: str
    signature_id: int                           # a string here is rejected, not fed downstream
    severity: int = Field(ge=1, le=3)           # Suricata severity is 1..3; 5 is rejected

class AlertEvent(EveBase):
    event_type: Literal["alert"]                # the discriminant; other types have no member yet
    alert: AlertDetails
```

> **▸ On track if:** every field you consume carries a real *constraint* (an IP that must parse, a bounded
> severity, a typed `signature_id`) — not a bare annotation an attacker's value would sail through.

### Step 4 — Parse at the boundary

**Concept (30 sec):** Flight-card #1. One `model_validate` converts untrusted input into a type; from then
on `pyright` enforces the shape for free.

**Do:** replace the ingest with a single `AlertEvent.model_validate(raw)` per line (after `json.loads`),
then delete the downstream `.get()`/`isinstance` guards you inventoried in Step 1.

> **▸ On track if:** downstream code receives an `AlertEvent`, not a dict of maybes, and `pyright` is happy
> treating each record as that type — the invariant is now carried by the type, checked once.

### Step 5 — Decide what "reject" does

**Concept (30 sec):** Flight-card #4. A validating parser gives you the *option* to be strict; you still
choose the policy. Don't let one poisoned line halt the run *or* pass silently.

**Do:** wrap the loader so a truncated / non-JSON line raises `json.JSONDecodeError` and a schema violation
raises `ValidationError`, and catch *both* at the ingest loop to apply your spec's policy — skip-and-log
the offending line + `err.errors()` to a quarantine file (recommended for a triage tool).

> **▸ On track if:** the validator **rejects the truncated line, the missing `dest_ip`, the out-of-range
> `severity` (5), and the wrong-type `signature_id`**, *and* the unhandled `event_type` (no union member)
> is **quarantined, not fatal** — a line the starter's `.get()` code trusted is now refused with a reason.

### Step 6 — Move secrets to `pydantic-settings`

**Concept (30 sec):** Flight-card #5. The starter's `enrich()` does `os.environ.get("SIFT_VT_API_KEY", "")`
and silently carries on when the key is missing — the same "trust the input" bug aimed at config.

**Do:** replace it with a `BaseSettings` object (`SecretStr` for the key, loaded from env / `.env`).

> **▸ On track if:** a missing key fails **loudly at startup** (not as a confusing `None` mid-request), and
> the secret never appears in source or logs.

---

## Prove the control (your finish line)

Run `sift` over `data/eve.json` and confirm the boundary holds — commit this **advanced `sift`**:

- [ ] Every EVE line passes through **one** `AlertEvent.model_validate` boundary; downstream receives typed `AlertEvent`s, not dicts (`pyright` confirms).
- [ ] Constraints bite: the missing `dest_ip`, the out-of-range `alert.severity` (5), the wrong-type `signature_id`, and the truncated non-JSON line are each **rejected** — no downstream crash, no silent default.
- [ ] Record-level policy is `extra="ignore"` (a real EVE line with envelope fields still parses); strictness comes from the **pinned/constrained** fields — you did **not** `extra="forbid"` the record.
- [ ] Your **reject-policy** is implemented and demonstrated: malformed lines quarantined/logged, valid ones flow through, the unhandled `event_type` quarantined not fatal.
- [ ] The API key loads via `pydantic-settings`; a missing key fails at startup; no secret in source or logs.
- [ ] The spec is updated and the CI gate (`ruff`/`pyright` + the parse tests) is green.

---

## Recall check — close the doc, answer from memory (3 min)

1. "Parse, don't validate" in one sentence — what does the typed boundary carry that scattered `if`-checks lose?
2. Why is `extra="forbid"` wrong on a real EVE line, and what gives you strictness instead?
3. One malformed line in ten thousand: what's your reject-policy, and why is "let it crash" the wrong default for a triage tool?

---

## Deliverables

The updated **`sift`** repository: the `models.py` (`EveBase`/`AlertDetails`/`AlertEvent`) boundary, the
`pydantic-settings` config, the ingest loop with its reject-policy, the parse/reject tests, and the updated
spec. Commit all of it. Do **not** commit the real API key or any populated `.env` — only a committed
`.env.example`.

## Automate & own it

**Required.** Commit the increment — `sift` with a typed EVE input boundary and `pydantic-settings` —
updating the spec and CI. Have the copilot draft the models, the ingest refactor, and the adversarial
fixtures from your spec, then review the draft against it. In the commit/PR, note what the copilot
generated and the **one thing it defaulted to** that you had to fix — the three high-value catches are
*annotating without constraining* (`dest_ip: str` where you specified an IP that must parse; a bare
`severity: int` where `1..3` is the rule), *defaulting instead of rejecting* (`.get("severity", 1)`
sneaking back as a "safe" fallback), and *over-sealing the record* (`extra="forbid"` that rejects every
genuine EVE line). Reviewing what the model *lets through* is where this class of risk lives.

## Definition of done (`parse-dont-validate` ✅)

- [ ] The typed boundary is committed to `sift`; every EVE line parses through one `model_validate` or is rejected.
- [ ] Constraints, reject-policy, and `pydantic-settings` are all demonstrated on `data/eve.json`; CI is green.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

This boundary is the **input edge** of the track's *parse, don't trust* through-line, and it defines the
EVE data model every later module reuses. Module 03 streams a large `eve.json` through these same models at
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
  Field(discriminator="event_type")]`. **▸ On track if:** a `dns` line now parses into a typed `DnsEvent`
  (not quarantined), *and* a line whose `event_type` still has no union member (e.g. `stats`, `http`) is
  **quarantined** — the discriminated-union boundary holds, unknown types are never fatal. This is rung 1
  of a dissector thread that grows one event type per module across the track (`http`, `tls`/`ja3`,
  `flow`/`fileinfo`) — keep the union somewhere M03 can extend.
- Reproduce the anchor in miniature: show `yaml.load()` (unsafe) constructing an object from a crafted
  payload, then `yaml.safe_load` / your pydantic schema refusing it — the same "trusted input" bug at the
  RCE extreme.
