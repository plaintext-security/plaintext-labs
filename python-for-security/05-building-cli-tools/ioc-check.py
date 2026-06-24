#!/usr/bin/env python3
"""
Reference ioc-check CLI — wraps the enrichment function from module 04.
Two subcommands: enrich (query an IOC or file) and report (summarise JSON output).
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

__version__ = "0.1.0"

app = typer.Typer(help="IOC enrichment CLI backed by real abuse.ch threat-intel feeds.")
console = Console()

API_BASE = os.environ.get("THREAT_API_URL", "http://localhost:8080")

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SAMPLE_RE = re.compile(r"^\d{4,}$")  # URLhaus sample id (numeric)


def _detect_type(ioc: str) -> str:
    if IP_RE.match(ioc):
        return "ip"
    if SAMPLE_RE.match(ioc):
        return "sample"
    return "unknown"


def _enrich_one(client: httpx.Client, ioc: str) -> dict:
    ioc_type = _detect_type(ioc)
    if ioc_type == "unknown":
        return {"ioc": ioc, "type": "unknown", "verdict": "error", "error": "invalid format"}
    url = f"{API_BASE}/api/v3/ip/{ioc}" if ioc_type == "ip" else f"{API_BASE}/api/v3/hash/{ioc}"
    try:
        resp = client.get(url, timeout=httpx.Timeout(connect=5.0, read=10.0))
    except httpx.TimeoutException:
        return {"ioc": ioc, "type": ioc_type, "verdict": "error", "error": "timeout"}
    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 404:
        return {"ioc": ioc, "type": ioc_type, "verdict": "unknown"}
    return {"ioc": ioc, "type": ioc_type, "verdict": "error", "error": f"http_{resp.status_code}"}


@app.command()
def enrich(
    ioc: Optional[str] = typer.Option(None, "--ioc", help="Single IOC to enrich (IP or hash)."),
    file: Optional[Path] = typer.Option(None, "--file", help="Path to a file with one IOC per line."),
    output: Optional[Path] = typer.Option(None, "--output", help="Write JSON output here (default: stdout)."),
) -> None:
    """Enrich one or more IOCs against the threat-intel API."""
    if not ioc and not file:
        console.print("[red]Error:[/red] supply --ioc or --file.", err=True)
        raise typer.Exit(code=1)

    iocs = []
    if ioc:
        if _detect_type(ioc) == "unknown":
            console.print(f"[red]Error:[/red] '{ioc}' is not a valid IP, MD5, or SHA-256.", err=True)
            raise typer.Exit(code=1)
        iocs.append(ioc)
    if file:
        if not file.exists():
            console.print(f"[red]Error:[/red] file not found: {file}", err=True)
            raise typer.Exit(code=1)
        iocs.extend([line.strip() for line in file.read_text().splitlines() if line.strip()])

    results = []
    with httpx.Client() as client:
        for i in iocs:
            results.append(_enrich_one(client, i))

    payload = json.dumps(results, indent=2)
    if output:
        output.write_text(payload)
        console.print(f"[dim]Wrote {len(results)} results to {output}[/dim]")
    else:
        print(payload)


@app.command()
def report(
    input: Optional[Path] = typer.Option(None, "--input", help="JSON file from enrich (default: stdin)."),
) -> None:
    """Render a summary table from enrichment JSON."""
    if input:
        data = json.loads(input.read_text())
    else:
        data = json.loads(sys.stdin.read())

    table = Table(title="IOC Enrichment Report")
    table.add_column("IOC")
    table.add_column("Type")
    table.add_column("Verdict")
    for row in data:
        verdict = row.get("verdict", "?")
        color = {"malicious": "red", "suspicious": "yellow", "clean": "green"}.get(verdict, "white")
        table.add_row(row.get("ioc", ""), row.get("type", ""), f"[{color}]{verdict}[/{color}]")
    console.print(table)


@app.command()
def version() -> None:
    """Print tool version."""
    console.print(f"ioc-check {__version__}")


if __name__ == "__main__":
    app()
