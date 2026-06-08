#!/usr/bin/env python3
"""Teaching harness: parse messy sshd auth logs and normalise to a common schema.

The point of this module is the discipline the bridge preaches: a pipeline that
*runs* is not a pipeline that *works*. So this harness doesn't just emit parsed
events — it reports the **parse rate** and prints every line it could NOT parse,
because those silent drops are where a detection quietly misses.

In production you'd express this in Vector (VRL) or a Logstash/Elastic ingest
pipeline; the lab has you rebuild this normalisation there. This stdlib version is
the worked example and the reference output to match.
"""
import json
import re
import sys

# One sshd auth line -> typed fields. Anything that doesn't match is surfaced,
# not silently dropped.
SSHD = re.compile(
    r"^(?P<ts>\w{3}\s+\d+\s[\d:]+)\s+"
    r"(?P<host>\S+)\s+sshd\[\d+\]:\s+"
    r"(?P<outcome>Accepted|Failed)\s+(?P<method>\w+)\s+for\s+"
    r"(?:invalid user\s+)?(?P<user>\S+)\s+from\s+"
    r"(?P<srcip>\d{1,3}(?:\.\d{1,3}){3})\s+port\s+(?P<port>\d+)"
)


def normalise(line):
    """Return an ECS-ish dict for an sshd auth line, or None if it doesn't match."""
    m = SSHD.match(line)
    if not m:
        return None
    return {
        "@timestamp": m["ts"],
        "host.name": m["host"],
        "event.category": "authentication",
        "event.action": f"ssh_{m['method'].lower()}",
        "event.outcome": "success" if m["outcome"] == "Accepted" else "failure",
        "user.name": m["user"],
        "source.ip": m["srcip"],
        "source.port": int(m["port"]),
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/auth_sample.txt"
    lines = [l.rstrip("\n") for l in open(path) if l.strip()]

    parsed, unparsed = [], []
    for line in lines:
        event = normalise(line)
        (parsed if event else unparsed).append((line, event))

    print("== Normalised events ==")
    for _, event in parsed:
        print("  " + json.dumps(event))

    print("\n== Could NOT parse (do not let these vanish silently) ==")
    for raw, _ in unparsed:
        print("  " + raw)

    total = len(lines)
    rate = len(parsed) / total * 100 if total else 0
    print(f"\nParse rate: {len(parsed)}/{total} lines ({rate:.0f}%).")
    print("A green pipeline is not a correct pipeline — account for every unparsed line.")


if __name__ == "__main__":
    main()
