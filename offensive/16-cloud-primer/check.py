#!/usr/bin/env python3
"""
Cloud primer — pre-flight check and walkthrough guide.

Validates that the external targets (flaws.cloud) are reachable and prints
the lab walkthrough structure.  This is not a container lab — the target is
the intentionally vulnerable cloud environment at flaws.cloud.

Usage:
    python3 check.py        # validate connectivity + print walkthrough
    python3 check.py --aws  # also check AWS CLI is configured
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.error
import urllib.request

DIVIDER = "─" * 64


def check_url(url: str, label: str, timeout: float = 6.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            ok = r.status < 400
            status = r.status
    except urllib.error.HTTPError as e:
        ok = True  # flaws.cloud first-level S3 may 403/404 — still reachable
        status = e.code
    except Exception as e:
        print(f"  ✗ {label}: {e}")
        return False
    print(f"  {'✓' if ok else '⚠'} {label}: HTTP {status}")
    return ok


def check_cli(cmd: str, label: str) -> bool:
    path = shutil.which(cmd)
    if path:
        print(f"  ✓ {label}: {path}")
        return True
    else:
        print(f"  ✗ {label}: not installed — install with pip/brew/apt")
        return False


def demo() -> int:
    print("=" * 64)
    print("Cloud Primer — External Lab Pre-flight Check")
    print("Targets: flaws.cloud  |  Optional: CloudGoat + Pacu")
    print("=" * 64)

    # ── Connectivity check ────────────────────────────────────────────────
    print("\n[1] Connectivity to external targets")
    print()
    targets = [
        ("http://flaws.cloud/", "flaws.cloud (level 1 S3 bucket)"),
        ("https://aws.amazon.com/free/", "AWS free-tier console"),
    ]
    all_ok = all(check_url(url, label) for url, label in targets)

    # ── CLI tools check ────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[2] Tools (optional — needed for CloudGoat/Pacu path)")
    print()
    tools = [
        ("aws",    "AWS CLI"),
        ("python3","Python 3 (for Pacu)"),
        ("git",    "git (for CloudGoat)"),
        ("terraform", "Terraform (for CloudGoat deployment)"),
    ]
    for cmd, label in tools:
        check_cli(cmd, label)

    # ── AWS CLI config check ──────────────────────────────────────────────
    if "--aws" in sys.argv:
        print(f"\n{DIVIDER}")
        print("[3] AWS CLI configuration")
        print()
        r = subprocess.run(["aws", "sts", "get-caller-identity"], capture_output=True, text=True)
        if r.returncode == 0:
            import json
            ident = json.loads(r.stdout)
            print(f"  ✓ AWS credentials configured:")
            print(f"    Account: {ident.get('Account')}")
            print(f"    ARN:     {ident.get('Arn')}")
        else:
            print(f"  ✗ AWS CLI not configured: {r.stderr.strip()[:100]}")
            print("    Run: aws configure  (or set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)")

    # ── Walkthrough ────────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Lab] flaws.cloud walkthrough structure")
    print()
    print("  flaws.cloud is an intentionally-misconfigured AWS environment")
    print("  by Scott Piper (Summit Route).  Each level reveals one real cloud flaw.")
    print()
    levels = [
        ("Level 1", "Public S3 bucket — list/read without credentials"),
        ("Level 2", "S3 bucket auth via leaked AWS key in bucket contents"),
        ("Level 3", "Git history reveals credentials (AWS key in old commit)"),
        ("Level 4", "EC2 snapshot exposed; mount it to find credentials"),
        ("Level 5", "SSRF → EC2 metadata → IAM role credentials (Capital One pattern)"),
        ("Level 6", "Security audit via IAM policy analysis"),
    ]
    for level, desc in levels:
        print(f"  {level:<10}  {desc}")
    print()
    print("  Start: http://flaws.cloud/")
    print()

    # ── CloudGoat alternative ─────────────────────────────────────────────
    print(DIVIDER)
    print("[Alt] CloudGoat — deployable vulnerable AWS lab (requires AWS account)")
    print()
    print("  Scenario: 'cloud_breach_s3' — realistic S3 data breach chain")
    print("  Setup:")
    print("    git clone https://github.com/RhinoSecurityLabs/cloudgoat")
    print("    cd cloudgoat && pip install -r requirements.txt")
    print("    ./cloudgoat.py config profile default")
    print("    ./cloudgoat.py create cloud_breach_s3")
    print()
    print("  Teardown (important — avoids AWS charges):")
    print("    ./cloudgoat.py destroy cloud_breach_s3")
    print()

    # ── Pacu quick reference ──────────────────────────────────────────────
    print(DIVIDER)
    print("[Tool] Pacu — AWS exploitation framework quick reference")
    print()
    print("  Install: pip install pacu")
    print("  Start:   pacu")
    print()
    pacu_modules = [
        ("aws__enum_account",        "Enumerate account details and active regions"),
        ("iam__enum_users_roles_policies", "Enumerate IAM users, roles, policies"),
        ("iam__privesc_scan",         "Scan for privilege escalation paths"),
        ("s3__enum_bucket_permissions", "Check S3 bucket permissions"),
        ("ec2__enum",                 "Enumerate EC2 instances, security groups"),
    ]
    print(f"  {'Module':<40}  Purpose")
    print(f"  {'─'*40}  {'─'*30}")
    for module, purpose in pacu_modules:
        print(f"  {module:<40}  {purpose}")

    print(f"\n{'=' * 64}")
    print("Pre-flight complete — proceed to http://flaws.cloud/ to start")
    print(f"{'=' * 64}\n")
    return 0


if __name__ == "__main__":
    sys.exit(demo())
