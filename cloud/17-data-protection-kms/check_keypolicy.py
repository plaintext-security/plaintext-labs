#!/usr/bin/env python3
"""
check_keypolicy.py — prove a KMS key policy enforces separation of duties.

A KMS key policy is a *resource* policy: it names principals and the kms actions
they may take on the key. The control that matters is separation — key
administrators (who can disable/delete/rotate the key) must NOT be able to decrypt
data, and key users (who encrypt/decrypt) must NOT be able to administer the key.
A loose policy that grants `kms:*` to the app role collapses both into one
principal, so one compromised app credential can both read all data AND destroy
the key.

This evaluates a fixed set of "(principal, action)" assertions against a key
policy and reports PASS/FAIL. Loop: run it on the original (loose) policy to see
the separation FAIL, author a fixed policy, run it again to prove separation holds.

Usage:
  python check_keypolicy.py data/key-policy.json          # original (expect FAILs)
  python check_keypolicy.py data/key-policy-fixed.json    # your fix (aim for all PASS)
"""
import argparse
import json
import re
import sys

ADMIN = "arn:aws:iam::000000000000:role/MeridianKeyAdmin"
APP = "arn:aws:iam::000000000000:role/MeridianAppRole"

# (description, principal, action, expected-allowed)
MATRIX = [
    ("key admin can administer the key (ScheduleKeyDeletion)", ADMIN, "kms:ScheduleKeyDeletion", True),
    ("key admin CANNOT decrypt data (separation of duties)",   ADMIN, "kms:Decrypt",            False),
    ("app role can decrypt data (its job)",                    APP,   "kms:Decrypt",            True),
    ("app role CANNOT administer the key (separation)",        APP,   "kms:PutKeyPolicy",       False),
    ("nobody is granted decrypt via a wildcard principal",     "*",   "kms:Decrypt",            False),
]


def _glob(pattern: str) -> re.Pattern:
    out = []
    for ch in pattern:
        out.append(".*" if ch == "*" else ("." if ch == "?" else re.escape(ch)))
    return re.compile("^" + "".join(out) + "$", re.IGNORECASE)


def _as_list(v):
    return v if isinstance(v, list) else [v]


def _principal_matches(stmt_principal, principal: str) -> bool:
    if stmt_principal == "*":
        return True
    if isinstance(stmt_principal, dict):
        vals = []
        for v in stmt_principal.values():
            vals.extend(_as_list(v))
    else:
        vals = _as_list(stmt_principal)
    # We test specific role ARNs (or "*"). A statement principal of "*" matches anyone;
    # otherwise require an exact ARN match (KMS principals are ARNs, not globs).
    return any(p == "*" or p == principal for p in vals)


def is_allowed(policy: dict, principal: str, action: str) -> bool:
    """Simplified KMS key-policy evaluation: explicit Deny wins, else any matching Allow."""
    allow = False
    for stmt in policy.get("Statement", []):
        if not _principal_matches(stmt.get("Principal"), principal):
            continue
        actions = _as_list(stmt.get("Action", []))
        if not any(_glob(a).match(action) for a in actions):
            continue
        if stmt.get("Effect") == "Deny":
            return False
        allow = True
    return allow


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("policy_file", help="a KMS key policy document (JSON)")
    args = ap.parse_args()

    with open(args.policy_file) as f:
        policy = json.load(f)

    print(f"Key-policy separation check: {args.policy_file}\n")
    failures = 0
    for desc, principal, action, expected in MATRIX:
        allowed = is_allowed(policy, principal, action)
        ok = allowed == expected
        verdict = "ALLOW" if allowed else "DENY "
        want = "ALLOW" if expected else "DENY"
        if not ok:
            failures += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {verdict} (want {want:<5}) {desc}")

    print()
    if failures:
        print(f"{failures} assertion(s) FAILED — key admins and key users are not separated.")
        return 1
    print("All assertions PASS — separation of duties holds on the key.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
