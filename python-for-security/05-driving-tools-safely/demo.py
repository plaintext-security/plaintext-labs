#!/usr/bin/env python3
"""Reference demo for Lab 05 — Driving Tools Safely (real Suricata EVE JSON).

sift drives external tools and parses a dissector's structured output. This demo:
  1. the shell=True wrapper EXECUTES a command hidden in an attacker-shaped indicator
     (a marker file appears) — exactly the copilot's `shell=True` bug,
  2. the shell=False + validated wrapper REFUSES the same payload at the boundary,
  3. parses Suricata's EVE JSON (the dissector's STRUCTURED output) into typed `alert`
     events through sift's pydantic union — unknown event types quarantined, not scraped,
  4. derives indicators from REAL EVE fields (the alert five-tuple) and enriches them safely.

The committed `data/eve.json` is real EVE output from the 2024-07-30 "You dirty rat!"
(STRRAT) infection pcap — so Suricata itself is NOT needed in this container; we parse its
recorded dissection as the driven tool's structured output.
"""
from __future__ import annotations

import sys
from pathlib import Path

LAB = Path(__file__).parent
sys.path.insert(0, str(LAB / "sift_reference"))

from sift.tools import (  # noqa: E402
    enrich_safe,
    enrich_unsafe,
    indicators_from_alerts,
    parse_eve,
    validate_indicator,
)

DIVIDER = "─" * 64
MARKER = Path("/tmp/pwned_by_injection")
EVE = LAB / "data" / "eve.json"


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    MARKER.unlink(missing_ok=True)

    # Parse the dissector's structured output FIRST, so the indicator we drive tools
    # with is DERIVED from a real EVE field (an alert's dest_ip) — not an invented value.
    alerts, quarantined = parse_eve(EVE)
    indicators = indicators_from_alerts(alerts)
    real_ip = indicators[0]  # a genuine src_ip/dest_ip from a real alert's five-tuple

    section("1. shell=True wrapper + attacker-shaped indicator (THE BUG)")
    payload = f"{real_ip}; touch {MARKER}"  # the alert field an attacker can shape
    print(f"  indicator (from a real alert, tampered): {payload!r}")
    enrich_unsafe(payload)
    injected = MARKER.exists()
    print(f"  injected `touch` executed: {injected}  <- command injection")
    MARKER.unlink(missing_ok=True)

    section("2. shell=False + validated wrapper, same payload")
    try:
        enrich_safe(payload)
        blocked = False
        print("  ✗ payload was ACCEPTED (should not happen!)")
    except ValueError:
        blocked = True
        print("  ✓ rejected at the boundary (not a valid IP) — no shell, no injection")

    section("3. Parse the dissector's STRUCTURED output (Suricata EVE JSON)")
    for a in alerts[:5]:
        print(
            f"  ✓ AlertEvent(sev={a.alert.severity}, {a.src_ip}→{a.dest_ip}, "
            f"sid={a.alert.signature_id}: {a.alert.signature})"
        )
    print(
        f"  parsed {len(alerts)} typed alert events; quarantined {quarantined} "
        f"non-alert/unknown lines (never scraped, never fatal)"
    )

    section("4. Enrich indicators DERIVED from real EVE fields, safely")
    validated = [validate_indicator(ip) for ip in indicators]
    sample = validated[0]
    out = enrich_safe(sample).strip()
    works = out == f"enriching {sample}"
    print(f"  {len(validated)} indicators derived from alert five-tuples (src_ip/dest_ip)")
    print(f"  enrich_safe({sample!r}) -> {out!r}  ({'✓' if works else '✗'})")

    section("Result")
    ok = (
        injected
        and blocked
        and works
        and len(alerts) > 0
        and quarantined > 0
        and len(indicators) > 0
    )
    print(
        "  injection reproduced then blocked; dissector output parsed to typed events; "
        "real-field indicators enriched safely ✓"
        if ok
        else "  DEMO FAILED — see above"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
