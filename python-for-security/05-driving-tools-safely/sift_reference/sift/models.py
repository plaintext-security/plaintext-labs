"""Typed domain models — the boundary sift parses a dissector's output through.

sift ingests real **Suricata EVE JSON** (`eve.json`): newline-delimited events, one JSON
object per line, keyed by `event_type`. In this module that feed is the *structured output
of a driven tool* (Suricata / `tshark -T ek`): instead of scraping stdout text, we parse each
line into a typed `AlertEvent` — or reject it.

Real EVE carries many envelope fields (`in_iface`, `app_proto`, `community_id`, `tx_id`, …), so
we do **not** `extra="forbid"` the record — that would reject every genuine line. We *pin and
constrain the fields sift depends on* and `extra="ignore"` the rest. Which fields to require is a
judgment call: an `alert` event always has a five-tuple, so `AlertEvent` makes `src_ip`/`dest_ip`
**required** even though `EveBase` leaves them optional for event types that legitimately omit them.

The core lab parses `alert` events. Other event types (`dns`, `http`, `tls`, `flow`, `fileinfo`)
are added as typed union members in the module Stretch tasks; until then, an unhandled `event_type`
fails the discriminator and is quarantined — never silently trusted, never fatal.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, TypeAdapter


class EveBase(BaseModel):
    """Envelope fields common to every EVE event. Endpoints are optional here because
    some event types (stats, flow bookkeeping) legitimately omit them."""

    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    flow_id: int | None = None
    src_ip: IPvAnyAddress | None = None
    dest_ip: IPvAnyAddress | None = None
    src_port: int | None = None
    dest_port: int | None = None
    proto: str | None = None


class AlertDetails(BaseModel):
    """The nested `alert` object on an EVE alert event."""

    model_config = ConfigDict(extra="ignore")

    signature: Annotated[str, Field(min_length=1)]
    signature_id: int                       # an ET/Suricata sid — an int, not "ET-2035678"
    category: str
    severity: int = Field(ge=1, le=3)       # Suricata alert severity is 1 (most) .. 3 (least)
    gid: int | None = None
    rev: int | None = None


class AlertEvent(EveBase):
    """`event_type: "alert"`. An alert always has endpoints, so we require the five-tuple —
    a real alert missing `dest_ip` is a signal, so we reject it rather than default it."""

    event_type: Literal["alert"]
    src_ip: IPvAnyAddress                    # required (overrides the optional EveBase field)
    dest_ip: IPvAnyAddress                   # required
    alert: AlertDetails


# The discriminated union GROWS as dissector Stretch tasks add members
# (DnsEvent, HttpEvent, TlsEvent, FlowEvent, FileinfoEvent). An event_type with no
# member fails the discriminator and is quarantined by the caller.
EveEvent = Annotated[Union[AlertEvent], Field(discriminator="event_type")]

# Parse one raw dict with `EVE_ADAPTER.validate_python(raw)`.
EVE_ADAPTER: TypeAdapter[AlertEvent] = TypeAdapter(EveEvent)
