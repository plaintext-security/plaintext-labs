#!/usr/bin/env python3
"""End-to-end MCP round-trip test: spawn the server over stdio and drive it as a client.

This proves the server actually *serves* the protocol — not just that the functions work.
It requires the `mcp` package (the SDK ships the client). Run it after installing deps:

    pip install -r server/requirements.txt
    python3 tests/mcp_roundtrip.py

Exit 0 = the client connected, listed tools/resources/prompts, and got correct results.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    sys.stderr.write("error: this test needs the 'mcp' package — pip install -r server/requirements.txt\n")
    raise SystemExit(2)


async def run() -> int:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / "server" / "server.py")],
    )
    failures: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail and not cond else ""))
        if not cond:
            failures.append(name)

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            names = {t.name for t in tools}
            print(f"Server advertised tools: {sorted(names)}")
            for expected in ("list_tracks", "get_module", "get_learn_path", "get_lab",
                             "search_curriculum", "suggest_next", "curriculum_stats"):
                check(f"tool '{expected}' advertised", expected in names)

            resources = (await session.list_resource_templates()).resourceTemplates
            res_uris = {r.uriTemplate for r in resources}
            print(f"Server advertised resource templates: {sorted(res_uris)}")
            check("module resource template advertised",
                  any("curriculum://module/" in u for u in res_uris), str(res_uris))

            prompts = (await session.list_prompts()).prompts
            check("tutor prompt advertised", any(p.name == "tutor" for p in prompts))

            # Call a tool and inspect the structured result.
            res = await session.call_tool("curriculum_stats", {})
            text = res.content[0].text if res.content else ""
            print(f"curriculum_stats -> {text}")
            check("curriculum_stats returns track count", '"tracks"' in text)

            res = await session.call_tool("search_curriculum", {"query": "mcp", "limit": 3})
            text = res.content[0].text if res.content else ""
            check("search_curriculum returns results", '"results"' in text, text[:120])

            # Read a resource.
            ov = await session.read_resource("curriculum://overview")
            ov_text = ov.contents[0].text if ov.contents else ""
            check("overview resource readable", "Plaintext Curriculum Map" in ov_text)

    print()
    if failures:
        print(f"ROUND-TRIP FAILED: {failures}")
        return 1
    print("ROUND-TRIP PASSED: client connected, listed, called, and read over stdio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
