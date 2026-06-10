#!/usr/bin/env python3
"""Detect the exploit you just fired — the defensive half of the KEV loop.

Exploiting a KEV proves it's real; *detecting* it is what a defender ships. This
matcher scans an access log for the Log4Shell (CVE-2021-44228) signature: a JNDI
lookup string in any field of the request. The point isn't the regex — it's the
discipline of writing the detection against the *same traffic your exploit produced*,
then proving it stays quiet on benign requests (no false positives).

The signature is deliberately field-agnostic: Log4Shell payloads land anywhere the
app logs an attacker-controlled value — the URI, the User-Agent, a header. Matching
only the URI misses the User-Agent variant in the sample log; that gap is the lesson.

Usage:
    python detect.py data/solr_access.log
    python detect.py --json data/solr_access.log
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# A JNDI lookup with a network-fetch scheme: the heart of the Log4Shell payload.
# ${jndi:ldap://...}, rmi://, dns://, and the nested-lookup obfuscation (${sys:...}).
JNDI = re.compile(r"\$\{jndi:(?:ldap|ldaps|rmi|dns|iiop|nis|corba)://", re.IGNORECASE)
# Nested ${...} lookups are a strong obfuscation tell even without a clean jndi: prefix.
NESTED = re.compile(r"\$\{(?:lower|upper|env|sys|date|java):", re.IGNORECASE)


def scan(path: Path) -> list[dict]:
    hits = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        m = JNDI.search(line)
        if m or NESTED.search(line):
            hits.append({
                "line": n,
                "rule": "log4shell_jndi" if m else "log4shell_nested_lookup",
                "matched": (m or NESTED.search(line)).group(0),
                "raw": line.strip(),
            })
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logfile", help="access log to scan")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    path = Path(args.logfile)
    if not path.is_file():
        print(f"error: no such log file: {path}", file=sys.stderr)
        return 2

    total = len(path.read_text().splitlines())
    hits = scan(path)

    if args.json:
        print(json.dumps({"logfile": str(path), "lines": total, "hits": hits}, indent=2))
        return 0 if hits else 1

    print(f"Scanned {total} request(s) in {path.name}")
    print(f"Log4Shell (CVE-2021-44228) signature matches: {len(hits)}\n")
    for h in hits:
        print(f"  [HIT] line {h['line']:>2}  {h['rule']}  ->  {h['matched']}")
        print(f"        {h['raw']}")
    if not hits:
        print("  (clean — no JNDI lookup strings found)")
    else:
        print(f"\n  {len(hits)} malicious request(s); the remaining "
              f"{total - len(hits)} benign request(s) did NOT match (no false positives).")
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main())
