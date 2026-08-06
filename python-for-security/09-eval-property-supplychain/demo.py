#!/usr/bin/env python3
"""Reference demo for Lab 09 — Eval Harness, Property Tests & Supply Chain.

  1. Score the triage classifier on a HELD-OUT corpus of REAL Suricata `alert` events
     (evals/holdout.jsonl) → precision/recall scorecard, with a regression GATE on recall
     (the metric that matters: a missed true positive is a missed intrusion).
  2. (via pytest) property tests fuzz the canonical EVE boundary (AlertEvent / the EveEvent
     union) with EVE-shaped inputs — proving it is total: parse OR ValidationError, nothing else.
  3. Supply-chain gate: verify the lockfile's hash matches what we pinned (offline stand-in for
     `pip-audit` + a hash-locked install).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

LAB = Path(__file__).parent
sys.path.insert(0, str(LAB / "sift_reference"))
from sift.classify import triage  # noqa: E402
from sift.evalharness import PRECISION_FLOOR, RECALL_BASELINE, score  # noqa: E402

DIVIDER = "─" * 60


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("1. Eval harness — scorecard on the held-out REAL Suricata alerts")
    s = score(triage)
    print(f"  held-out alerts scored: {int(s['n'])}  (evals/holdout.jsonl — never tuned against)")
    print(f"  confusion: tp={s['tp']} fp={s['fp']} fn={s['fn']} tn={s['tn']}")
    print(f"  precision={s['precision']:.2f}  recall={s['recall']:.2f}  (positive class = true_positive)")
    recall_ok = s["recall"] >= RECALL_BASELINE
    precision_ok = s["precision"] >= PRECISION_FLOOR
    print(f"  regression gate (recall >= {RECALL_BASELINE:.2f}): {'PASS ✓' if recall_ok else 'FAIL ✗'}")
    print(f"  precision floor (>= {PRECISION_FLOOR:.2f}):        {'PASS ✓' if precision_ok else 'FAIL ✗'}")
    print("  note: the rule MISSES the info-level external-IP lookup that was the RAT's recon —")
    print("        an honest false negative, and exactly why we gate on recall.")

    section("2. Supply-chain gate — lockfile hash matches the pin")
    lockfile = LAB / "requirements.lock"
    expected = (LAB / "requirements.lock.sha256").read_text().strip()
    actual = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    supply_ok = actual == expected
    print(f"  lockfile sha256 matches pinned digest: {'✓' if supply_ok else '✗ TAMPERED'}")
    print("  (in production: pip-audit + a hash-locked install — see lab.md)")

    section("Result")
    ok = recall_ok and precision_ok and supply_ok
    print("  eval gate green + supply chain verified — now run `pytest` for property tests ✓"
          if ok else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
