"""FastAPI service — a thin adapter over the SAME shared core.

FastAPI validates the request body against the same `AlertEvent` model the CLI uses
— the payoff of the parse-don't-trust spine: input validation is free and shared. A
malformed EVE line (bad JSON, severity outside Suricata's 1..3, a non-`alert`
event_type) is rejected with a 422 *before* our code runs.
"""
from __future__ import annotations

from fastapi import FastAPI

from sift.core import AlertEvent, TriageResult, triage

app = FastAPI(title="sift")


@app.post("/triage", response_model=TriageResult)
def triage_endpoint(event: AlertEvent) -> TriageResult:
    return triage(event)
