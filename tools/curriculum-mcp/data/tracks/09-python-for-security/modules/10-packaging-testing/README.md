# Module 10 — Packaging, Testing & Owning AI Code

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *the code an AI generates is a first draft; the tests you write turn it into software.*

## Why this matters
AI will write the script. That is no longer the differentiating skill. What separates an engineer
who ships reliable security tooling from one who ships interesting demos is the review-and-test
loop: does it handle bad input? Does it do what it claims? Does the regex actually match what it
says? These questions are answered by tests, not by reading the code. Every security script that
runs unattended in production needs a test that proves it behaves correctly on the edge cases that
will eventually happen.

## Objective
Given a deliberately flawed AI-generated security script, identify the bugs through static analysis
and testing, write `pytest` tests that catch each one, and fix the script until all tests pass —
practicing the review workflow that should precede any AI-authored code going to production.

## The core idea
The most dangerous property of AI-generated code is that it looks right. The structure is
idiomatic, the variable names are sensible, the comments are coherent — and buried inside is an
off-by-one in the regex character class, a SQL query built by string concatenation (SQL injection),
a missing `try/except` around the network call that will kill the process on the first timeout,
and a hardcoded credential in the test fixture that will end up in git. None of these are obvious
from a casual read. All of them are obvious from a systematic review.

The review checklist is not long: (1) run `bandit` and `ruff`; read every finding; don't dismiss
MEDIUM findings. (2) Check every function that takes user input — does it validate before using?
(3) Find every SQL query, shell command, and file path that involves user-provided data — is it
parameterized? (4) Find every network call — is there a timeout? Is the error handled? (5) Check
every secret — is it coming from an environment variable, or is it a string literal? Five
questions, five passes, and you've caught 80% of the production bugs in a typical AI-generated
security script.

`pytest` is the standard Python testing framework and the right tool for this module. Write
tests before you fix — this is the test-driven debugging workflow: write a test that captures
the broken behavior, confirm it fails, fix the code, confirm it passes. This sequence ensures
you actually fixed the bug and not just made the symptom disappear. A fix that makes the test
pass is a fix you can trust.

Packaging with `pyproject.toml` is the final step that makes a script into a distributable tool.
`[project]` section declares the name, version, dependencies, and entry points; `pip install .`
installs it. The entry point `[project.scripts] ioc-check = "ioc_check.cli:app"` is what turns
`python ioc_check.py` into the command `ioc-check`. This matters for security tools that get
installed on jump servers and shared via internal package mirrors — the install process is the
same as any other Python package, with a pinned `requirements.txt` and a known version.

## Learn (~2.5 hrs)

**pytest fundamentals (~1 hr)**
- [pytest — Getting Started (official docs)](https://docs.pytest.org/en/stable/getting-started.html) — read through "How to write and run tests" and "Fixtures"; understand `assert`, parametrize, and `tmp_path` fixture.
- [Effective Python Testing With pytest — Real Python](https://realpython.com/pytest-python-testing/) — deeper treatment of fixtures, marks, and mocking; the section on `monkeypatch` is especially useful for patching API calls.

**Packaging (~1 hr)**
- [Python Packaging User Guide — Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) — the canonical reference; read the "Declaring the project name", "Dependencies", and "Entry points" sections.
- [hatch — Modern Python project management](https://hatch.pypa.io/latest/) — the modern build backend; skim the "Getting started" section to understand how `pyproject.toml` + hatch replaces `setup.py`.

**Reviewing AI code (~30 min)**
- [ruff — Security rule set (S rules)](https://docs.astral.sh/ruff/rules/#flake8-bandit-s) — the specific rules that catch security bugs in Python; skim the list so you know what to enable.

## Key concepts
- The five-pass AI code review: bandit/ruff, input validation, SQL/shell/path injection, network error handling, secrets
- Test-driven debugging: write the failing test first, then fix
- `pytest.parametrize` for testing multiple inputs with one test function
- `pyproject.toml` entry points: turning a script into an installable command
- `unittest.mock.patch` for patching API calls in tests without network access

## AI acceleration
Use a model to write the initial tests — it will cover the happy path. Then push it: "Write a
test for when the API call times out." "Write a test for when the input is an empty string."
"Write a test for SQL injection." Each of those prompts uncovers a test the model didn't write
spontaneously, which usually means the code doesn't handle it correctly either. The gaps in
the test suite are a map of the bugs.
