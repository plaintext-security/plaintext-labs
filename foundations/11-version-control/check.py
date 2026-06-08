#!/usr/bin/env python3
"""
Version Control lab — git workflow guide + gitleaks demo.

Validates git is installed and prints the portfolio-repo setup guide,
including secret-hygiene checks and pre-commit hook setup.

Usage:
    python3 check.py          # check git + print guide
    python3 check.py --scan   # scan current directory for secrets with gitleaks (if installed)
"""
from __future__ import annotations

import shutil
import subprocess
import sys

DIVIDER = "─" * 64


def check_git() -> bool:
    if not shutil.which("git"):
        print("  ✗  git not found — install git first")
        return False
    r = subprocess.run(["git", "--version"], capture_output=True, text=True)
    print(f"  ✓  {r.stdout.strip()}")
    return True


def check_gitleaks() -> bool:
    if shutil.which("gitleaks"):
        r = subprocess.run(["gitleaks", "version"], capture_output=True, text=True)
        print(f"  ✓  gitleaks: {r.stdout.strip() or r.stderr.strip()}")
        return True
    print("  ○  gitleaks not installed (optional — needed for Stretch goal)")
    print("     Install: https://github.com/gitleaks/gitleaks#installing")
    return False


def print_guide() -> None:
    print("""
══════════════════════════════════════════════════════════════
Lab 11 — Build a Portfolio Repo the Right Way
══════════════════════════════════════════════════════════════

GOAL: A clean, public GitHub repo — home for all curriculum deliverables
— with a .gitignore that keeps secrets and lab artifacts out.

──────────────────────────────────────────────────────────────
STEP 1 — Create the repo
──────────────────────────────────────────────────────────────
  $ mkdir security-portfolio && cd security-portfolio
  $ git init
  $ git checkout -b main

──────────────────────────────────────────────────────────────
STEP 2 — .gitignore (copy + extend this)
──────────────────────────────────────────────────────────────
  # Secrets and credentials
  *.pem  *.key  *.p12  *.pfx
  .env  .env.*  secrets.txt  credentials.json
  *_rsa  *_dsa  *_ecdsa  *_ed25519  authorized_keys

  # Lab artifacts
  *.pcap  *.pcapng  *.cap
  *.log   *.evtx   *.mem   *.vmem
  *.img   *.iso    *.ova   *.ovf
  site/   __pycache__/   .venv/   node_modules/

  # OS noise
  .DS_Store  Thumbs.db  .idea/  .vscode/

Verify: create a file matching a pattern and confirm git ignores it:
  $ echo "secret_key=abc123" > .env
  $ git status    # .env should NOT appear

──────────────────────────────────────────────────────────────
STEP 3 — First commit
──────────────────────────────────────────────────────────────
  $ echo "# Security Portfolio" > README.md
  $ git add README.md .gitignore
  $ git commit -m "Initial commit: README and .gitignore"

──────────────────────────────────────────────────────────────
STEP 4 — Push to GitHub
──────────────────────────────────────────────────────────────
  $ gh repo create security-portfolio --public   # using GitHub CLI
  # OR create on github.com, then:
  $ git remote add origin https://github.com/<you>/security-portfolio.git
  $ git push -u origin main

──────────────────────────────────────────────────────────────
STEP 5 — Branch, PR, and merge (the collaboration loop)
──────────────────────────────────────────────────────────────
  $ git checkout -b feat/module-01
  # make changes …
  $ git add <files> && git commit -m "Add breach analysis (module 01)"
  $ git push origin feat/module-01
  $ gh pr create --title "Add module 01 breach analysis"
  # Merge on GitHub (or: gh pr merge)

──────────────────────────────────────────────────────────────
STEP 6 — Pre-commit hook to block secrets
──────────────────────────────────────────────────────────────
Option A — gitleaks pre-commit hook:
  $ cat > .git/hooks/pre-commit << 'EOF'
  #!/bin/sh
  gitleaks protect --staged --no-banner || { echo "gitleaks: secrets detected — commit blocked"; exit 1; }
  EOF
  $ chmod +x .git/hooks/pre-commit

Option B — simple grep hook (no extra tools):
  $ cat > .git/hooks/pre-commit << 'EOF'
  #!/bin/sh
  if git diff --cached | grep -qiE '(password|secret|api.key|private.key).*=.*[A-Za-z0-9]{8,}'; then
    echo "pre-commit: possible secret detected — review staged changes"; exit 1
  fi
  EOF
  $ chmod +x .git/hooks/pre-commit

Test it:
  $ echo "AWS_SECRET=AKIAIOSFODNN7EXAMPLE" > test_secret.txt
  $ git add test_secret.txt && git commit -m "test"
  # Should be BLOCKED by the hook

──────────────────────────────────────────────────────────────
KEY POINT: why deleting a committed secret isn't enough
──────────────────────────────────────────────────────────────
Once a secret is in git history, every clone of the repo has it —
even after a later commit deletes it. You must use BFG Repo Cleaner
or 'git filter-repo' to rewrite history, AND rotate the secret
immediately (assume it's already been harvested).

The lesson: never commit secrets in the first place.
""")


def run_gitleaks_scan() -> None:
    if not shutil.which("gitleaks"):
        print("gitleaks not installed — install from https://github.com/gitleaks/gitleaks")
        return
    print("\n[gitleaks scan of current directory]\n")
    r = subprocess.run(
        ["gitleaks", "detect", "--source", ".", "--no-banner"],
        capture_output=False, text=True
    )
    if r.returncode == 0:
        print("\n  ✓ No secrets detected")
    else:
        print(f"\n  ✗ Secrets found — rotate them before committing")


def main() -> None:
    if "--scan" in sys.argv:
        run_gitleaks_scan()
        return

    print("=" * 64)
    print("Lab 11 — Version Control Checks")
    print("=" * 64)
    print()
    check_git()
    check_gitleaks()
    print_guide()


if __name__ == "__main__":
    main()
