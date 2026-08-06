# Lab 01 — Migrate a Legacy Script into a Spec-Driven `uv` Project

> **Hands-on lab.** Environment: `plaintext-labs/python-for-security/01-modern-toolchain` (a container
> with `uv`, `ruff`, `pyright`, `git` + the legacy `alert_parse.py` and a bundled Suricata `eve.json`).
> Objective: **migrate a working legacy script into a modern, CI-gated `uv` project without breaking it —
> landing `sift` v0**, the alert-triage tool you grow across all nine modules. Target: **~2–3 hrs.**
> *Intermediate-plus: the steps state objectives; you derive the `uv`/`ruff`/CI commands (with the copilot).*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The toolchain is a security control, not a preference.** | A hash-locked lockfile defeats the `torchtriton` dependency-confusion class. |
| 2 | **Hash-locked ≠ version-pinned.** | `torch==2.0.1` fixes the version, not the *bytes*; the hash refuses tampered bytes. |
| 3 | **Strangler-fig: wrap first, never big-bang.** | Wrap the working script, get CI green *around* it, refactor behind the gate. |
| 4 | **Spec → AI implements → review *against the spec*.** | A far sharper lens than reading generated code cold — and how you *own* it. |
| 5 | **CI is where the bar is enforced.** | Lint, types, and lockfile checks fail the build — not your goodwill. |
| 6 | **This lab lands `sift` v0.** | Every later module adds a stage; the migration is the seed of the whole track. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) and the `torchtriton` primary source.

---

## Warm-up — answer before you build (2 min)

1. Why does pinning `torch==2.0.1` **not** fully protect you, and what does a hash-locked file add?
2. What breaks if you delete `alert_parse.py` and have the copilot regenerate it clean, versus wrapping
   it and migrating behind a passing CI gate?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/01-modern-toolchain
make up      # build the toolchain container
make shell   # drop into the project with the legacy alert_parse.py + bundled eve.json
make demo    # runs the migrated project's CI gate (lint + types + locked install + the legacy script)
make down
```

> **Authorization note.** Everything runs locally in the lab container against bundled sample data —
> only test systems you own or have written permission to test.

---

## Build it — objective, then a signal (intermediate-plus: you drive the commands)

### Step 1 — Reproduce the legacy baseline (your ground truth)

**Concept (30 sec):** Flight-card #3. The migration is *correct* only if the legacy output never changes.
Capture it before you touch anything.

**Do:** run `alert_parse.py` against the bundled `eve.json`; save its output (it counts `alert` events by
`alert.signature`).

> **▸ On track if:** you have a saved baseline output you can diff against at every later step.

### Step 2 — Write the spec first

**Concept (30 sec):** Flight-card #4. The spec is the contract you review the copilot's work *against*.

**Do:** write a short change spec for the migration — *wrap the script unchanged in a `uv` project; add
`ruff`, `pyright`, and a hash-locked lockfile; gate all three in CI; behaviour identical.*

> **▸ On track if:** the spec names the typed contract and the acceptance checks — not just "modernize it."

### Step 3 — Stand up the `uv` project *around* the script (strangler-fig)

**Concept (30 sec):** Flight-card #3. Wrap, don't rewrite. No refactor yet.

**Do:** `uv init` the project, add the script unchanged as an entry point, and get `uv run` to reproduce
Step 1's output.

> **▸ On track if:** `uv run` reproduces the baseline **byte-for-byte** — and you haven't edited the script's logic.

### Step 4 — Add the gates (and review the copilot's defaults)

**Concept (30 sec):** Flight-card #1 + #2. Let the copilot generate the config, then hold it to the bar.

**Do:** configure `ruff` and `pyright` in `pyproject.toml`; produce a **hash-locked** `uv.lock`.

> **▸ On track if:** the lockfile is pinned **and** hashed, and the type gate is actually on — catch the
> copilot if it emitted `pip`/`requirements.txt`, skipped the hashes, or left types off.

### Step 5 — Wire CI, then prove it bites

**Do:** add a workflow that fails on any of `ruff` findings, `pyright` errors, or a non-reproducible
install. Plant a lint error, watch CI fail, fix it.

> **▸ On track if:** you have demonstrated **both** a red build (planted error) and a green one (fixed).

### Step 6 — Migrate one slice behind the green gate

**Do:** refactor *one* piece (e.g. type the parse function, or split I/O from logic); keep the prior
commit as rollback.

> **▸ On track if:** Step 1's output still matches byte-for-byte **and** CI stays green after the refactor.

---

## Prove the control (your finish line)

Commit **`sift` v0** and confirm the whole gate holds:

- [ ] `uv run` reproduces the legacy output **byte-for-byte** (migration broke nothing).
- [ ] `ruff` + `pyright` clean; install reproducible from a **hash-locked** `uv.lock`.
- [ ] CI fails on a planted lint/type error and passes when fixed (you showed both).
- [ ] The migration **spec** exists and you can point to the implementation that satisfies it.
- [ ] `ADR-001-toolchain.md` records the decision with an honest **Consequences** section.

---

## Recall check — close the doc, answer from memory (3 min)

1. Hash-locked vs version-pinned — which one stops the `torchtriton` class, and why?
2. State the strangler-fig sequence in three moves.
3. What does reviewing an implementation *against a spec* catch that reading the code cold does not?

---

## Deliverables

The migrated **`sift` v0** repo: the `uv` project wrapping the legacy script, `pyproject.toml`
(`ruff`/`pyright`), the hash-locked `uv.lock`, the CI workflow, the migration spec, and
`ADR-001-toolchain.md`. *Do not commit real API keys or `.env` — later modules add secrets handling.*

## Automate & own it

**Required.** Commit `sift` v0 with the CI gate, the spec, and the ADR. In the commit/PR, note what the
copilot generated, what you corrected, and the **one thing it defaulted to** that you had to fix (the old
toolchain, the missing lockfile hashes, or a dropped behaviour). Reviewing the AI's *setup* is where this
class of risk lives.

## Definition of done (`modern-toolchain` ✅)

- [ ] `sift` v0 is committed with a green CI gate over lint + types + a hash-locked install.
- [ ] The byte-for-byte migration, the spec, and `ADR-001-toolchain.md` are all in the repo.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

This skeleton is the home for every later module: **02** adds `pydantic` validation inside it, **04**
makes it async, **09** hardens the very supply-chain gate you started here. The strangler-fig muscle
returns in Track 06 (brownfield AD tiering) and Track 10 (click-ops → IaC), where a big-bang cutover means
a real outage.

## Marketable proof

> "I migrate legacy Python into a modern `uv`/`ruff`/`pyright` project with a hash-locked supply-chain
> gate in CI, using a spec-driven workflow to direct and review AI-generated code — without breaking the
> running script."

## Stretch (optional)

- Add `pip-audit` (or `uv`'s audit) to CI and make it fail on a known-vulnerable pinned dependency — a
  preview of Module 09.
- Reproduce the `torchtriton` class in miniature: a tiny private index, an unpinned install resolving the
  *public* shadowing package, then the hash-locked install refusing it.
