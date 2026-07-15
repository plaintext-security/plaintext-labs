# Lab 02 — A Typed Input Boundary for `sift`

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/02-parse-dont-validate/`:

- **`sift_starter/`** — where `sift` stands after the copilot "helped": a working feed-triage draft
  (`triage.py`) that reads alerts into dicts and trusts them — `.get()` defaults, `isinstance` patch-ups,
  shape-assuming indexing, and an API key read straight from the environment. Fold it into your `sift`
  project from Module 01 (or work on it in place).
- **`data/`** — the messier sample: the clean records, malformed ones (a bad IP, an out-of-enum severity,
  a fake hash, a wrong-type id, a missing field), and an *adversarial* one designed to slip past naive
  `.get()` handling.
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

`sift` currently reads the alert feed straight into dicts and reaches into them with `.get()` and
`if`-checks — the exact shape the copilot handed you (`sift_starter/triage.py`). It works on the clean
sample and falls apart on the real one: a malformed IP sails through and gets scored as a real IOC, an
out-of-enum severity is silently *defaulted* instead of rejected, and a record missing its `indicator` —
or carrying a string where a number was assumed — kills the whole run three calls deep. An alert with an
unexpected extra field is trusted anyway. Run `make demo` to watch all of that happen. You're going to add
a **typed boundary** — `Alert` and `Indicator` pydantic models — so the raw feed becomes validated domain
objects or gets rejected at the door, and move `sift`'s API key out of the code into `pydantic-settings`.

> Only test systems you own or have explicit written permission to test. Everything here runs locally in
> the lab container against bundled sample data.

## Do

1. [ ] **Find the trust.** Grep `sift_starter/triage.py` for `.get(`, `[` indexing, and `isinstance` on
   the raw feed — inventory every place it assumes an untrusted field's shape (there are half a dozen,
   spread across `normalize`/`enrich`/`score`/`triage`). This is the `.get()`-soup you're replacing.
2. [ ] **Write the spec first.** Per the track's spec-driven workflow, spec the boundary: the `Alert`
   fields and their **types/constraints** (id is an integer, severity from a fixed enum, the nested
   `Indicator`'s value must match its `kind` — an `ipv4` must parse, a `sha256` is 64 hex chars), the
   **reject-policy** (halt / quarantine / skip-and-log — pick one and justify it), and the acceptance
   checks (valid → typed object; each malformed fixture → `ValidationError`).
3. [ ] **Model the domain.** Implement `Indicator` and `Alert` as pydantic v2 `BaseModel`s. Make the
   fields real types, not stringly-typed placeholders — the constraint *is* the check:

   ```python
   import ipaddress
   from typing import Literal
   from pydantic import BaseModel, field_validator

   Severity = Literal["low", "medium", "high", "critical"]

   class Indicator(BaseModel):
       kind: Literal["ipv4", "domain", "sha256"]
       value: str

       @field_validator("value")
       @classmethod
       def value_matches_kind(cls, v: str, info) -> str:
           if info.data.get("kind") == "ipv4":
               ipaddress.IPv4Address(v)   # a non-IP raises here, not three calls down
           # ... and constrain the other kinds too (64 hex chars, no spaces/slashes)
           return v

   class Alert(BaseModel):
       model_config = {"extra": "forbid"}  # an unexpected field is a signal, not noise
       id: int                             # "seven" is rejected, not fed into a sort
       source: str
       severity: Severity                  # anything outside the enum is rejected
       indicator: Indicator
   ```

4. [ ] **Parse at the boundary.** Replace the ingest with a single `Alert.model_validate(raw)` per record.
   Delete the downstream `.get()`/`isinstance` guards — the type now carries the invariant, so prove
   `pyright` is happy treating each record as an `Alert`, not a dict.
5. [ ] **Decide what "reject" does.** Catch `ValidationError` at the ingest loop and apply your spec's
   policy: skip-and-log with the offending record + `err.errors()` to a quarantine file (recommended for a
   triage tool), so one poisoned alert doesn't halt the run *or* pass silently.
6. [ ] **Prove the boundary holds.** Run `sift` over the messy sample: the valid records become `Alert`
   objects, and each malformed/adversarial fixture is rejected with a precise field-level reason. Add a
   fixture the copilot's original `.get()` code trusted and show the model now refuses it.
7. [ ] **Move secrets to `pydantic-settings`.** The starter's `enrich()` does
   `os.environ.get("SIFT_VT_API_KEY", "")` and silently carries on when the key is missing. Replace it
   with a `BaseSettings` object (`SecretStr` for the key, loaded from env / `.env`) so a missing key fails
   loudly at startup and the secret never lives in source or logs.
8. [ ] **Automate & own it.** Commit the increment — `sift` with a typed input boundary and
   `pydantic-settings` — updating the spec and CI. In the commit/PR, note what the copilot generated, and
   the one thing it defaulted to that you had to fix: an unconstrained type it *annotated* but didn't
   *validate*, or malformed input it silently defaulted instead of rejecting.

## Success criteria — you're done when
- [ ] Every raw record passes through **one** `Alert.model_validate` boundary; downstream code receives typed `Alert`s, not dicts (`pyright` confirms it).
- [ ] Fields carry **real constraints** — the bad IP, the out-of-enum severity, the wrong-type id, and the missing `indicator` each raise `ValidationError`, not a downstream crash or a silent default.
- [ ] Your **reject-policy** is implemented and demonstrated: malformed records are handled deliberately (quarantined/logged), valid ones flow through.
- [ ] The API key loads via `pydantic-settings`; a missing key fails at startup, and no secret appears in source or logs.
- [ ] The spec is updated and the CI gate (ruff/pyright + the parse tests) is green.

## Deliverables
The updated `sift` repository: the `models.py` (`Alert`/`Indicator`) boundary, the `pydantic-settings`
config, the ingest loop with its reject-policy, the parse/reject tests, and the updated spec. Commit all
of it. Do **not** commit the real API key or any populated `.env` — only a committed `.env.example`.

## AI acceleration
Have the copilot draft the models, the ingest refactor, and the adversarial fixtures from your spec — then
review the draft against it. The two high-value catches are the copilot's habit of *annotating without
constraining* (`ip: str` where you specified an IP that must parse) and *defaulting instead of rejecting*
(`.get("severity", "low")` sneaking back in as a "safe" fallback). Make the model generate the malformed
inputs it thinks its own code handles, then run them and watch which ones it actually lets through — that
gap is the review.

## Connects forward
This boundary is the input edge of the track's *parse, don't trust* through-line. Module 03 streams a
large feed through these same models at scale; Module 04 enriches the validated `Indicator`s against
threat-intel APIs concurrently; Module 07 applies the identical discipline to *LLM output* with
`instructor`; and Module 09 fuzzes this validator with `hypothesis` property tests. The typed object you
define here is the contract every later module builds on.

## Marketable proof
> "I put a typed pydantic boundary on untrusted security data — parsing an alert feed into validated
> domain models that reject malformed and adversarial input at the edge, with secrets loaded via
> pydantic-settings — so invalid states never reach the logic."

## Stretch (optional)
- You shipped `extra="forbid"` — now argue the other side: relax it to `extra="ignore"` and reason about
  when strictness helps (an unexpected field on a security feed is a signal) and when it breaks a
  legitimately-evolving upstream feed. Which would you run in production, and behind what alert?
- Reproduce the anchor in miniature: show `yaml.load()` (unsafe) constructing an object from a crafted
  payload, then `yaml.safe_load` / your pydantic schema refusing it — the same "trusted input" bug at the
  RCE extreme.
