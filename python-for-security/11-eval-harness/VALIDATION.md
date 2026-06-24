# Validation — Module 11: Eval Harness

## Prerequisites
- Docker (with Compose v2: `docker compose ...`). No GPU, no model, no network at
  runtime. The image is `python:3.12.9-slim` + pinned `pytest` / `coverage`.

## One-command check
```bash
cd plaintext-labs/python-for-security/11-eval-harness
make up && make demo && make down
```

### Expected `make demo` outcome
`demo` scores both parsers over the held-out corpus and ends with the success line:

```
======================== verdict ========================
PASS: gate is GREEN on the good parser and RED on the regression
```

- **GOOD parser** (`scripts/parser_good.py`): recall **1.000**, gate `recall>=0.85`
  PASSES, exit 0.
- **REGRESSED parser** (`scripts/parser_regressed.py`): the slow-and-low spray
  `198.51.100.7` is a false negative (FN), recall drops to **0.667**, gate FAILS,
  exit 1. Note its accuracy is still 0.900 — the imbalanced-corpus trap the lab calls out.

## Other targets (exercised by lab.md)
```bash
make eval                  # full scorecard for the good parser (no gate)
make classify              # writes results/verdicts-good.json (gitignored)
make gate RECALL_MIN=0.95  # re-run the gate at a stricter floor (good parser now FAILS)
make test                  # pytest: scorer math + parser robustness (12 tests)
make coverage              # coverage of the parser over the corpus (coverage-as-foil step)
make shell                 # interactive shell in the container
```

## Host-side pre-check (no Docker)
The eval and parsers are pure stdlib, so the core logic was verified on the host
before containerizing:
```bash
python3 eval.py --tool scripts/parser_good.py      --corpus data/auth-corpus.jsonl --labels data/auth-labels.json --gate recall=0.85   # -> PASS, exit 0
python3 eval.py --tool scripts/parser_regressed.py --corpus data/auth-corpus.jsonl --labels data/auth-labels.json --gate recall=0.85   # -> FAIL, exit 1
python3 eval.py --tool scripts/parser_good.py      --corpus data/auth-corpus.jsonl --labels data/auth-labels.json --gate recal=0.85    # -> fail-closed, exit 2 (typo'd metric)
python -m pytest tests/ -v                                                                                                              # -> 12 passed
```
All four behaved as expected during scaffolding. **Docker (`make up/demo/down`) was
NOT run in this environment — validate on a Docker-capable host before adding `.ci-demo`.**

> No `.ci-demo` marker is present: per the lab's design the gate intentionally goes
> RED on the regressed parser, and `make demo` only exits 0 via its own wrapper logic.
> Confirm `make up && make demo && make down` is green on a clean Linux runner before
> marking this lab CI-eligible.
