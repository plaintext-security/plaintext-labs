#!/usr/bin/env python3
"""Summarise a grype JSON report (read from stdin) as a CVE-severity breakdown."""
import json
import sys

data = json.load(sys.stdin)
counts = {}
for m in data.get("matches", []):
    sev = m["vulnerability"]["severity"]
    counts[sev] = counts.get(sev, 0) + 1
print("CVE severity breakdown:")
for sev in ["Critical", "High", "Medium", "Low", "Negligible"]:
    if sev in counts:
        print(f"  {sev}: {counts[sev]}")
