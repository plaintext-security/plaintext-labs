"""typer CLI — a thin adapter over the shared core."""
from __future__ import annotations

import typer

from sift.core import Indicator, triage

app = typer.Typer(help="sift — triage an indicator")


@app.command()
def scan(value: str, kind: str = typer.Option("ipv4", help="ipv4|domain|sha256")) -> None:
    """Triage a single indicator and print the result as JSON."""
    result = triage(Indicator(kind=kind, value=value))
    typer.echo(result.model_dump_json())


if __name__ == "__main__":
    app()
