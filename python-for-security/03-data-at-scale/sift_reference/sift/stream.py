"""Streaming ingest — read the Suricata EVE feed one line at a time, never all of it.

Suricata writes `eve.json` as newline-delimited JSON: one event per line, keyed by
`event_type` (`alert`, `dns`, `tls`, `flow`, `http`, `smb`, ...). Over a real infection
capture that file is hundreds of thousands of lines. The copilot writes
`json.load(open(f))` / `[json.loads(l) for l in f]` and holds the whole feed in RAM;
this yields validated events one at a time so `sift` scales to any feed size at flat memory.

Each line is validated into the canonical EVE `AlertEvent` model (pydantic v2). Real EVE
carries dozens of envelope fields (`community_id`, `app_proto`, `tx_id`, `pkt_src`, ...), so
we `extra="ignore"` the rest and pin only the fields `sift` depends on — you never
`extra="forbid"` a real feed or it rejects every genuine line. Non-`alert` lines and
malformed/rotated lines are *quarantined* (skipped, counted), never fatal — the seam a
later dissector fills.
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, ValidationError


class EveBase(BaseModel):
    model_config = ConfigDict(extra="ignore")  # EVE has many fields; pin what matters, ignore the rest
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
    signature_id: int                  # an ET Open / SURICATA sid
    category: str
    severity: int = Field(ge=1, le=3)  # Suricata alert severity is 1..3
    gid: int | None = None
    rev: int | None = None


class AlertEvent(EveBase):
    event_type: Literal["alert"]
    alert: AlertDetails


@dataclass
class StreamStats:
    """Side-channel counters — how many lines we read, yielded, and quarantined."""
    read: int = 0
    alerts: int = 0
    quarantined: int = 0


def stream_alerts(
    path: str | Path, stats: StreamStats | None = None
) -> Iterator[AlertEvent]:
    """Yield one validated ``AlertEvent`` at a time from an EVE feed (constant memory).

    Non-alert event types, malformed JSON, and out-of-spec records are quarantined
    (skipped and counted in ``stats``), never raised — a rotated/cut line must not kill
    the stream. Pass a shared ``StreamStats`` to observe totals across a replayed feed.
    """
    if stats is None:
        stats = StreamStats()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats.read += 1
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                stats.quarantined += 1  # truncated / rotated mid-write
                continue
            if raw.get("event_type") != "alert":
                stats.quarantined += 1  # unhandled type — a dissector stretch fills this seam
                continue
            try:
                event = AlertEvent.model_validate(raw)
            except ValidationError:
                stats.quarantined += 1  # e.g. severity out of 1..3, bad signature_id type
                continue
            stats.alerts += 1
            yield event
