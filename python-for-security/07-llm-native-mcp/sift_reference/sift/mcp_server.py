"""sift as an MCP server — every argument the LLM passes is untrusted input.

Two tools, both over the REAL EVE-derived indicators `sift` already produces:
  - `enrich`  takes one IP indicator (a `src_ip`/`dest_ip` off a validated `AlertEvent`)
  - `triage`  takes a whole EVE `alert` record

Each validates its argument with the canonical EVE pydantic models *inside* the tool,
exactly as a web handler would — an `IPvAnyAddress` for the IP, `AlertEvent` for the
record. The plain functions are kept separately so they're directly testable.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from .models import IP_ADAPTER, AlertEvent, load_alerts, malicious_ips

mcp = FastMCP("sift")

# Known-bad indicators derived once from the real corpus (the C2 the alerts flag).
_MALICIOUS: set[str] = malicious_ips(load_alerts())


def enrich_impl(indicator: str) -> dict:
    """Enrich one IP indicator. `indicator` must be a valid IP — reject anything else."""
    try:
        ip = IP_ADAPTER.validate_python(indicator)
    except ValidationError as e:
        raise ValueError(f"indicator must be an IP address, got {indicator!r}") from e
    ip_s = str(ip)
    # never interpolate `indicator` into a shell/SQL string (Module 05).
    malicious = ip_s in _MALICIOUS
    return {
        "indicator": ip_s,
        "malicious": malicious,
        "reason": "seen as C2 in a MALWARE/CnC Suricata alert" if malicious
        else "not in the alert corpus",
    }


def triage_impl(record: dict) -> dict:
    """Triage a whole EVE `alert` record. Validate it as an `AlertEvent` first — an
    out-of-range `severity`, a missing `signature`, or a non-`alert` line is rejected
    at the tool boundary rather than acted on."""
    event = AlertEvent.model_validate(record)  # raises ValidationError on a bad record
    dest = str(event.dest_ip)
    sig = event.alert.signature
    suspicious = (
        "MALWARE" in sig.upper()
        or "CNC" in sig.upper()
        or dest in _MALICIOUS
    )
    return {
        "src_ip": str(event.src_ip),
        "dest_ip": dest,
        "signature": sig,
        "severity": event.alert.severity,
        "suspicious": suspicious,
    }


# Register the (validated) functions as MCP tools the model can call.
enrich = mcp.tool()(enrich_impl)
triage = mcp.tool()(triage_impl)
