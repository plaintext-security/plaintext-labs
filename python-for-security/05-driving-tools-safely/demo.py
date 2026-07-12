#!/usr/bin/env python3
"""Reference demo for Lab 05 — Driving Tools Safely.

Proves the vulnerability and the fix with a benign injected command (touch a
marker file):
  1. the shell=True wrapper EXECUTES the injected command (marker appears),
  2. the shell=False + validated wrapper REFUSES the same payload,
  3. the safe wrapper still works on a legitimate indicator.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))
from sift.tools import enrich_safe, enrich_unsafe  # noqa: E402

DIVIDER = "─" * 60
MARKER = Path("/tmp/pwned_by_injection")
PAYLOAD = f"1.1.1.1; touch {MARKER}"


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    MARKER.unlink(missing_ok=True)

    section("1. shell=True wrapper + injection payload (THE BUG)")
    print(f"  payload: {PAYLOAD!r}")
    enrich_unsafe(PAYLOAD)
    injected = MARKER.exists()
    print(f"  injected `touch` executed: {injected}  <- command injection")
    MARKER.unlink(missing_ok=True)

    section("2. shell=False + validated wrapper, same payload")
    try:
        enrich_safe(PAYLOAD)
        blocked = False
        print("  ✗ payload was ACCEPTED (should not happen!)")
    except ValueError:
        blocked = True
        print("  ✓ rejected at the boundary (not a valid indicator) — no shell, no injection")

    section("3. safe wrapper on a legitimate indicator")
    out = enrich_safe("1.1.1.1").strip()
    works = out == "enriching 1.1.1.1"
    print(f"  output: {out!r}  ({'✓' if works else '✗'})")

    section("Result")
    ok = injected and blocked and works
    print("  injection reproduced, then blocked by shell=False + validation ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
