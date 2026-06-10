# Module 01 — Setup & Security Idioms

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *build a toolchain you'd trust with production data, starting from the first line.*

## Why this matters
The first week of a new Python project usually carries the most technical debt. Dependencies get
installed globally, credentials get hardcoded to "test quickly," and the linter never gets turned
on. In security tooling that debt is not embarrassing — it is a liability: a script that runs with
ambient cloud credentials or that shells out through `eval()` can be the pivot that escalates
an incident. Setting the environment right the first time costs one hour; cleaning up compromised
credentials costs weeks.

## Objective
Stand up a clean, isolated Python 3.12 environment; write a small script that passes `ruff` lint
and `bandit` static analysis; identify and fix the common security anti-patterns that AI-generated
Python code repeats.

## The core idea
A Python virtual environment is not optional for security tooling — it is the boundary between
your carefully pinned dependencies and whatever the system (or the next analyst) installed last
month. `venv` gives you an isolated interpreter; `pip freeze > requirements.txt` (or `pip-tools`
`requirements.in`) pins what you ran; and `ruff` enforces the code quality bar before anything
runs in production. Think of it as the security hygiene equivalent of least-privilege: the tool
only has access to what you deliberately gave it.

The security anti-patterns that matter most are not exotic. **Hardcoded credentials** (`API_KEY =
"abc123"` at module level) are the single most common finding in security-team code repositories —
they end up in git, and they stay there forever in the history even after you delete the line. The
fix is `os.environ.get("API_KEY")` and a `.env` file you gitignore. **`subprocess(shell=True)`**
turns a string into a shell invocation and opens the door to injection the moment any part of
that string is user-controlled; prefer a list argument and `shell=False`. **`eval()` and
`exec()`** are almost never necessary in a security tool and are instant red flags in code review.

`bandit` is the static analyzer that catches these patterns automatically. It is not a substitute
for code review, but it is the first gate — the equivalent of running `checkov` before you
`terraform apply`. A clean `bandit` run does not mean the code is safe; it means the obvious
landmines are gone. `ruff` handles style and common bugs (shadowed builtins, unused imports,
mutable defaults) faster than `flake8` + `isort` combined. Running both before every commit is
the floor, not the ceiling.

Secrets management in practice: production tools use environment variables or a secrets manager
(Vault, AWS Secrets Manager, Azure Key Vault) — never the source file. For local lab work, a
`.env` file loaded by `python-dotenv` is acceptable, provided the file is in `.gitignore` from
day one. Get into this habit on the first script; undoing it later is painful.

## Learn (~2 hrs)

**Environment setup (~45 min)**
- [Python Virtual Environments Primer — Real Python](https://realpython.com/python-virtual-environments-a-primer/) — the definitive walkthrough of why venv exists and how to use it correctly; covers `activate`, `deactivate`, and `requirements.txt`.
- [pip-tools documentation](https://pip-tools.readthedocs.io/en/latest/) — for when `requirements.txt` alone is not enough; shows how to pin a full dependency tree reproducibly.

**Code quality (~45 min)**
- [Ruff — fast Python linter and formatter](https://docs.astral.sh/ruff/) — read the "Getting started" and "Configuration" sections; understand what rule codes mean so you can triage findings.
- [Bandit — security linter for Python (PyCQA)](https://bandit.readthedocs.io/en/latest/) — skim the "Getting started" and "Tests" sections to understand the finding levels and how to suppress a false positive.

**Security idioms (~30 min)**

## Key concepts
- Why virtual environments are a security boundary, not just a convenience
- `ruff` for style/bug-catching; `bandit` for security-specific anti-patterns
- The three most dangerous Python idioms: hardcoded secrets, `shell=True`, `eval()`
- Secrets via environment variables and `.env` (gitignored) for local work
- `pip freeze` / `pip-tools` for reproducible, auditable dependency pinning

## AI acceleration
AI generates Python code that passes syntax checks but routinely includes `shell=True`, raw
`os.system()`, and API keys in strings. Ask a model to write a script, then immediately feed
the output to `bandit -r .` — you will find something on the first try. The workflow: model
drafts, `ruff` formats, `bandit` gates, you read and own it.
