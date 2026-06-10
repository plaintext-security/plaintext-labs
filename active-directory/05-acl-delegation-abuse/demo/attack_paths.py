#!/usr/bin/env python3
"""Print the Meridian ACL attack paths (chained ACE edges from a low-priv principal to DA)."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "data/acl-findings.json"
data = json.load(open(path))
for p in data["attack_paths"]:
    print(f'Path: {p["name"]} ({p["total_hops"]} hops)')
    for hop in p["hops"]:
        print(f'  {hop["step"]}. {hop["from"]} --[{hop["edge"]}]--> {hop["to"]} ({hop["technique"]})')
