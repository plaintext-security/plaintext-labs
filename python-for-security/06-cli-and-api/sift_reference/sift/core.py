"""The shared core — pydantic models + triage logic. Both surfaces import THIS.

The copilot's mistake is writing the logic twice (once behind the CLI, once behind
the API). Instead the models and `triage()` are the single core; `cli.py` and
`api.py` are thin adapters over it, so they can never drift.

The INPUT model is canonical Suricata **EVE JSON** — a real `alert` event
(`AlertEvent`), not an invented indicator schema. EVE carries many envelope fields;
we pin the ones we depend on and `extra="ignore"` the rest (you never `extra="forbid"`
a real feed — it would reject every genuine line). The OUTPUT model is `TriageResult`.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress

Verdict = Literal["benign", "suspicious", "malicious"]


class EveBase(BaseModel):
    # EVE has many fields; ignore the rest, pin what matters.
    model_config = ConfigDict(extra="ignore")
    timestamp: datetime
    flow_id: int | None = None
    src_ip: IPvAnyAddress | None = None
    dest_ip: IPvAnyAddress | None = None
    src_port: int | None = None
    dest_port: int | None = None
    proto: str | None = None


class AlertDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")
    signature: str
    signature_id: int                  # e.g. an ET Open sid
    category: str
    severity: int = Field(ge=1, le=3)  # Suricata alert severity is 1..3
    gid: int | None = None
    rev: int | None = None


class AlertEvent(EveBase):
    event_type: Literal["alert"]
    alert: AlertDetails


# The union GROWS as dissector stretches add members (DnsEvent, HttpEvent, ...).
# For M06 it has the single `alert` member; both surfaces validate against it.
EveEvent = Annotated[Union[AlertEvent], Field(discriminator="event_type")]


class TriageResult(BaseModel):
    verdict: Verdict
    score: int


def triage(event: AlertEvent) -> TriageResult:
    """Deterministic scoring off the validated EVE alert.

    Suricata severity is 1 (highest priority) .. 3 (lowest). We map it to a 0..100
    score so a SOAR playbook and an analyst read the same number. The point of the
    lab is that ONE function serves both surfaces — the exact scoring is incidental.
    """
    score = {1: 100, 2: 60, 3: 20}[event.alert.severity]
    verdict: Verdict = (
        "malicious" if score >= 80 else "suspicious" if score >= 40 else "benign"
    )
    return TriageResult(verdict=verdict, score=score)
