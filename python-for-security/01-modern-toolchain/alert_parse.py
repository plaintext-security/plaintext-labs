#!/usr/bin/env python3
# Legacy alert parser — THIS is the script you migrate in Lab 01.
# It works, it's in "production", and it has: no types, no lockfile, no tests,
# and a stale requirements.txt. Do NOT rewrite it from scratch — wrap it, gate
# it in CI, then refactor behind the green build (strangler-fig).
#
# It reads a Suricata eve.json (newline-delimited JSON, one event per line),
# keeps the alert-type events, and counts them by rule signature.
import json
import sys


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/eve.json"

    counts = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if event.get("event_type") != "alert":
                continue
            sig = event.get("alert", {}).get("signature", "unknown")
            counts[sig] = counts.get(sig, 0) + 1

    print("Alert summary by signature:")
    for sig, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {sig}: {n}")


if __name__ == "__main__":
    main()
