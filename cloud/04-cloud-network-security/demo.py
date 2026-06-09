#!/usr/bin/env python3
"""
demo.py — Worked example for Lab 04 (Cloud Network Security).

1. Parses the bundled Security Group JSON and reports 0.0.0.0/0 ingress findings.
2. Runs the VPC flow log analyzer against the bundled log.

Run via: python demo.py   (or  make demo)
"""

import json
import subprocess
import sys
from pathlib import Path


def check_security_groups(sg_file: str) -> int:
    """Print Security Group findings and return count of misconfigurations."""
    with open(sg_file) as f:
        data = json.load(f)

    findings = 0
    severity_map = {
        "meridian-alb-sg": "INFO",   # intentional: public ALB
        "meridian-app-sg": "HIGH",   # SSH to 0.0.0.0/0 on app tier
        "meridian-db-sg":  "CRITICAL",  # database port to 0.0.0.0/0
    }

    print("Security Groups with 0.0.0.0/0 ingress:")
    for sg in data["SecurityGroups"]:
        for perm in sg["IpPermissions"]:
            for r in perm.get("IpRanges", []):
                if r.get("CidrIp") == "0.0.0.0/0":
                    port = perm.get("FromPort", "all")
                    proto = perm.get("IpProtocol", "?")
                    sev = severity_map.get(sg["GroupName"], "MEDIUM")
                    desc = r.get("Description", "")
                    print(f"  [{sev}] {sg['GroupName']} ({sg['GroupId']})")
                    print(f"         Port {port}/{proto} open to 0.0.0.0/0")
                    if desc:
                        print(f"         Note: {desc}")
                    if sev in ("HIGH", "CRITICAL"):
                        findings += 1
    return findings


def main():
    base = Path(__file__).parent

    print("=" * 60)
    print("Lab 04 — Cloud Network Security: Worked Demo")
    print("=" * 60)
    print()

    print("=== 1. Security Group Audit ===")
    sg_file = base / "data/account/meridian/describe-security-groups.json"
    sg_findings = check_security_groups(str(sg_file))
    print(f"\n  Total HIGH/CRITICAL findings: {sg_findings}")
    print()

    print("=== 2. VPC Flow Log Anomaly Analysis ===")
    flow_log = base / "data/vpc-flow-logs.log"
    result = subprocess.run(
        [sys.executable, str(base / "analyze_flows.py"), str(flow_log)],
        capture_output=False,
    )
    print()

    total = sg_findings + (1 if result.returncode != 0 else 0)
    print("=" * 60)
    if total > 0:
        print(f"Demo complete. {sg_findings} Security Group misconfiguration(s) + flow log anomalies found.")
        print("See lab.md for the full investigation steps.")
    else:
        print("Demo complete. No findings (unexpected — check data files).")


if __name__ == "__main__":
    main()
