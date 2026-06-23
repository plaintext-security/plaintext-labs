#!/usr/bin/env python3
"""
test-client.py — MCP test client that calls the SOC Security MCP server
via HTTP (SSE transport) and prints the results of each tool.

Usage:
    python3 scripts/test-client.py [--host http://mcp-server:8080]
"""

import argparse
import json
import sys

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "requests"], check=True)
    import requests


def call_tool(base_url: str, tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool via the HTTP/JSON-RPC interface."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    resp = requests.post(f"{base_url}/mcp", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_tools(base_url: str) -> list:
    """Call tools/list to get the server's tool manifest."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
    resp = requests.post(f"{base_url}/mcp", json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", {}).get("tools", [])


def main():
    parser = argparse.ArgumentParser(description="MCP test client for the SOC Security server")
    parser.add_argument("--host", default="http://mcp-server:8080", help="MCP server URL")
    args = parser.parse_args()

    print(f"=== MCP Test Client ===")
    print(f"Server: {args.host}\n")

    # 1. List tools
    print("--- tools/list ---")
    try:
        tools = list_tools(args.host)
        for t in tools:
            print(f"  {t['name']}: {t.get('description', '(no description)')[:80]}")
    except Exception as e:
        print(f"ERROR calling tools/list: {e}")
        print("Is the MCP server running? Try: make up && make demo")
        sys.exit(1)
    print()

    # 2. Call get_threat_intel
    print("--- tools/call: get_threat_intel(ioc='185.220.101.42') ---")
    result = call_tool(args.host, "get_threat_intel", {"ioc": "185.220.101.42"})
    print(json.dumps(result.get("result", result), indent=2))
    print()

    # 3. Call search_alerts
    print("--- tools/call: search_alerts(query='PowerShell') ---")
    result = call_tool(args.host, "search_alerts", {"query": "PowerShell"})
    print(json.dumps(result.get("result", result), indent=2))
    print()

    # 4. Call summarize_incident
    print("--- tools/call: summarize_incident(id='INC-2025-0042') ---")
    result = call_tool(args.host, "summarize_incident", {"id": "INC-2025-0042"})
    print(json.dumps(result.get("result", result), indent=2))
    print()


if __name__ == "__main__":
    main()
