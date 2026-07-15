#!/usr/bin/env python3
"""Reference demo for Lab 02 — Parse, Don't Validate.

Shows the before/after that IS the lesson:
  1. the trusting starter (sift_starter/) works on the clean feed,
  2. on the messy feed it either accepts garbage or crashes deep in triage —
     it never *rejects* anything,
  3. the typed boundary (sift_reference/) rejects every malformed record at
     the door, with a field-level reason,
  4. secrets load via pydantic-settings, not hardcoding.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LAB = Path(__file__).parent
sys.path.insert(0, str(LAB / "sift_reference"))
sys.path.insert(0, str(LAB / "sift_starter"))

import triage as starter  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from sift.models import Alert  # noqa: E402
from sift.settings import Settings  # noqa: E402

DIVIDER = "─" * 60


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    valid = json.loads((LAB / "data" / "alerts.json").read_text())
    malformed = json.loads((LAB / "data" / "alerts_malformed.json").read_text())

    section("1. The starter on the CLEAN feed — looks fine")
    for a in starter.triage(json.loads(json.dumps(valid))):
        print(f"  [{a['severity']:>8}] #{a['id']} {a['source']}: {a['indicator']['value']}")
    print(f"  triaged {len(valid)} alerts — 'it works'")

    section("2. The starter on the MESSY feed — trusts garbage or dies, never rejects")
    crashed = None
    try:
        starter.triage(json.loads(json.dumps(malformed)))
        print("  ✗ full feed triaged without error (should not happen!)")
    except Exception as e:  # noqa: BLE001 — the crash is the point
        crashed = e
        print("  ✗ one poisoned record killed the whole run, three calls deep:")
        print(f"      {type(e).__name__}: {e}")
    accepted = 0
    for r in malformed:
        try:
            starter.triage([json.loads(json.dumps(r))])
            accepted += 1
            print(f"  ✗ id={r.get('id')} ACCEPTED as-is (bad value trusted downstream)")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ id={r.get('id')} crashed in triage: {type(e).__name__}")
    print(f"  accepted {accepted}/{len(malformed)} malformed records; rejected: 0")

    section("3. The typed boundary — every malformed record REJECTED at the door")
    alerts = [Alert.model_validate(r) for r in valid]
    for a in alerts:
        print(f"  ✓ Alert(id={a.id}, source={a.source!r}, {a.indicator.kind}={a.indicator.value!r})")
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
    print(f"  parsed {len(alerts)} valid, rejected {rejected}/{len(malformed)} malformed")

    section("4. Secrets via pydantic-settings (from the environment)")
    s = Settings()
    print(f"  log_level={s.log_level!r}; vt_api_key set: {bool(s.vt_api_key)} (loaded from SIFT_* env)")

    section("Result")
    ok = (
        len(alerts) == len(valid)
        and all_rejected
        and crashed is not None
        and accepted >= 4
    )
    print("  the boundary rejects what the starter trusted or died on ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
