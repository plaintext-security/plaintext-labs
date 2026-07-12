"""FastAPI service — a thin adapter over the SAME shared core.

FastAPI validates the request body against the same `Indicator` model the CLI uses
— the payoff of the parse-don't-trust spine: input validation is free and shared.
"""
from __future__ import annotations

from fastapi import FastAPI

from sift.core import Indicator, TriageResult, triage

app = FastAPI(title="sift")


@app.post("/triage", response_model=TriageResult)
def triage_endpoint(indicator: Indicator) -> TriageResult:
    return triage(indicator)
