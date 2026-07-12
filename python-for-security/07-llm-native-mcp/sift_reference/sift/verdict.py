"""Typed LLM output — validate the model's reply like an API response.

`instructor` automates this against a real model (re-asking until the reply fits the
schema). Offline, we show the *discipline*: coerce the model's JSON into a pydantic
`Verdict`, and REJECT a malformed reply instead of trusting free text.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Verdict(BaseModel):
    model_config = {"extra": "forbid"}

    severity: Literal["low", "medium", "high", "critical"]
    is_true_positive: bool
    rationale: str


def parse_model_reply(raw_json: str) -> Verdict:
    """What instructor does under the hood: validate the model's output into a model."""
    return Verdict.model_validate_json(raw_json)
