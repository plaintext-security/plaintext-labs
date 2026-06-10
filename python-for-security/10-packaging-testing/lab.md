# Lab 10 — Packaging, Testing & Owning AI Code

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/10-packaging-testing
make up        # Python 3.12 container with pytest + ruff + bandit
make demo      # runs ruff + bandit on data/ai_generated.py (failing), then pytest (failing), then on the fixed version (passing)
make shell
make down
```

`data/ai_generated.py` is a deliberately flawed Python script that an AI plausibly generated —
a small log-analysis utility with SQL injection, missing error handling, a bad regex, and a
hardcoded credential in a test fixture. Your task is to find every bug, write tests that catch
each one, and fix the script until all tests pass.

## Scenario
Meridian's junior analyst received this script from an AI assistant and is about to run it in
production. Your lead asks you to do a proper review before it goes anywhere near live data.
Review it, write the failing tests, fix the bugs, get the tests green, and package the fixed
version as an installable tool.

> Everything runs locally against bundled code. No production systems involved.

## Do
1. [ ] `make demo` — watch `ruff` and `bandit` run over `data/ai_generated.py`. Read every
   finding. Note the severity level of each `bandit` finding.
2. [ ] Do your own review pass — read `data/ai_generated.py` line by line and list the bugs
   you find before running any tests. Compare your list to what `bandit` found. Did you catch
   something bandit missed? Did bandit catch something you missed?
3. [ ] Write `tests/test_ai_generated.py` with a test for each bug:
   - A test that demonstrates the SQL injection (pass `"' OR '1'='1"` as input; the broken
     function should return results; the fixed one should not).
   - A test that demonstrates missing timeout handling (mock the network call to raise
     `httpx.TimeoutException`; the broken function should propagate the exception; the fixed
     one should return a structured error).
   - A test that demonstrates the incorrect regex (pass a line the regex should match but
     doesn't; confirm the broken function returns `None`; the fixed one returns the match).
   - A test that confirms the hardcoded credential is gone (assert the function reads from
     `os.environ["DB_PASSWORD"]` rather than a string literal).
4. [ ] Run `pytest tests/ -v` — all four tests should fail against the unfixed code.
5. [ ] Copy `data/ai_generated.py` to `fixed.py`. Fix each bug. Run `pytest tests/ -v` again —
   all four tests should pass.
6. [ ] Run `ruff check fixed.py` and `bandit -r fixed.py` — both should exit clean.

## Success criteria — you're done when
- [ ] All four tests pass against `fixed.py`.
- [ ] `ruff check fixed.py` exits 0.
- [ ] `bandit -r fixed.py` shows no HIGH or MEDIUM findings.
- [ ] You can articulate, in one sentence each, why each original bug was dangerous.

## Deliverables
`tests/test_ai_generated.py` + `fixed.py` + `pyproject.toml` (see below). Commit all three.
Do not commit `data/ai_generated.py` changes.

## Automate & own it
**Required.** Write a `pyproject.toml` that packages `fixed.py` as a distributable tool:
- `[project]` with name `meridian-log-analyzer`, version `0.1.0`, and dependencies list.
- `[project.scripts]` entry point that makes `meridian-log-analyzer` the CLI command.
- `[tool.ruff]` section that enables the `S` (security) rule set.

Have a model draft the `pyproject.toml`; verify that `pip install -e .` works inside the
container and that `meridian-log-analyzer --help` responds. Commit the file.

## AI acceleration
Ask a model to review `data/ai_generated.py` for security issues. Compare its findings to your
manual list and to `bandit`'s findings. Rate each tool: what did the model catch that bandit
missed? What did bandit catch that the model missed? What did you catch that neither found? This
three-way comparison is the practical answer to "when do I trust AI code review?"

## Connects forward
The review-and-test workflow in this module applies to every piece of AI-generated automation
in Track 10 — especially the Terraform and Ansible reviewed in modules 02-04 and the AI-generated
Terraform in module 10. The packaging skills complete the track 09 capstone.

## Marketable proof
> "I don't just use AI to write code — I write tests that prove the AI code is correct before
> it runs in production, and I can find SQL injection, missing error handling, and hardcoded
> credentials in a code review."

## Stretch
- Add `pytest-cov` and measure test coverage over `fixed.py`; aim for 90%+ and report the
  uncovered lines.
- Set up a `pre-commit` config that runs `ruff`, `bandit`, and `pytest` before every commit.
