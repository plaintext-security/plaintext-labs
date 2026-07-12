#!/usr/bin/env python3
# Legacy alert parser — THIS is the script you migrate in Lab 01.
# It works, it's in "production", and it has: no types, no lockfile, no tests,
# and a stale requirements.txt. Do NOT rewrite it from scratch — wrap it, gate
# it in CI, then refactor behind the green build (strangler-fig).
import json
import sys


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/alerts.json"
    with open(path) as f:
        alerts = json.load(f)

    counts = {}
    for a in alerts:
        src = a.get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1

    print("Alert summary by source:")
    for src, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {src}: {n}")


if __name__ == "__main__":
    main()
