#!/usr/bin/env python3
"""Pretty-print an osquery deb_packages inventory read as JSON from stdin."""
import json
import sys

rows = json.load(sys.stdin)
print(f"Installed packages (first 15 of {len(rows)} total):")
for r in rows:
    print(f"  {r['name']:30} {r['version']}")
