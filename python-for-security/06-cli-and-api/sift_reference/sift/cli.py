"""typer CLI — a thin adapter over the shared core.

Reads a real EVE record from an `eve.json` file, validates it into an `AlertEvent`
(the SAME model the API uses), delegates to the core `triage()`, and renders JSON.
Parse, delegate, render — no business logic here.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from sift.core import AlertEvent
from sift.core import triage as core_triage

app = typer.Typer(help="sift — triage a Suricata EVE alert")


@app.callback()
def main() -> None:
    """sift — triage Suricata EVE alerts (keeps `triage` a named subcommand)."""


@app.command()
def triage(
    path: Path = typer.Argument(..., help="path to an eve.json (NDJSON, one event per line)"),
    line: Optional[int] = typer.Option(
        None, "--line", help="0-based line to triage; default = first alert event in the file"
    ),
) -> None:
    """Triage one EVE alert record and print the TriageResult as JSON."""
    lines = path.read_text().splitlines()
    if line is not None:
        raw = lines[line]
    else:
        raw = next(l for l in lines if json.loads(l).get("event_type") == "alert")
    event = AlertEvent.model_validate_json(raw)  # same model that guards the API
    typer.echo(core_triage(event).model_dump_json())


if __name__ == "__main__":
    app()
