# Lab 01 — Setup & Security Idioms

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/01-setup-idioms
make up        # build the Python 3.12 container with ruff + bandit
make demo      # run ruff and bandit over data/insecure.py and show findings
make shell     # drop into the container to work interactively
make down      # stop when done
```

The container ships `python3.12`, `venv`, `ruff`, and `bandit`. The `data/` directory holds
`insecure.py` — a deliberately flawed script that mimics what AI-generated security tooling
commonly produces. Everything runs locally; no credentials, no external calls.

## Scenario
The Meridian Financial security team inherited a script from a contractor. Before it runs anywhere
near production, your lead asks you to audit it with the same tools used in CI. `data/insecure.py`
contains four common anti-patterns. Your job: identify each one, understand why it matters, and
produce a clean version that passes both `ruff` and `bandit`.

> Everything runs locally against code you own. No authorization issues here.

## Do
1. [ ] `make demo` — read every finding that `ruff` and `bandit` print. For each `bandit` finding,
   note its severity (LOW / MEDIUM / HIGH) and what it flags.
2. [ ] Open `data/insecure.py` in the shell (`make shell`, then `cat data/insecure.py`). Without
   looking up the fix yet: can you spot the four issues just by reading the code?
3. [ ] Create `data/secure.py` — a copy of `insecure.py` with all four anti-patterns fixed:
   - Replace the hardcoded credential with `os.environ.get("API_KEY")`.
   - Replace `subprocess(shell=True, ...)` with a list argument and `shell=False`.
   - Remove the `eval()` call; replace it with an explicit type conversion.
   - Move the secret to a `.env` pattern (just show the `os.environ.get` call; the actual `.env` is gitignored).
4. [ ] Inside the container, run `ruff check data/secure.py` and `bandit -r data/secure.py`. Both
   should exit clean (no errors, no HIGH/MEDIUM findings).
5. [ ] Write `setup.sh` — a three-line shell script that creates a venv, activates it, and installs
   from `requirements.txt`. Run it inside the container to confirm it works.

## Success criteria — you're done when
- [ ] `ruff check data/secure.py` exits 0 (no findings).
- [ ] `bandit -r data/secure.py` shows no HIGH or MEDIUM severity findings.
- [ ] You can explain to a colleague, in one sentence each, why the four original patterns are dangerous.
- [ ] `setup.sh` exists and runs without error.

## Deliverables
`data/secure.py` (the cleaned script) + `setup.sh` (the venv bootstrap). Commit both. Do not
commit `data/insecure.py` changes — the point is the contrast.

## Automate & own it
**Required.** Have a model generate a GitHub Actions workflow that runs `ruff check` and
`bandit -r` over all `.py` files on every pull request. Read every line — pay attention to
whether it pins the action version and whether it runs in the right directory. Commit the workflow
as `.github/workflows/python-quality.yml` next to your deliverables.

## AI acceleration
Use a model to explain *why* each bandit finding is dangerous — it's good at translating finding
codes into plain English. Then ask it to generate the fixed version and compare its output to what
you wrote. Where do they differ? Which is safer? Own the version you understand, not the one you
pasted.

## Connects forward
The clean environment you set up here is the foundation for every subsequent module — modules 02
through 10 all assume a working venv and a linter in the loop. The bandit habit pays off hardest
in module 10, where you review an AI-generated script before trusting it.

## Marketable proof
> "I run ruff and bandit in CI over every Python tool before it touches a production system — I
> know the common anti-patterns cold and I review AI-generated code the same way I'd review a PR."

## Stretch
- Configure `ruff` via `pyproject.toml` to enable additional rule sets (`S` for security, `B` for
  bugbear) and see what new findings appear on `insecure.py`.
- Add `pip-audit` to the workflow to scan `requirements.txt` for known-vulnerable packages.
