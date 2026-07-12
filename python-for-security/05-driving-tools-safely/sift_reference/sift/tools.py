"""Wrapping external tools — the safe way and the copilot's dangerous default.

In a triage tool the indicator comes from an alert an attacker may have shaped, so
`shell=True` string interpolation is remote code execution. The fix: validate at the
boundary, then `shell=False` with an argument LIST — no shell to inject into.
"""
from __future__ import annotations

import ipaddress
import subprocess


def enrich_unsafe(indicator: str) -> str:
    """THE BUG — never do this. Attacker-controlled `indicator` → command injection."""
    # A shell interprets ; | $() ` — so `indicator` can run arbitrary commands.
    return subprocess.run(
        f"echo enriching {indicator}", shell=True, capture_output=True, text=True
    ).stdout


def validate_indicator(indicator: str) -> str:
    """Boundary check: an IP indicator must BE an IP. Rejects shell metacharacters."""
    ipaddress.ip_address(indicator)  # raises ValueError on anything that isn't an IP
    return indicator


def enrich_safe(indicator: str) -> str:
    """Validate, then pass as a single argument via a list — no shell involved."""
    validate_indicator(indicator)
    return subprocess.run(
        ["echo", "enriching", indicator], shell=False, capture_output=True, text=True
    ).stdout
