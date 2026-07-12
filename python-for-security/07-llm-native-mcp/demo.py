#!/usr/bin/env python3
"""Reference demo for Lab 07 — LLM-Native Python & MCP (offline).

Proves both trust boundaries without calling a real model:
  1. the MCP tool validates its arguments — a valid IP works, a hostile arg is rejected,
  2. the typed-output discipline (what instructor does) accepts a well-formed model
     reply and REJECTS a malformed one — no trusting free text.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))

from pydantic import ValidationError  # noqa: E402

from sift.mcp_server import enrich, enrich_impl, mcp  # noqa: E402
from sift.verdict import parse_model_reply  # noqa: E402

DIVIDER = "─" * 60


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("MCP server")
    registered = enrich is not None and mcp.name == "sift"
    print(f"  FastMCP server {mcp.name!r}; enrich tool registered: {registered}")

    section("1. MCP tool validates the LLM's (untrusted) argument")
    print(f"  enrich('45.83.192.44') -> {enrich_impl('45.83.192.44')}")
    hostile = "1.1.1.1; DROP TABLE alerts"
    try:
        enrich_impl(hostile)
        arg_blocked = False
        print(f"  ✗ hostile arg {hostile!r} ACCEPTED")
    except ValueError:
        arg_blocked = True
        print(f"  ✓ hostile arg {hostile!r} rejected at the tool boundary")

    section("2. Typed LLM output — validate the reply, don't trust it")
    good = '{"severity": "high", "is_true_positive": true, "rationale": "known C2"}'
    v = parse_model_reply(good)
    print(f"  ✓ well-formed reply -> Verdict(severity={v.severity!r}, tp={v.is_true_positive})")
    bad = '{"severity": "VERY BAD", "is_true_positive": "maybe"}'
    try:
        parse_model_reply(bad)
        out_blocked = False
        print("  ✗ malformed reply ACCEPTED")
    except ValidationError:
        out_blocked = True
        print("  ✓ malformed model reply rejected (bad enum + missing field)")

    section("Result")
    ok = registered and arg_blocked and out_blocked
    print("  MCP arg validation + typed LLM output both enforced ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
