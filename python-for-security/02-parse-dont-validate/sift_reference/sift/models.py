"""Typed domain models — the input boundary of sift. *Parse, don't validate.*

sift ingests real **Suricata EVE JSON** (`eve.json`): newline-delimited events, one JSON
object per line, keyed by `event_type`. This boundary turns each untrusted line into a typed
`AlertEvent`, or rejects it. Invalid input is refused here, loudly, not carried forward as a
half-checked dict.

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

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


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
# (DnsEvent, HttpEvent, TlsEvent, FlowEvent, FileinfoEvent). Parse with
# `TypeAdapter(EveEvent).validate_python(raw)`; an event_type with no member is quarantined.
EveEvent = Annotated[Union[AlertEvent], Field(discriminator="event_type")]
