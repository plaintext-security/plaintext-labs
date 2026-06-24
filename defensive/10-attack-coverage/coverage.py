#!/usr/bin/env python3
"""Map a Sigma rule set to ATT&CK: build a Navigator layer and a gap report.

A pile of detections isn't a strategy. This reads every rule's `attack.tXXXX` tags,
emits a MITRE ATT&CK Navigator layer (upload it to the hosted Navigator to *see*
coverage), and — the point of the module — flags which **priority** techniques your
rules do NOT cover. Coverage is not effectiveness, but you can't even start the
conversation without knowing your gaps.
"""
import glob
import json
import re
import sys

import yaml

TECH = re.compile(r"^attack\.(t\d{4}(?:\.\d{3})?)$", re.IGNORECASE)


def techniques_from_rule(path):
    rule = yaml.safe_load(open(path)) or {}
    found = set()
    for tag in rule.get("tags", []):
        m = TECH.match(str(tag))
        if m:
            found.add(m.group(1).upper())
    return rule.get("title", path), found


def load_priorities(path):
    out = []
    for line in open(path):
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line.upper())
    return out


def main():
    rules = sorted(glob.glob("rules/*.yml"))
    covered = {}
    for path in rules:
        title, techs = techniques_from_rule(path)
        for t in techs:
            covered.setdefault(t, []).append(title)

    print(f"== Coverage from {len(rules)} rules ==")
    for tech in sorted(covered):
        print(f"  {tech}  <- {', '.join(covered[tech])}")

    priorities = load_priorities("priority_techniques.txt")
    gaps = [t for t in priorities if t not in covered]
    print(f"\n== Priority gaps ({len(gaps)} of {len(priorities)} uncovered) ==")
    for t in gaps:
        print(f"  [GAP] {t} — no rule detects this")

    layer = {
        "name": "Plaintext — SOC detection coverage",
        "domain": "enterprise-attack",
        "versions": {"layer": "4.5", "navigator": "4.9.1", "attack": "14"},
        "description": "Generated from the lab's Sigma rule set.",
        "techniques": [
            {"techniqueID": t, "score": 100, "color": "#2e7d32",
             "comment": "; ".join(covered[t])}
            for t in sorted(covered)
        ],
        "gradient": {"colors": ["#ffffff", "#2e7d32"], "minValue": 0, "maxValue": 100},
    }
    with open("navigator_layer.json", "w") as fh:
        json.dump(layer, fh, indent=2)
    print("\nWrote navigator_layer.json — upload it at "
          "https://mitre-attack.github.io/attack-navigator/ to visualise coverage.")
    if gaps:
        print(f"\n[!] {len(gaps)} priority technique(s) uncovered — treat as findings.")


if __name__ == "__main__":
    main()
