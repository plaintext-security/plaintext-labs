# Validation — Module 18 (Detection Drift)

**Status: scaffolded, NOT yet validated on a Docker runner.** No `.ci-demo` marker
is present (per the repo honor-system rule, add it only once the command below is
green on a clean Linux runner).

## Prerequisite

- Docker with the Compose plugin (`docker compose`, v2).
- No network access needed at run time; the build pulls `python:3.12-slim` and
  `pyyaml` once.

## Command

```bash
make up && make demo && make down
```

## Expected `make demo` output (verified with host Python 3.12 + PyYAML)

The harness logic was exercised directly with `python3 drift_check.py ...` against
the bundled fixtures (the Docker layer only adds the interpreter + PyYAML):

- **t=0 BASELINE** — all four sources `OK`, rule recall `1.00`, verdict **CLEAN**,
  exit `0`.
- **t=30 OBSERVED** — detects three drifts and exits non-zero (swallowed by `|| true`
  in the demo so the target still succeeds):
  - `MER-FS01` → `DRIFT: DEGRADED (volume 3 < floor 20)` — the volume tell a binary
    up/down check would miss.
  - `MER-DC01` → `DRIFT: DEAD (no events)` — the source that stopped logging.
  - `MER-LEGACY03` → `DRIFT: DEAD` — becomes "expected silence" only after the
    learner sets `decommissioned: true` in the reconcile step.
  - Rule recall regresses `1.00 → 0.00` — the field-rename (CommandLine →
    ProcessCommandLine) that rots a rule which still parses and runs.

## Files

- `Dockerfile`, `docker-compose.yml`, `Makefile` — one-command env (`up/down/reset/shell/demo`).
- `drift_check.py` — the drift harness (telemetry heartbeat+volume, detection re-score).
- `baseline/sources.yml` — declared baseline manifest (the "expected" half).
- `data/events_t0.jsonl`, `data/events_t30.jsonl` — healthy vs. drifted telemetry.
- `corpus/corpus_t0.jsonl`, `corpus/corpus_t30.jsonl` — labelled re-scoring corpus.
- `rules/encoded_powershell.yml` — the detection that rots under schema drift.
