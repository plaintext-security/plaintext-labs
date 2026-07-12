"""Typed domain models — the input boundary of sift. *Parse, don't validate.*

Turn untrusted feed records into typed `Alert` objects at the edge, so the rest of
sift only ever handles valid data. Invalid input is rejected here, loudly, not
carried forward as a half-checked dict.
"""
from __future__ import annotations

import ipaddress
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

Severity = Literal["low", "medium", "high", "critical"]


class Indicator(BaseModel):
    """An observable pulled from an alert. `value` must match its `kind`."""

    kind: Literal["ipv4", "domain", "sha256"]
    value: Annotated[str, Field(min_length=1, max_length=253)]

    @field_validator("value")
    @classmethod
    def _shape_matches_kind(cls, v: str, info) -> str:
        kind = info.data.get("kind")
        if kind == "ipv4":
            ipaddress.IPv4Address(v)  # raises → ValidationError
        elif kind == "sha256":
            if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
                raise ValueError("sha256 must be 64 hex chars")
        elif kind == "domain":
            if " " in v or "/" in v:
                raise ValueError("domain must not contain spaces or slashes")
        return v


class Alert(BaseModel):
    """One security alert. Unknown/extra fields are rejected, not ignored."""

    model_config = {"extra": "forbid"}

    id: int
    source: Annotated[str, Field(min_length=1)]
    severity: Severity
    indicator: Indicator
