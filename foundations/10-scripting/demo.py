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


def reference_log() -> Path:
    """Prefer the REAL loghub OpenSSH log (run `make fetch-data`); fall back to
    the small committed sample if the fetch hasn't run yet."""
    real = DATA_DIR / "OpenSSH_2k.log"
    return real if real.exists() else DATA_DIR / "ssh_auth.log"


def run_reference() -> collections.Counter:
    log = reference_log()
    pattern = re.compile(r"Failed password for (?:invalid user )?\S+ from (\S+) port")
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
    print("Scripting Lab Demo — rank brute-force source IPs")
    print("=" * 64)
    print()
    print("Goal: build topips.py that reads an SSH auth log and ranks")
    print("source IPs by failed-login count. This demo shows the target output.")

    log = reference_log()
    src = ("REAL loghub OpenSSH dataset" if log.name == "OpenSSH_2k.log"
           else "committed sample (run `make fetch-data` for the real log)")
    section("Expected output — top failed-login IPs")
    print(f"\n  Source: {src} — data/{log.name}")
    counts = run_reference()
    print()
    print(f"  {'IP':<22}  {'Count':>5}")
    print(f"  {'-'*22}  {'-'*5}")
    top = counts.most_common(15)
    busiest = top[0][1] if top else 1
    for ip, count in top:
        bar = "█" * max(1, round(40 * count / busiest))  # scaled, capped at 40 cols
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
