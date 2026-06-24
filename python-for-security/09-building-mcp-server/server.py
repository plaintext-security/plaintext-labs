#!/usr/bin/env python3
"""
Reference MCP server — exposes enrich_ip as a tool via fastmcp.
"""

import os
import re

import httpx
import fastmcp

API_BASE = os.environ.get("THREAT_API_URL", "http://localhost:8080")
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

mcp = fastmcp.FastMCP("ioc-enrichment")


@mcp.tool
def enrich_ip(ip: str) -> dict:
    """Enrich an IP address with real threat-intel data (abuse.ch Feodo Tracker + URLhaus).

    Returns a dict with verdict, asn, country, malware family, and provenance (source).
    Returns {"error": "invalid IP format"} for non-IP input.
    Returns {"verdict": "unknown"} if the IP is not in the feed snapshot.
    """
    if not IP_RE.match(ip):
        return {"error": "invalid IP format"}

    try:
        resp = httpx.get(
            f"{API_BASE}/api/v3/ip/{ip}",
            timeout=httpx.Timeout(connect=5.0, read=10.0),
        )
    except httpx.TimeoutException:
        return {"error": "timeout", "ip": ip}

    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 404:
        return {"verdict": "unknown", "ip": ip}
    return {"error": "api_error", "status": resp.status_code, "ip": ip}


if __name__ == "__main__":
    mcp.run()
