"""Typed Suricata EVE JSON models (the M02 substrate `sift enrich` builds on).

`sift` ingests **Suricata EVE JSON** — newline-delimited JSON, one event per line,
keyed by `event_type`. Real EVE carries many envelope fields (`community_id`,
`in_iface`, `app_proto`, `tx_id`, `pkt_src`, …); we DON'T `extra="forbid"` a real
feed (that would reject every genuine line). We pin and constrain the fields we
depend on and `extra="ignore"` the rest — that judgment is the point.

The enrichable indicators are **derived from real EVE fields**, not invented: the
unique `src_ip` / `dest_ip` off the validated `alert` events in `eve.json`. There
is no `Indicator{kind, value}` invented schema.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, TypeAdapter


class EveBase(BaseModel):
    model_config = ConfigDict(extra="ignore")  # EVE has many fields; pin what matters
    timestamp: str
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


_ALERT_ADAPTER = TypeAdapter(AlertEvent)


def load_alerts(path: str | Path) -> list[AlertEvent]:
    """Parse an ``eve.json`` and return only the validated ``alert`` events.

    Non-`alert` lines (dns/tls/flow/…) are skipped here — the dissector stretches
    grow the union to cover them; the core enricher works off alerts. A line that
    claims ``event_type: "alert"`` but breaks the model raises — that's the
    quarantine seam, surfaced to the caller.
    """
    alerts: list[AlertEvent] = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        if raw.get("event_type") != "alert":
            continue
        alerts.append(_ALERT_ADAPTER.validate_python(raw))
    return alerts


def unique_indicators(alerts: list[AlertEvent]) -> list[str]:
    """The enrichable indicator set: every distinct ``src_ip``/``dest_ip`` seen on
    the alerts, deduped so each IP is enriched exactly once. Sorted for a stable
    report."""
    ips: set[str] = set()
    for a in alerts:
        for ip in (a.src_ip, a.dest_ip):
            if ip is not None:
                ips.add(str(ip))
    return sorted(ips)
