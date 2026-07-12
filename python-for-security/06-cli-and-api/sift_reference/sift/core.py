"""The shared core — pydantic models + triage logic. Both surfaces import THIS.

The copilot's mistake is writing the logic twice (once behind the CLI, once behind
the API). Instead the models and `triage()` are the single core; `cli.py` and
`api.py` are thin adapters over it, so they can never drift.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Verdict = Literal["benign", "suspicious", "malicious"]


class Indicator(BaseModel):
    kind: Literal["ipv4", "domain", "sha256"]
    value: str


class TriageResult(BaseModel):
    indicator: Indicator
    verdict: Verdict
    score: int


def triage(indicator: Indicator) -> TriageResult:
    """Deterministic toy scoring — the point is that ONE function serves both surfaces."""
    score = sum(ord(c) for c in indicator.value) % 100
    verdict: Verdict = "malicious" if score > 66 else "suspicious" if score > 33 else "benign"
    return TriageResult(indicator=indicator, verdict=verdict, score=score)
