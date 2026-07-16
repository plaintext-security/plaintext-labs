#!/usr/bin/env python3
"""Reference demo for Lab 07 — LLM-Native Python & MCP (offline).

Drives the real Suricata EVE corpus (data/eve.json — a STRRAT RAT infection) and proves
both trust boundaries without calling a real model:
  1. the MCP tools validate their arguments with the canonical EVE pydantic models —
     `enrich` over a real IP indicator, `triage` over a whole `alert` record; a hostile
     IP arg and an out-of-Suricata-range record are both rejected at the tool boundary,
  2. the typed-output discipline (what instructor does) accepts a well-formed model
     reply and REJECTS a malformed one — no trusting free text.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))

from pydantic import ValidationError  # noqa: E402

from sift.mcp_server import enrich, enrich_impl, mcp, triage, triage_impl  # noqa: E402
from sift.models import load_alerts, malicious_ips  # noqa: E402
from sift.verdict import parse_model_reply  # noqa: E402

DIVIDER = "─" * 60


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("MCP server + real EVE corpus")
    registered = enrich is not None and triage is not None and mcp.name == "sift"
    alerts = load_alerts()
    bad = malicious_ips(alerts)
    corpus_ok = len(alerts) > 0 and len(bad) > 0
    print(f"  FastMCP server {mcp.name!r}; enrich+triage tools registered: {registered}")
    print(f"  parsed {len(alerts)} real AlertEvents from data/eve.json")
    print(f"  derived {len(bad)} known-bad C2 indicator(s): {sorted(bad)}")

    # A real indicator derived from a validated AlertEvent — the C2 the alerts flag.
    c2 = sorted(bad)[0]

    section("1a. enrich validates the LLM's (untrusted) IP argument")
    print(f"  enrich({c2!r}) -> {enrich_impl(c2)}")
    print(f"  enrich('208.95.112.1') -> {enrich_impl('208.95.112.1')}")
    hostile = "1.1.1.1; DROP TABLE alerts"
    try:
        enrich_impl(hostile)
        arg_blocked = False
        print(f"  ✗ hostile arg {hostile!r} ACCEPTED")
    except ValueError:
        arg_blocked = True
        print(f"  ✓ hostile arg {hostile!r} rejected at the tool boundary")

    section("1b. triage validates a whole EVE alert record (AlertEvent)")
    # A genuine alert straight from the corpus round-trips through the tool.
    real = next(e for e in alerts if str(e.dest_ip) in bad)
    print(f"  triage(real STRRAT alert) -> {triage_impl(real.model_dump(mode='json'))}")
    # Canon §1.3: alert.severity=5 is out of Suricata's 1..3 range -> rejected.
    poisoned = real.model_dump(mode="json")
    poisoned["alert"]["severity"] = 5
    try:
        triage_impl(poisoned)
        record_blocked = False
        print("  ✗ out-of-range record (severity=5) ACCEPTED")
    except ValidationError:
        record_blocked = True
        print("  ✓ out-of-range record (alert.severity=5) rejected at the tool boundary")

    section("2. Typed LLM output — validate the reply, don't trust it")
    good = '{"severity": "high", "is_true_positive": true, "rationale": "known STRRAT C2"}'
    v = parse_model_reply(good)
    print(f"  ✓ well-formed reply -> Verdict(severity={v.severity!r}, tp={v.is_true_positive})")
    bad_reply = '{"severity": "VERY BAD", "is_true_positive": "maybe"}'
    try:
        parse_model_reply(bad_reply)
        out_blocked = False
        print("  ✗ malformed reply ACCEPTED")
    except ValidationError:
        out_blocked = True
        print("  ✓ malformed model reply rejected (bad enum + missing field)")

    section("Result")
    ok = registered and corpus_ok and arg_blocked and record_blocked and out_blocked
    print("  MCP arg validation (IP + AlertEvent) + typed LLM output all enforced ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
