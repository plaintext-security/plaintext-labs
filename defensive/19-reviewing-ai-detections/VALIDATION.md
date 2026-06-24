# Validation — Module 19 (Reviewing AI Detections)

**Status: scaffolded, NOT yet validated on a Docker runner.** No `.ci-demo` marker
is present (per the repo honor-system rule, add it only once the command below is
green on a clean Linux runner).

## Prerequisite

- Docker with the Compose plugin (`docker compose`, v2).
- The build pulls `python:3.12-slim` and installs `sigma-cli`, the Splunk backend,
  the sysmon pipeline, and `pyyaml` (same toolchain as module 08). Network is
  needed at build time only; the demo runs offline against bundled data.

## Command

```bash
make up && make demo && make down
```

## Expected `make demo` output (review.py logic verified with host Python 3.12 + PyYAML)

The `review.py` harness was exercised directly against the bundled corpus and
rules (the Docker layer only adds the interpreter + `sigma-cli` + PyYAML):

1. `sigma convert` turns `ai-drafts/01_...yml` into SPL with **no error** — the
   point being that conversion passing is not correctness.
2. Firing rule 01 at the labelled corpus catches **0/2** of its malicious targets
   (wrong field) — the empirical tell a clean read misses.
3. The whole-batch review reports, one finding per planted bug:
   - `01_encoded_powershell.yml` → **MISS** (wrong field: `ProcessCommandLine`).
   - `02_rundll32_lolbin.yml` → **FALSE POSITIVE** on a benign rundll32 (over-broad condition).
   - `03_wmic_process_create.yml` → **FABRICATED ATT&CK ID** (`T1047.002` does not exist).
   - `04_wrong_logsource_creds.yml` → **NO TARGET SAMPLE** (wrong logsource: `process_creation` vs. `process_access`).
   - `05_encoded_powershell_correct.yml` → **PASS** (the control: 2/2 malicious, 0 FPs).
   - Gate verdict: **BLOCKED**, exit non-zero (swallowed by `|| true` in the demo).

`make reveal` prints `solution/findings.md` (the sealed answer key) — intended for
*after* the learner commits their own review.

## Note on the `sigma convert` step

`sigma-cli` version pins are carried over from the validated module-08 image. If a
pinned wheel is unavailable at build time, the `convert` line in `make demo` is
wrapped in `|| true`, so the demo still proceeds to the fire-test (which is the
load-bearing part). Confirm the convert step on first real `make up`.

## Files

- `Dockerfile`, `docker-compose.yml`, `Makefile` — one-command env (`up/down/reset/shell/demo`, plus `review`/`convert`/`reveal`).
- `review.py` — fire-test + ATT&CK-tag-resolution review gate.
- `ai-drafts/01..05_*.yml` — five AI-drafted Sigma rules (four planted-wrong, one control).
- `corpus/corpus.jsonl` — labelled benign+malicious telemetry (ground truth via `_label`/`_technique`).
- `attack/attack_ids.txt` — local ATT&CK ID list for tag resolution.
- `solution/findings.md` — sealed answer key (revealed by `make reveal`).
