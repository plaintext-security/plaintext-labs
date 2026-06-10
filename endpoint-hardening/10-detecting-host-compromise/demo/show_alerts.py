#!/usr/bin/env python3
"""Print the Meridian payroll-server alert feed (level, timestamp, ATT&CK id, description)."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "data/alerts.json"
with open(path) as f:
    alerts = json.load(f)
print(f"Total alerts: {len(alerts)}")
print()
for a in alerts:
    level = a["rule"]["level"]
    desc = a["rule"]["description"]
    ts = a["timestamp"]
    mitre = a.get("mitre", {}).get("id", "N/A")
    print(f"  [{level:2}] {ts} | ATT&CK: {mitre:15} | {desc}")
