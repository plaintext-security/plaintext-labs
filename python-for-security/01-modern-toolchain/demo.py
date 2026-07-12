#!/usr/bin/env python3
"""Reference demo for Lab 01 — Modern Toolchain & Spec-Driven Skeleton.

Proves the three things the migration must hold:
  1. the legacy script still runs,
  2. the migrated `sift` reproduces its output byte-for-byte (strangler-fig),
  3. the ruff gate is clean on the migrated package.
(pyright is part of the full toolchain the learner adds; uv + ruff are exercised here.)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

LAB = Path(__file__).parent
DATA = LAB / "data" / "alerts.json"
REF = LAB / "sift_reference"

DIVIDER = "─" * 60


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("Toolchain versions (the modern default)")
    for tool in (["uv", "--version"], ["ruff", "--version"]):
        r = subprocess.run(tool, capture_output=True, text=True)
        print(f"  {r.stdout.strip() or r.stderr.strip()}")

    section("1. Legacy alert_parse.py")
    legacy = subprocess.run(
        [sys.executable, str(LAB / "alert_parse.py"), str(DATA)],
        capture_output=True, text=True,
    ).stdout.rstrip()
    print(legacy)

    section("2. Migrated sift reproduces the output (strangler-fig)")
    sys.path.insert(0, str(REF))
    from sift.parse import format_summary  # reference migrated code

    migrated = format_summary(json.loads(DATA.read_text())).rstrip()
    print(migrated)
    identical = migrated == legacy
    print(f"\n  byte-for-byte identical: {'✓' if identical else '✗'}")

    section("3. ruff gate on the migrated package")
    ruff = subprocess.run(
        ["ruff", "check", str(REF)], capture_output=True, text=True
    )
    ruff_clean = ruff.returncode == 0
    print("  " + (ruff.stdout.strip() or "All checks passed!"))
    print(f"  ruff gate clean: {'✓' if ruff_clean else '✗'}")

    section("Result")
    ok = identical and ruff_clean
    print("  migration preserved behaviour AND passes the gate ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
