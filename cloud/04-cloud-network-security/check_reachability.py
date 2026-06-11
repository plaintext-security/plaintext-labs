#!/usr/bin/env python3
"""
check_reachability.py — prove a Security Group ruleset against a reachability matrix.

Auditing finds the bad rule; this closes the loop. It evaluates a fixed set of
"who must / must not reach whom" assertions against a security-groups JSON file
(same shape as `aws ec2 describe-security-groups`) and reports PASS/FAIL. The
intended loop:

  1. run it on the original (bad) groups  -> the over-broad paths show ALLOW = FAIL
  2. author a corrected groups file (close SSH/Postgres to the world)
  3. run it on your fixed file            -> bad paths now DENY, good paths still ALLOW = PASS

Exit 0 only when every assertion holds, so it doubles as a CI gate on network config.

Usage:
  python check_reachability.py data/account/meridian/describe-security-groups.json
  python check_reachability.py data/account/meridian/security-groups-fixed.json
"""
import argparse
import ipaddress
import json
import sys

# An arbitrary public host used to test "the internet" — clearly outside any
# private/bastion range, so a rule scoped to a bastion CIDR correctly denies it.
INTERNET = "203.0.113.50"  # TEST-NET-3

# The reachability requirements for Meridian's three-tier app.
# source: an IP string ("the internet") OR a security-group id (group-referenced rule).
# expected: True = must be reachable, False = must be denied.
MATRIX = [
    ("internet -> ALB :443 (public web — legitimate)",        INTERNET,      "sg-00000001", 443, True),
    ("internet -> app :22  (SSH — must be closed)",           INTERNET,      "sg-00000002", 22,  False),
    ("internet -> app :8080 (only the ALB should reach app)", INTERNET,      "sg-00000002", 8080, False),
    ("ALB -> app :8080 (legitimate app traffic)",             "sg-00000001", "sg-00000002", 8080, True),
    ("internet -> db  :5432 (Postgres — must be closed)",     INTERNET,      "sg-00000003", 5432, False),
    ("app -> db :5432 (legitimate DB traffic)",               "sg-00000002", "sg-00000003", 5432, True),
]


def _port_match(perm: dict, port: int) -> bool:
    if perm.get("IpProtocol") == "-1":
        return True
    if perm.get("IpProtocol") != "tcp":
        return False
    lo, hi = perm.get("FromPort"), perm.get("ToPort")
    return lo is not None and hi is not None and lo <= port <= hi


def can_reach(groups: dict, source: str, target_sg: str, port: int) -> bool:
    """True if `source` (an IP or an sg-id) is allowed to TARGET_SG on PORT by ingress rules."""
    sg = groups.get(target_sg)
    if sg is None:
        return False
    src_is_ip = not source.startswith("sg-")
    src_ip = ipaddress.ip_address(source) if src_is_ip else None

    for perm in sg.get("IpPermissions", []):
        if not _port_match(perm, port):
            continue
        if src_is_ip:
            for rng in perm.get("IpRanges", []):
                if src_ip in ipaddress.ip_network(rng["CidrIp"]):
                    return True
        else:
            for pair in perm.get("UserIdGroupPairs", []):
                if pair.get("GroupId") == source:
                    return True
    return False


def load_groups(path: str) -> dict:
    with open(path) as f:
        data = json.load(f)
    return {sg["GroupId"]: sg for sg in data["SecurityGroups"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sg_file", help="security-groups JSON (describe-security-groups shape)")
    args = ap.parse_args()

    groups = load_groups(args.sg_file)
    print(f"Reachability check: {args.sg_file}\n")
    failures = 0
    for desc, source, target, port, expected in MATRIX:
        allowed = can_reach(groups, source, target, port)
        ok = allowed == expected
        verdict = "ALLOW" if allowed else "DENY "
        want = "ALLOW" if expected else "DENY"
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"  [{mark}] {verdict} (want {want:<5}) {desc}")

    print()
    if failures:
        print(f"{failures} assertion(s) FAILED — the network is not least-privilege yet.")
        return 1
    print("All reachability assertions PASS — bad paths denied, required paths intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
