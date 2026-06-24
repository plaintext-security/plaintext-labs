#!/usr/bin/env python3
"""
flat-walk.py — re-walk PATH-001 against the FLAT baseline (no waves applied) and prove it
reaches Domain Admin. This is the t=0 "before" proof: on the brownfield domain a Domain
Admin (tallen) logs on interactively to a Tier 2 Finance workstation, so the credential is
harvestable and the path runs to the end. Reuses the same hop-evaluation logic as
wave-check.py so the "before" and "after" verdicts are scored identically.

  python3 flat-walk.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from importlib import import_module

wc = import_module("wave-check")  # reuse hop_is_open / check_attack_dead


def main():
    baseline = wc.load("baseline.json")
    path = wc.load("path-001.json")

    print("=" * 70)
    print("PATH-001 re-walk on the FLAT brownfield domain (t=0, no tiering applied)")
    print("Domain:", path["meta"]["domain"])
    print("=" * 70)
    res = wc.check_attack_dead(baseline, path, targeted_hop=3)
    for h in res["hops"]:
        state = "OPEN  (attacker can take it)" if h["open"] else "closed"
        print(f"  step {h['step']:>1}  [{h['edge']:<24}]  {state}")
    print("-" * 70)
    print(f"  Path reaches DOMAIN ADMINS? {res['path_reaches_domain_admin']}")
    print(f"  Credential-harvest hop (3) open? {res['targeted_hop_open']}  "
          "(tallen logs on interactively to FIN-WS01 -> DA cred harvestable)")
    print("=" * 70)
    if res["path_reaches_domain_admin"]:
        print("BEFORE: PATH-001 is OPEN end to end. This is what the migration must kill.")
        return 0
    print("UNEXPECTED: flat baseline does not reach DA — check the fixtures.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
