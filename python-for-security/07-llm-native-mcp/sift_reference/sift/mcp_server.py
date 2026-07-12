"""sift as an MCP server — every argument the LLM passes is untrusted input.

The tool validates its arguments with pydantic *inside* the tool, exactly as a web
handler would. The plain function is kept separately so it's directly testable.
"""
from __future__ import annotations

import ipaddress

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sift")


def enrich_impl(indicator: str) -> dict:
    """Enrich one indicator. `indicator` must be an IPv4 — reject anything else."""
    try:
        ipaddress.IPv4Address(indicator)
    except ValueError as e:
        raise ValueError(f"indicator must be an IPv4 address, got {indicator!r}") from e
    # never interpolate `indicator` into a shell/SQL string (Module 05).
    return {"indicator": indicator, "malicious": indicator.startswith("45.")}


# Register the (validated) function as an MCP tool the model can call.
enrich = mcp.tool()(enrich_impl)
