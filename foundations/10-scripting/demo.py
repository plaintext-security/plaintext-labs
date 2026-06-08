#!/usr/bin/env python3
"""
Scripting Lab — demo + reference run.

Shows what topips.py should produce, then explains the key Python
building blocks: re, collections.Counter, argparse, edge cases.

Usage: python3 demo.py
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

DATA_DIR = Path("/lab/data") if Path("/lab/data").exists() else Path("data")
DIVIDER = "─" * 64


def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"[{title}]")
    print(DIVIDER)


def run_reference() -> collections.Counter:
    log = DATA_DIR / "ssh_auth.log"
    pattern = re.compile(r"Failed password for \S+ from (\S+) port")
    counts: collections.Counter = collections.Counter()
    unparsed = 0

    for line in log.read_text().splitlines():
        m = pattern.search(line)
        if m:
            counts[m.group(1)] += 1
        elif "Failed" in line:
            unparsed += 1
    return counts


def main() -> None:
    print("=" * 64)
    print("Meridian Financial — Scripting Lab Demo")
    print("=" * 64)
    print()
    print("Goal: build topips.py that reads an SSH auth log and ranks")
    print("source IPs by failed-login count. This demo shows the target output.")

    section("Expected output — top failed-login IPs")
    counts = run_reference()
    print()
    print(f"  {'IP':<22}  {'Count':>5}")
    print(f"  {'-'*22}  {'-'*5}")
    for ip, count in counts.most_common():
        bar = "█" * count
        print(f"  {ip:<22}  {count:>5}  {bar}")

    section("Key Python building blocks")
    print("""
  import re
  import collections

  pattern = re.compile(r"Failed password for \\S+ from (\\S+) port")
  #                                                   ↑ capturing group = the IP

  counts = collections.Counter()

  for line in open("ssh_auth.log"):
      m = pattern.search(line)
      if m:
          counts[m.group(1)] += 1   # m.group(1) = first capturing group = IP

  for ip, count in counts.most_common():
      print(f"{ip:<20}  {count}")
""")

    section("Edge cases — your script must handle these")
    print()
    edge_cases = [
        ("Malformed line",      "Nov 15 07:00:00 bastion sshd: garbled",
         "No match → skip (don't crash)"),
        ("IPv6 address",        "Failed password for root from ::1 port 22",
         "Pattern should still match \\S+"),
        ("Valid line, no IP",   "Failed password for invalid user foo",
         "No port clause → no match → skip"),
    ]
    for name, line, expected in edge_cases:
        pattern = re.compile(r"Failed password for \S+ from (\S+) port")
        m = pattern.search(line)
        result = f"matched: {m.group(1)!r}" if m else "no match (skipped)"
        print(f"  Case: {name}")
        print(f"    Line:     {line}")
        print(f"    Expected: {expected}")
        print(f"    Got:      {result}")
        print()

    section("Reference implementation")
    print()
    print("  The answer key is in data/topips_reference.py.")
    print("  Do NOT look at it until you've written your own version.")
    print()
    print("  Run the reference: python3 data/topips_reference.py data/ssh_auth.log")
    print("  With threshold:    python3 data/topips_reference.py data/ssh_auth.log --threshold 3")
    print("  As JSON:           python3 data/topips_reference.py data/ssh_auth.log --json")

    section("Deliverable")
    print()
    print("  Commit: topips.py + a one-paragraph README explaining:")
    print("    - What the script does")
    print("    - How to run it")
    print("    - One limitation you'd fix next")
    print()
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
