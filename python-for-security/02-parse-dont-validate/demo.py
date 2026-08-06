#!/usr/bin/env python3
"""Reference demo for Lab 02 — Parse, Don't Validate (real Suricata EVE JSON).

Shows the before/after that IS the lesson, on real `eve.json` (newline-delimited events):
  1. the trusting starter (sift_starter/) works on the clean feed,
  2. on the messy feed it trusts garbage or dies three calls deep — and a single
     truncated line takes out the whole load. It never *rejects* anything,
  3. the typed boundary (sift_reference/) turns each line into a typed `AlertEvent`
     or refuses it: a JSON-decode failure is quarantined, a malformed event is
     rejected with a field-level reason,
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
from sift.models import AlertEvent  # noqa: E402
from sift.settings import Settings  # noqa: E402

DIVIDER = "─" * 64


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def raw_lines(name: str) -> list[str]:
    return [ln for ln in (LAB / "data" / name).read_text().splitlines() if ln.strip()]


def main() -> int:
    clean = raw_lines("eve.json")
    messy = raw_lines("eve_malformed.json")

    section("1. The starter on the CLEAN eve.json — looks fine")
    clean_events = [json.loads(ln) for ln in clean]
    for e in starter.triage(clean_events):
        print(f"  [sev {e['alert']['severity']}] {e['src_ip']}→{e['dest_ip']}: "
              f"{e['alert']['signature']}")
    print(f"  triaged {len(clean_events)} alert events — 'it works'")

    section("2. The starter on the MESSY feed — trusts garbage or dies, never rejects")
    load_died = None
    try:
        starter.load_events(str(LAB / "data" / "eve_malformed.json"))
        print("  ✗ full feed loaded without error (should not happen!)")
    except Exception as e:  # noqa: BLE001 — the truncated line killing the load is the point
        load_died = e
        print(f"  ✗ one truncated line killed the whole load: {type(e).__name__}")
    accepted = crashed = 0
    for ln in messy:
        try:
            obj = json.loads(ln)
            starter.triage([obj])
            accepted += 1
            print(f"  ✗ flow={obj.get('flow_id')} ACCEPTED as-is (bad value trusted downstream)")
        except Exception as e:  # noqa: BLE001
            crashed += 1
            print(f"  ✗ a messy line crashed the starter: {type(e).__name__}")
    print(f"  accepted {accepted} malformed lines, crashed on {crashed}; deliberately rejected: 0")

    section("3. The typed boundary — every messy line QUARANTINED or REJECTED at the door")
    events = [AlertEvent.model_validate(json.loads(ln)) for ln in clean]
    for a in events:
        print(f"  ✓ AlertEvent(sev={a.alert.severity}, {a.src_ip}→{a.dest_ip}, "
              f"sid={a.alert.signature_id})")
    handled = 0
    for ln in messy:
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            handled += 1
            print("  ✓ quarantined: line is not valid JSON (truncated write)")
            continue
        try:
            AlertEvent.model_validate(obj)
            print(f"  ✗ flow={obj.get('flow_id')} was ACCEPTED (should not happen!)")
        except ValidationError as e:
            err = e.errors()[0]
            handled += 1
            print(f"  ✓ flow={obj.get('flow_id')} rejected: {err['loc']} — {err['msg']}")
    print(f"  parsed {len(events)} valid, handled {handled}/{len(messy)} messy lines")

    section("4. Secrets via pydantic-settings (from the environment)")
    s = Settings()
    print(f"  log_level={s.log_level!r}; vt_api_key set: {bool(s.vt_api_key)} (loaded from SIFT_* env)")

    section("Result")
    ok = (
        len(events) == len(clean)
        and handled == len(messy)
        and load_died is not None
        and accepted >= 2
    )
    print("  the boundary rejects/quarantines what the starter trusted or died on ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
