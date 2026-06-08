#!/usr/bin/env python3
"""
Reference implementation of topips.py — the learner builds their own version.

This is the answer key. Students should NOT look at this until they've
written and tested their own version against the same log file.

Usage:
    python3 topips_reference.py data/ssh_auth.log
    python3 topips_reference.py data/ssh_auth.log --threshold 3
    python3 topips_reference.py data/ssh_auth.log --json
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

FAILED_RE = re.compile(r"Failed password for \S+ from (\S+) port")


def parse(path: Path) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    unparsed = 0
    for line in path.read_text().splitlines():
        m = FAILED_RE.search(line)
        if m:
            counts[m.group(1)] += 1
        elif "Failed" in line:
            unparsed += 1
    if unparsed:
        print(f"# note: {unparsed} 'Failed' line(s) did not match the pattern",
              file=sys.stderr)
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description="Rank source IPs by failed SSH logins")
    ap.add_argument("logfile", nargs="?", default="data/ssh_auth.log")
    ap.add_argument("--threshold", "-t", type=int, default=0,
                    help="Only show IPs with count >= threshold")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    counts = parse(Path(args.logfile))
    results = [(ip, c) for ip, c in counts.most_common() if c >= args.threshold]

    if args.json:
        print(json.dumps([{"ip": ip, "count": c} for ip, c in results], indent=2))
    else:
        print(f"{'IP':<22}  {'Count':>5}")
        print("-" * 30)
        for ip, count in results:
            print(f"{ip:<22}  {count:>5}")


if __name__ == "__main__":
    main()
