"""Migrated parse logic — same behaviour as the legacy alert_parse.py, now typed.

The input is a list of Suricata EVE events (each a decoded eve.json line). We keep
the alert-type events and count them by rule signature. Module 02 replaces the plain
dicts with validated pydantic models; here the point is only that the migration
preserves behaviour (the strangler-fig move), typed and lintable.
"""
from __future__ import annotations

from collections import Counter


def summarize(events: list[dict[str, object]]) -> list[tuple[str, int]]:
    """Count alert events by signature, most-frequent first (ties broken by name)."""
    counts: Counter[str] = Counter()
    for event in events:
        if event.get("event_type") != "alert":
            continue
        alert = event.get("alert")
        sig = alert.get("signature", "unknown") if isinstance(alert, dict) else "unknown"
        counts[str(sig)] += 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def format_summary(events: list[dict[str, object]]) -> str:
    lines = ["Alert summary by signature:"]
    lines += [f"  {sig}: {n}" for sig, n in summarize(events)]
    return "\n".join(lines)
