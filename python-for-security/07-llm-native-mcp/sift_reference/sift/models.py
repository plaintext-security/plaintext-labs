"""Canonical Suricata EVE JSON models for `sift` (pydantic v2).

These are the same shapes `sift` uses from M02 onward (canon §1.1): a discriminated
union keyed on `event_type`. The core track parses `alert` events. Real EVE carries
many envelope fields (`community_id`, `pkt_src`, `app_proto`, `tx_id`, …), so we
`extra="ignore"` the rest and pin/constrain only the fields we depend on.

Indicators are DERIVED from real EVE fields (`src_ip`/`dest_ip`/`signature`) — there is
no invented `Indicator{kind, value}` schema.
"""
from __future__ import annotations

import ipaddress
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    TypeAdapter,
)

# Validate a single untrusted IP argument with the canonical IP type.
IP_ADAPTER: TypeAdapter[IPvAnyAddress] = TypeAdapter(IPvAnyAddress)


class EveBase(BaseModel):
    model_config = ConfigDict(extra="ignore")  # EVE has many fields; pin what matters
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
    signature_id: int                  # an ET Open sid
    category: str
    severity: int = Field(ge=1, le=3)  # Suricata alert severity is 1..3
    gid: int | None = None
    rev: int | None = None


class AlertEvent(EveBase):
    event_type: Literal["alert"]
    alert: AlertDetails


# The union GROWS as dissector stretches add members (Dns/Http/Tls/Flow/Fileinfo).
EveEvent = Annotated[Union[AlertEvent], Field(discriminator="event_type")]

# data/eve.json lives at the lab root (three parents up from this module).
DATA = Path(__file__).resolve().parents[2] / "data" / "eve.json"


def load_alerts(path: Path = DATA) -> list[AlertEvent]:
    """Parse the real EVE corpus into typed `AlertEvent`s.

    Non-`alert` event types and any non-JSON (truncated) line are skipped — the core
    track parses `alert`; the dissector stretch grows the union to the rest.
    """
    alerts: list[AlertEvent] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            continue  # truncated / rotated line -> quarantine
        if raw.get("event_type") != "alert":
            continue
        alerts.append(AlertEvent.model_validate(raw))
    return alerts


def malicious_ips(alerts: list[AlertEvent]) -> set[str]:
    """Derive a known-bad indicator set from real alerts: the PUBLIC IP seen in any
    MALWARE / CnC / Trojan signature (the C2 endpoint, not the internal victim)."""
    bad: set[str] = set()
    for e in alerts:
        sig = e.alert.signature.upper()
        if "MALWARE" in sig or "CNC" in sig or "TROJAN" in sig:
            for ip in (e.src_ip, e.dest_ip):
                if ip is not None and not ipaddress.ip_address(str(ip)).is_private:
                    bad.add(str(ip))
    return bad
