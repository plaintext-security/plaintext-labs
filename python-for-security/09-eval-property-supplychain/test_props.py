"""Property tests — fuzz the canonical EVE boundary (M02) to prove it is TOTAL.

Example-based tests check the cases you thought of; `hypothesis` generates thousands you didn't.
The invariant (canon §1.1): for ANY EVE-shaped input, the `AlertEvent` / `EveEvent` union validator
either

  * yields a well-formed `AlertEvent` (event_type == "alert", severity in 1..3, endpoints present), OR
  * raises `pydantic.ValidationError`

— never a half-parsed object, never any *other* exception. If the fuzzer ever provokes something that
is neither a clean parse nor a `ValidationError`, that is the bug: the boundary leaked.

The explicit cases below are the canon §1.3 malformed fixtures — real EVE breakage — kept as
regression tests alongside the fuzzer.
"""
import sys
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))
from sift.classify import EVE_ADAPTER, AlertEvent  # noqa: E402


# ── Strategies: EVE-shaped inputs, deliberately spanning valid and malformed ────────────────
_ips = st.ip_addresses().map(str)
_maybe_ip = st.one_of(_ips, st.text(max_size=12), st.none())            # valid IP, junk, or absent
_timestamps = st.one_of(
    st.just("2024-07-30T02:38:49.686160+0000"),
    st.datetimes().map(lambda d: d.isoformat()),
    st.text(max_size=12),                                              # non-timestamp junk
    st.none(),
)
_severities = st.one_of(st.integers(min_value=-3, max_value=9), st.text(max_size=4), st.none())
_sids = st.one_of(st.integers(), st.text(max_size=10))                  # int sid, or "ET-2019401"
_event_types = st.one_of(
    st.just("alert"),
    st.sampled_from(["dns", "http", "tls", "flow", "fileinfo", "stats", "anomaly"]),
    st.text(max_size=8),
)


@st.composite
def _alert_objects(draw):
    """A nested `alert` object — sometimes complete, sometimes missing/mistyped fields."""
    obj = {}
    if draw(st.booleans()):
        obj["signature"] = draw(st.one_of(st.text(max_size=40), st.just("")))
    if draw(st.booleans()):
        obj["signature_id"] = draw(_sids)
    if draw(st.booleans()):
        obj["category"] = draw(st.text(max_size=30))
    if draw(st.booleans()):
        obj["severity"] = draw(_severities)
    # occasional real-EVE extra field that must be ignored, not rejected
    if draw(st.booleans()):
        obj["metadata"] = {"confidence": ["High"]}
    return obj


@st.composite
def _eve_lines(draw):
    """An EVE-shaped record: a dict with a plausible mix of present/absent/mistyped fields."""
    rec = {}
    if draw(st.booleans()):
        rec["event_type"] = draw(_event_types)
    if draw(st.booleans()):
        rec["timestamp"] = draw(_timestamps)
    if draw(st.booleans()):
        rec["src_ip"] = draw(_maybe_ip)
    if draw(st.booleans()):
        rec["dest_ip"] = draw(_maybe_ip)
    if draw(st.booleans()):
        rec["src_port"] = draw(st.one_of(st.integers(), st.text(max_size=4)))
    if draw(st.booleans()):
        rec["dest_port"] = draw(st.one_of(st.integers(), st.text(max_size=4)))
    if draw(st.booleans()):
        rec["proto"] = draw(st.sampled_from(["TCP", "UDP", "ICMP"]))
    if draw(st.booleans()):
        rec["alert"] = draw(_alert_objects())
    # real EVE envelope extras — extra="ignore" must tolerate these
    if draw(st.booleans()):
        rec["community_id"] = draw(st.text(max_size=20))
    return rec


# ── The totality property ───────────────────────────────────────────────────────────────────
@given(st.one_of(_eve_lines(), st.text(), st.integers(), st.lists(st.integers(), max_size=3), st.none()))
def test_eve_boundary_is_total(raw):
    """Every input either validates to a well-formed AlertEvent or raises ValidationError — nothing else."""
    try:
        event = EVE_ADAPTER.validate_python(raw)
    except ValidationError:
        return  # rejected → quarantine path; that's a correct outcome
    # Accepted → it MUST be a fully-formed alert, not a half-parsed object.
    assert isinstance(event, AlertEvent)
    assert event.event_type == "alert"
    assert 1 <= event.alert.severity <= 3
    assert event.src_ip is not None and event.dest_ip is not None


@given(st.builds(dict))  # sanity: an empty dict is rejected, never half-parsed
def test_empty_is_rejected(raw):
    with pytest.raises(ValidationError):
        EVE_ADAPTER.validate_python(raw)


# ── Canon §1.3 malformed fixtures — real EVE breakage, kept as regression tests ─────────────
_VALID_ALERT = {
    "timestamp": "2024-07-30T02:38:57.606763+0000",
    "flow_id": 1234567890,
    "event_type": "alert",
    "src_ip": "172.16.1.66",
    "dest_ip": "45.144.31.30",
    "src_port": 49702,
    "dest_port": 8848,
    "proto": "TCP",
    "alert": {
        "gid": 1,
        "signature_id": 2400000,
        "rev": 1,
        "signature": "ET MALWARE STRRAT CnC Checkin",
        "category": "Malware Command and Control Activity Detected",
        "severity": 1,
    },
}


def test_valid_alert_parses():
    event = EVE_ADAPTER.validate_python(_VALID_ALERT)
    assert isinstance(event, AlertEvent)
    assert event.alert.severity == 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: {**r, "alert": {**r["alert"], "severity": 5}},            # out of Suricata 1..3
        lambda r: {**r, "event_type": "stats"},                            # unhandled union member
        lambda r: {**r, "event_type": "dns"},                              # dissector-stretch type
        lambda r: {k: v for k, v in r.items() if k != "dest_ip"},          # alert missing dest_ip
        lambda r: {**r, "alert": {**r["alert"], "signature_id": "ET-2019401"}},  # sid wrong type
        lambda r: {**r, "src_ip": "999.1.1.1"},                            # invalid IP
        lambda r: {**r, "alert": {**r["alert"], "signature": ""}},         # empty signature
    ],
)
def test_malformed_eve_is_rejected(mutate):
    with pytest.raises(ValidationError):
        EVE_ADAPTER.validate_python(mutate(_VALID_ALERT))
