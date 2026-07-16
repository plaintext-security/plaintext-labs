"""Driving external tools safely, and parsing a dissector's structured output.

Two jobs sift does in this module:

1. **Drive tools without opening a shell.** In triage the indicator comes from an alert
   an attacker may have shaped, so `shell=True` string interpolation is remote code
   execution. The fix: validate at the boundary, then `shell=False` with an argument
   LIST — there is no shell to inject into. (`echo` stands in for the real tool here —
   `nmap`/`whois`/`suricata` are driven the exact same way.)

2. **Treat a dissector's output as STRUCTURED data.** Suricata emits EVE JSON, not free
   text. We parse each line into a typed event through sift's pydantic union and derive
   indicators from real fields (`src_ip`/`dest_ip`) — never scrape stdout, never invent an
   indicator schema.
"""
from __future__ import annotations

import ipaddress
import json
import subprocess
from pathlib import Path

from pydantic import ValidationError

from .models import EVE_ADAPTER, AlertEvent


def enrich_unsafe(indicator: str) -> str:
    """THE BUG — never do this. An attacker-shaped `indicator` is command injection.

    A shell interprets ``; | $() ` `` — so the interpolated `indicator` can run arbitrary
    commands. This is exactly the wrapper a copilot ships by default.
    """
    return subprocess.run(
        f"echo enriching {indicator}", shell=True, capture_output=True, text=True
    ).stdout


def validate_indicator(indicator: str) -> str:
    """Boundary check: an IP indicator must BE an IP. Rejects shell metacharacters.

    Fed indicators DERIVED from real EVE fields (an alert's `src_ip`/`dest_ip`), so a
    genuine endpoint passes and a tampered one (`1.2.3.4; touch …`) is refused before any
    tool sees it.
    """
    ipaddress.ip_address(indicator)  # ValueError on anything that isn't an IP
    return indicator


def enrich_safe(indicator: str) -> str:
    """Validate, then pass as a single list argument — no shell to inject into."""
    validate_indicator(indicator)
    return subprocess.run(
        ["echo", "enriching", indicator], shell=False, capture_output=True, text=True
    ).stdout


def parse_eve(path: str | Path) -> tuple[list[AlertEvent], int]:
    """Parse a dissector's structured output (Suricata EVE JSON) into typed events.

    Each line is one event. We parse through the discriminated union, so an `alert` line
    becomes a typed `AlertEvent` and any event_type with no union member (`dns`/`flow`/`tls`/…)
    — or a truncated/non-JSON line — is QUARANTINED: never scraped, never silently trusted,
    never fatal. Returns ``(typed alerts, quarantined count)``.
    """
    alerts: list[AlertEvent] = []
    quarantined = 0
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = EVE_ADAPTER.validate_python(json.loads(line))
        except (json.JSONDecodeError, ValidationError):
            quarantined += 1  # unknown event_type or malformed line -> quarantine
            continue
        alerts.append(event)  # the union currently only yields AlertEvent
    return alerts, quarantined


def indicators_from_alerts(alerts: list[AlertEvent]) -> list[str]:
    """Derive enrichable indicators from real EVE fields — the alert five-tuple endpoints
    (`src_ip`/`dest_ip`) — not from an invented ``Indicator{kind, value}`` schema."""
    seen: dict[str, None] = {}
    for a in alerts:
        for ip in (str(a.src_ip), str(a.dest_ip)):
            seen.setdefault(ip, None)
    return list(seen)
