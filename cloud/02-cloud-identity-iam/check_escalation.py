#!/usr/bin/env python3
"""
check_escalation.py — prove an IAM policy closes the PassRole escalation.

Enumeration (cloudfox) finds that dev-alice can escalate: `iam:PassRole` on `*`
plus `ec2:RunInstances` lets her launch an instance carrying MeridianEC2AdminRole
(AdministratorAccess) and read its credentials. This closes the loop — it evaluates
a fixed set of "can dev-alice do X on Y?" assertions against a policy document and
reports PASS/FAIL, so you can *prove* your remediation.

The intended loop:
  1. run it on the original policy   -> the escalation assertions show ALLOW = FAIL
  2. author a fixed policy (scope iam:PassRole to a specific non-admin role)
  3. run it on your fixed policy      -> escalation closed, legitimate access intact = PASS

Exit 0 only when every assertion holds, so it also works as a CI gate on IAM policy.

Usage:
  python check_escalation.py data/dev-alice-policy.json          # original (expect FAILs)
  python check_escalation.py data/dev-alice-fixed-policy.json    # your fix (aim for all PASS)
"""
import argparse
import json
import re
import sys

ADMIN_ROLE = "arn:aws:iam::000000000001:role/MeridianEC2AdminRole"
ANY_ROLE = "arn:aws:iam::000000000001:role/SomeOtherRole"
DEV_BUCKET_OBJ = "arn:aws:s3:::meridian-dev-data/reports.csv"

# (description, action, resource, expected-allowed)
MATRIX = [
    ("dev-alice can PassRole the EC2 ADMIN role (the escalation)", "iam:PassRole", ADMIN_ROLE, False),
    ("dev-alice can PassRole *any* role (wildcard escalation)",    "iam:PassRole", ANY_ROLE,   False),
    ("dev-alice retains ec2:DescribeInstances (legitimate)",       "ec2:DescribeInstances", "*", True),
    ("dev-alice retains S3 read on its data (legitimate)",         "s3:GetObject", DEV_BUCKET_OBJ, True),
]


def _glob(pattern: str) -> re.Pattern:
    """IAM wildcard (only '*' and '?') -> regex, case-insensitive."""
    out = []
    for ch in pattern:
        if ch == "*":
            out.append(".*")
        elif ch == "?":
            out.append(".")
        else:
            out.append(re.escape(ch))
    return re.compile("^" + "".join(out) + "$", re.IGNORECASE)


def _as_list(v):
    return v if isinstance(v, list) else [v]


def _matches(values, target) -> bool:
    return any(_glob(v).match(target) for v in values)


def is_allowed(policy: dict, action: str, resource: str) -> bool:
    """Simplified IAM evaluation: explicit Deny wins, else any matching Allow. (No conditions/SCPs.)"""
    allow = False
    for stmt in policy.get("Statement", []):
        actions = _as_list(stmt.get("Action", []))
        resources = _as_list(stmt.get("Resource", []))
        if _matches(actions, action) and _matches(resources, resource):
            if stmt.get("Effect") == "Deny":
                return False
            allow = True
    return allow


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("policy_file", help="an IAM policy document (JSON)")
    args = ap.parse_args()

    with open(args.policy_file) as f:
        policy = json.load(f)

    print(f"Escalation check: {args.policy_file}\n")
    failures = 0
    for desc, action, resource, expected in MATRIX:
        allowed = is_allowed(policy, action, resource)
        ok = allowed == expected
        verdict = "ALLOW" if allowed else "DENY "
        want = "ALLOW" if expected else "DENY"
        if not ok:
            failures += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {verdict} (want {want:<5}) {desc}")

    print()
    if failures:
        print(f"{failures} assertion(s) FAILED — the PassRole escalation is still open "
              "(or you broke legitimate access).")
        return 1
    print("All assertions PASS — escalation closed, legitimate access intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
