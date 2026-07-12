"""Migrated parse logic — same behaviour as the legacy alert_parse.py, now typed.

Module 02 replaces the plain dict with a validated pydantic model; here the point is
only that the migration preserves behaviour (the strangler-fig move), typed and lintable.
"""
from __future__ import annotations

from collections import Counter


def summarize(alerts: list[dict[str, object]]) -> list[tuple[str, int]]:
    """Count alerts by source, most-frequent first (ties broken by name)."""
    counts: Counter[str] = Counter(str(a.get("source", "unknown")) for a in alerts)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def format_summary(alerts: list[dict[str, object]]) -> str:
    lines = ["Alert summary by source:"]
    lines += [f"  {src}: {n}" for src, n in summarize(alerts)]
    return "\n".join(lines)
