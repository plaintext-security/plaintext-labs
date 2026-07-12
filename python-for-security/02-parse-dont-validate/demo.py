#!/usr/bin/env python3
"""Reference demo for Lab 02 — Parse, Don't Validate.

Proves the boundary works:
  1. valid alerts parse into typed `Alert` models,
  2. malformed alerts are REJECTED with a clear reason (not silently accepted),
  3. secrets load via pydantic-settings, not hardcoding.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).parent
sys.path.insert(0, str(LAB / "sift_reference"))

from pydantic import ValidationError  # noqa: E402
from sift.models import Alert  # noqa: E402
from sift.settings import Settings  # noqa: E402

DIVIDER = "─" * 60


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("1. Valid alerts → typed Alert models")
    valid = json.loads((LAB / "data" / "alerts.json").read_text())
    alerts = [Alert.model_validate(r) for r in valid]
    for a in alerts:
        print(f"  ✓ Alert(id={a.id}, source={a.source!r}, {a.indicator.kind}={a.indicator.value!r})")
    print(f"  parsed {len(alerts)} valid alerts")

    section("2. Malformed alerts → REJECTED at the boundary")
    malformed = json.loads((LAB / "data" / "alerts_malformed.json").read_text())
    rejected = 0
    for r in malformed:
        try:
            Alert.model_validate(r)
            print(f"  ✗ id={r.get('id')} was ACCEPTED (should not happen!)")
        except ValidationError as e:
            err = e.errors()[0]
            print(f"  ✓ id={r.get('id')} rejected: {err['loc']} — {err['msg']}")
            rejected += 1
    all_rejected = rejected == len(malformed)
    print(f"  rejected {rejected}/{len(malformed)} malformed records")

    section("3. Secrets via pydantic-settings (from the environment)")
    s = Settings()
    print(f"  log_level={s.log_level!r}; vt_api_key set: {bool(s.vt_api_key)} (loaded from SIFT_* env)")

    section("Result")
    ok = len(alerts) == len(valid) and all_rejected
    print("  boundary validation works — valid in, malformed out ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
