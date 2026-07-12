"""The triage classifier under evaluation, plus the validator the property tests fuzz."""
from __future__ import annotations

import ipaddress

from pydantic import BaseModel, field_validator


def classify(indicator: str) -> str:
    """Toy deterministic triage — the non-trivial thing the eval harness measures."""
    if indicator.startswith(("45.", "203.0.113.")):
        return "malicious"
    return "benign"


class Indicator(BaseModel):
    """Module 02's boundary model — the property tests fuzz this to prove it rejects
    ALL malformed input, not just the examples we thought of."""

    value: str

    @field_validator("value")
    @classmethod
    def must_be_ip(cls, v: str) -> str:
        ipaddress.ip_address(v)  # raises → ValidationError
        return v
