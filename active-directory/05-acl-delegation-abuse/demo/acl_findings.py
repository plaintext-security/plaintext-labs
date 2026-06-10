#!/usr/bin/env python3
"""Print the Meridian ACL misconfiguration findings (severity, principal, edge, target)."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "data/acl-findings.json"
data = json.load(open(path))
for f in data["acl_misconfigurations"]:
    print(f'[{f["severity"]}] {f["principal"]} --[{f["ace_type"]}]--> {f["target"]}')
    print(f'         {f["attack_description"][:100]}...')
    print()
