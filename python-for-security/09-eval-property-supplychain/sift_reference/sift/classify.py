"""The triage classifier under evaluation, plus the canonical EVE boundary the property tests fuzz.

`sift` ingests real **Suricata EVE JSON** (`eve.json`): newline-delimited events, one JSON object
per line, keyed by `event_type`. The core track parses **`alert`** events. This module measures the
triage judgment `sift` makes on those alerts — *is this alert worth an analyst's time?* — and fuzzes
the same M02 boundary model that turns each untrusted line into a typed `AlertEvent` or rejects it.

Real EVE carries many envelope fields (`in_iface`, `app_proto`, `community_id`, `tx_id`, `pkt_src`, …),
so we do **not** `extra="forbid"` the record — that would reject every genuine line. We pin and
constrain the fields `sift` depends on and `extra="ignore"` the rest. That judgment (which fields to
pin vs. ignore) is the bridge; the property tests below prove the boundary is total either way.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, TypeAdapter


# ── The canonical EVE boundary (mirrors M02 `sift.models`) ────────────────────────────────
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


# The discriminated union GROWS as dissector Stretch tasks add members (DnsEvent, HttpEvent, …).
# Parse with `TypeAdapter(EveEvent).validate_python(raw)`; an event_type with no member is quarantined.
EveEvent = Annotated[Union[AlertEvent], Field(discriminator="event_type")]
EVE_ADAPTER: TypeAdapter[AlertEvent] = TypeAdapter(EveEvent)


# ── The triage judgment under evaluation ──────────────────────────────────────────────────
# The non-deterministic-in-spirit call the eval harness measures: given a parsed alert, is it a
# true positive (an analyst should look) or a false positive (dismissible noise)? This conservative
# rule keys on Suricata severity + ET category — deliberately simple, so the held-out corpus can
# expose where it MISSES (the info-level external-IP lookup that was actually the RAT's recon).
_ATTACK_CATEGORIES = frozenset(
    {
        "Malware Command and Control Activity Detected",
        "A Network Trojan was Detected",
        "A Network Trojan was detected",
        "Misc Attack",
        "Attempted Administrator Privilege Gain",
        "Attempted User Privilege Gain",
    }
)


def triage(event: AlertEvent) -> str:
    """Return the triage verdict for a parsed alert: ``"true_positive"`` or ``"false_positive"``."""
    a = event.alert
    if a.severity == 1:                       # Suricata's most-severe band → always worth a look
        return "true_positive"
    if a.category in _ATTACK_CATEGORIES:      # explicit attack/trojan categories
        return "true_positive"
    if a.signature.startswith("ET DROP"):     # traffic from a known-bad (Spamhaus DROP) netblock
        return "true_positive"
    return "false_positive"
