# Lab 01 — Migrate a Legacy Script into a Spec-Driven `uv` Project

*[← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo at
`plaintext-labs/python-for-security/01-modern-toolchain/`: a container with `uv`, `ruff`, `pyright`, and
`git` preinstalled, plus the legacy `alert_parse.py` you'll migrate and a small bundled alert sample.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/01-modern-toolchain
make up      # build the toolchain container
make shell   # drop into the project with the legacy script
make demo    # runs the migrated project's CI gate (lint + types + locked install + the legacy script)
make down    # stop when done
```

The lab **builds one custom minimal target** — a legacy script — because the lesson is the *migration
mechanism* and you edit the source yourself; a black-box image can't teach that. It is reproducible at
zero cost.

## Scenario

You've inherited `alert_parse.py`: a 60-line script a teammate wrote that reads a JSON alert feed and
prints a summary. It works, it's in production, and it has no tests, no lockfile, no types, and a
`requirements.txt` last touched two years ago. You're going to migrate it into the modern skeleton the
rest of this track builds in — **without breaking it at any step** — and turn it into the seed of `sift`,
the alert-triage tool you grow across all nine modules.

> Only test systems you own or have explicit written permission to test. Everything here runs locally in
> the lab container against bundled sample data.

## Do

1. [ ] **Reproduce the legacy baseline.** Run `alert_parse.py` against the bundled sample and capture its
   output. This is your ground truth — the migration is correct only if this output never changes.
2. [ ] **Write the spec first.** Using the spec-driven workflow (openspec, or spec-kit), write a short
   change spec for the migration: "wrap the existing script unchanged in a `uv` project; add `ruff`,
   `pyright`, and a hash-locked lockfile; gate all three in CI; behavior identical." The spec is the
   contract you'll review the copilot's work against.
3. [ ] **Stand up the `uv` project *around* the script (strangler-fig).** `uv init` the project, add the
   script unchanged as a module/entry point, and get `uv run` to reproduce step 1's output byte-for-byte.
   Do **not** refactor yet — wrap first.
4. [ ] **Add the gates.** Configure `ruff` and `pyright` in `pyproject.toml`; produce a hash-locked
   `uv.lock`. Let the copilot generate the config, then check it against your spec — pinned *and* hashed?
   type gate actually on?
5. [ ] **Wire CI.** Add a workflow that fails on any of: `ruff` findings, `pyright` errors, or a
   non-reproducible/unlocked install. Prove it fails by introducing a lint error, then fix it.
6. [ ] **Migrate one slice behind the green gate.** Now refactor *one* piece (e.g. add types to the parse
   function, or split I/O from logic) — and prove step 1's output still matches and CI stays green.
   Keep a rollback (the prior commit) at every step.
7. [ ] **Write the ADR.** Record the decision: why `uv`/`ruff`/`pyright` over `pip`/`venv`/`flake8`, why
   a hash-locked lockfile, and which spec-driven tool you chose and its honest downside.
8. [ ] **Automate & own it.** Commit the migrated project — `sift` v0 — with the CI gate, the spec, and
   the ADR. In the commit/PR, note what the copilot generated, what you corrected, and the one thing it
   defaulted to that you had to fix (the old toolchain, the missing lockfile, or a dropped behavior).

## Success criteria — you're done when
- [ ] `uv run` reproduces the legacy script's output **byte-for-byte** — the migration broke nothing.
- [ ] `ruff` and `pyright` are clean, and the install is reproducible from a **hash-locked** `uv.lock`.
- [ ] CI fails on a planted lint/type error and passes when it's fixed (you demonstrated both).
- [ ] A spec for the migration exists, and you can point to the implementation that satisfies it.
- [ ] An ADR records the toolchain + spec-workflow decision with an honest "Consequences" section.

## Deliverables
The migrated `sift` v0 repository: the `uv` project wrapping the legacy script, `pyproject.toml` with
`ruff`/`pyright` config, the hash-locked `uv.lock`, the CI workflow, the migration spec, and
`ADR-001-toolchain.md`. Commit all of it. Do **not** commit any real API keys or `.env` — the later
modules add secrets handling.

## AI acceleration
Have the copilot generate the entire skeleton — `pyproject.toml`, CI YAML, the wrapping module — from
your spec, then review the diff against the spec rather than reading it cold. The high-value catch is the
copilot's *defaults*: it will tend to emit `pip`/`requirements.txt`, skip the lockfile hashes, and leave
types off. Fixing those is the whole point — you're reviewing the AI's setup, which is where this class
of risk actually lives.

## Connects forward
This skeleton is the home for every later module: Module 02 adds `pydantic` validation inside it, Module
04 makes it async, Module 09 hardens the very supply-chain gate you started here. The strangler-fig
migration muscle returns in Track 06 (brownfield AD tiering) and Track 10 (click-ops → IaC), where a
big-bang cutover means a real outage.

## Marketable proof
> "I migrate legacy Python into a modern `uv`/`ruff`/`pyright` project with a hash-locked supply-chain
> gate in CI, using a spec-driven workflow to direct and review AI-generated code — without breaking the
> running script."

## Stretch (optional)
- Add `pip-audit` (or `uv`'s audit) to the CI gate and make it fail on a known-vulnerable pinned
  dependency — a preview of Module 09's supply-chain work.
- Reproduce the `torchtriton` class in miniature: stand up a tiny private index, show how an unpinned
  install resolves the *public* shadowing package, then show the hash-locked install refusing it.
