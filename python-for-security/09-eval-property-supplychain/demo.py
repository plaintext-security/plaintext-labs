#!/usr/bin/env python3
"""Reference demo for Lab 09 — Eval Harness, Property Tests & Supply Chain.

  1. Score the triage classifier on a HELD-OUT corpus → precision/recall scorecard,
     with a regression GATE (fail if recall < baseline).
  2. (via pytest) property tests fuzz the pydantic validator — reject ALL malformed input.
  3. Supply-chain gate: verify the lockfile's hash matches what we pinned (offline
     stand-in for `pip-audit` + hash-locked install).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

LAB = Path(__file__).parent
sys.path.insert(0, str(LAB / "sift_reference"))
from sift.classify import classify  # noqa: E402
from sift.evalharness import RECALL_BASELINE, score  # noqa: E402

DIVIDER = "─" * 60


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("1. Eval harness — scorecard on the held-out corpus")
    s = score(classify)
    print(f"  confusion: tp={s['tp']} fp={s['fp']} fn={s['fn']} tn={s['tn']}")
    print(f"  precision={s['precision']:.2f}  recall={s['recall']:.2f}")
    gate_ok = s["recall"] >= RECALL_BASELINE
    print(f"  regression gate (recall >= {RECALL_BASELINE:.2f}): {'PASS ✓' if gate_ok else 'FAIL ✗'}")

    section("2. Supply-chain gate — lockfile hash matches the pin")
    lockfile = LAB / "requirements.lock"
    expected = (LAB / "requirements.lock.sha256").read_text().strip()
    actual = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    supply_ok = actual == expected
    print(f"  lockfile sha256 matches pinned digest: {'✓' if supply_ok else '✗ TAMPERED'}")
    print("  (in production: pip-audit + a hash-locked install — see lab.md)")

    section("Result")
    ok = gate_ok and supply_ok
    print("  eval gate green + supply chain verified — now run `pytest` for property tests ✓"
          if ok else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
