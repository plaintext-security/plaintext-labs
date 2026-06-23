#!/usr/bin/env python3
"""
SOC Security MCP Server
Exposes three security data tools via the Model Context Protocol using fastmcp.

Tools:
  - get_threat_intel(ioc)     Query threat intelligence for an IOC
  - search_alerts(query)      Search the SOC alert database
  - summarize_incident(id)    Retrieve and summarise an incident record

Run:
    python3 server/server.py
    # or via Docker (see Makefile)
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    from fastmcp import FastMCP
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastmcp>=0.9"], check=True)
    from fastmcp import FastMCP

DATA_DIR = Path(os.environ.get("DATA_DIR", "/lab/data"))

mcp = FastMCP(
    name="soc-security",
    instructions="Security operations tools for a SOC. Use these tools to "
                 "look up threat intelligence, search security alerts, and retrieve incident details.",
)


def _load_json(filename: str) -> dict | list:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path) as f:
        return json.load(f)


IOC_PATTERN = re.compile(r'^[a-zA-Z0-9./:\-_@]{1,255}$')


@mcp.tool()
def get_threat_intel(ioc: str) -> dict:
    """Look up an indicator of compromise (IOC) in the SOC threat intelligence database.

    The IOC can be an IP address (e.g. '185.220.101.42'), a domain name (e.g.
    'update-checker.net'), or an MD5/SHA256 hash. Returns classification (malicious/
    clean/unknown/internal), confidence level, category, and first/last seen dates.
    Returns {"found": false} if the IOC is not in the database.

    Args:
        ioc: The indicator to look up. Must be a valid IP, domain, or hash string.
    """
    # Input validation: reject strings that look like injection attempts
    if not IOC_PATTERN.match(ioc):
        return {"error": f"Invalid IOC format: '{ioc[:40]}'. Must match [a-zA-Z0-9./:\\-_@]{{1,255}}."}

    intel = _load_json("threat-intel.json")

    # Search across all IOC type buckets
    for bucket in ("ips", "domains", "hashes"):
        if ioc in intel.get(bucket, {}):
            record = intel[bucket][ioc]
            return {
                "found": True,
                "ioc": ioc,
                "classification": record["classification"],
                "category": record["category"],
                "confidence": record["confidence"],
                "first_seen": record.get("first_seen"),
                "last_seen": record.get("last_seen"),
                "references": record.get("references", []),
            }

    return {"found": False, "ioc": ioc, "message": "IOC not found in local threat intel database."}


@mcp.tool()
def search_alerts(query: str) -> dict:
    """Search the SOC alert database for security alerts matching a keyword or IOC.

    Performs a case-insensitive substring search across alert titles, descriptions,
    hostnames, and IOC fields. Returns up to 10 matching alerts ordered by timestamp
    descending. Each result includes alert ID, severity, title, host, status, and timestamp.

    Args:
        query: Search term — a keyword (e.g. 'PowerShell'), hostname, IP address, or alert ID.
    """
    if not query or not query.strip():
        return {"error": "Query cannot be empty."}
    if len(query) > 200:
        return {"error": "Query too long (max 200 characters)."}

    query_lower = query.lower().strip()
    alerts = _load_json("alerts.json")

    matches = []
    for alert in alerts:
        searchable = " ".join([
            alert.get("title", ""),
            alert.get("description", ""),
            alert.get("host", ""),
            str(alert.get("ioc") or ""),
            alert.get("id", ""),
        ]).lower()

        if query_lower in searchable:
            matches.append({
                "id": alert["id"],
                "timestamp": alert["timestamp"],
                "severity": alert["severity"],
                "title": alert["title"],
                "host": alert["host"],
                "status": alert["status"],
                "ioc": alert.get("ioc"),
            })

    # Sort by timestamp descending, limit to 10
    matches.sort(key=lambda a: a["timestamp"], reverse=True)
    matches = matches[:10]

    return {
        "query": query,
        "count": len(matches),
        "alerts": matches,
    }


@mcp.tool()
def summarize_incident(id: str) -> dict:
    """Retrieve and summarise a SOC security incident by its incident ID.

    Returns the incident title, severity, current status, creation timestamp, assigned
    team, description, related alert IDs, and MITRE ATT&CK technique IDs. Use this tool
    to get context about an ongoing or historical incident before making recommendations.

    Args:
        id: Incident ID in the format 'INC-YYYY-NNNN' (e.g. 'INC-2025-0042').
    """
    if not re.match(r'^INC-\d{4}-\d{4}$', id):
        return {"error": f"Invalid incident ID format: '{id}'. Expected format: INC-YYYY-NNNN."}

    incidents = _load_json("incidents.json")

    for incident in incidents:
        if incident["id"] == id:
            return {
                "found": True,
                "id": incident["id"],
                "title": incident["title"],
                "severity": incident["severity"],
                "status": incident["status"],
                "created": incident["created"],
                "assigned_to": incident["assigned_to"],
                "description": incident["description"],
                "related_alerts": incident.get("related_alerts", []),
                "mitre_techniques": incident.get("mitre_techniques", []),
            }

    return {"found": False, "id": id, "message": f"Incident {id} not found."}


if __name__ == "__main__":
    mcp.run(transport="stdio")
