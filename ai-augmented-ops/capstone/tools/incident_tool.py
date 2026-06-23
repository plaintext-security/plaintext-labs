#!/usr/bin/env python3
"""
Stub MCP tool for the Track 12 capstone — a STARTING POINT, not a finished tool.

It exposes one real tool over the Model Context Protocol (fastmcp):
    lookup_incident(query)  -> search the seed runbook corpus for a matching incident/runbook

Your job in the capstone is to turn this into a copilot tool worth having: ground it
in YOUR notes, scope it to least privilege, then red-team it (prompt injection / data
exfil) and harden it. See ../README.md and ../rubric.md.

Two ways to run:
    python3 tools/incident_tool.py            # start the MCP server (stdio)
    python3 tools/incident_tool.py --selftest # run the tool logic directly, no MCP client

Trust-boundary note (this is the whole point of the capstone): the corpus this tool
reads is UNTRUSTED content. A poisoned runbook can carry instructions aimed at the model
(the EchoLeak / CVE-2025-32711 indirect-injection shape, the Invariant Labs tool-poisoning
shape). Treat tool *output* as data, never as instructions. The starter does no such
defence on purpose — adding it is your "fix".
"""

import argparse
import os
import re
import sys
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
RUNBOOKS = DATA_DIR / "runbooks"


def _search_runbooks(query: str, limit: int = 3) -> list[dict]:
    """Naive keyword search over the seed runbook corpus.

    Deliberately simple (substring/term overlap) so the mechanism is legible. Replace
    with real RAG (embeddings + ChromaDB) when you build the copilot — the seed corpus
    lives in data/runbooks/ and the stack already ships ChromaDB + nomic-embed-text.
    """
    terms = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
    hits = []
    if not RUNBOOKS.exists():
        return hits
    for path in sorted(RUNBOOKS.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        low = text.lower()
        score = sum(low.count(t) for t in terms)
        if score > 0:
            # First non-empty, non-heading line as a snippet.
            snippet = next(
                (ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")),
                "",
            )
            hits.append({"runbook": path.name, "score": score, "snippet": snippet[:200]})
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:limit]


def _run_mcp_server() -> None:
    try:
        from fastmcp import FastMCP
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastmcp>=0.9"], check=True)
        from fastmcp import FastMCP

    mcp = FastMCP(
        name="capstone-incident-tool",
        instructions="Look up incident-response runbooks from the local SOC corpus.",
    )

    @mcp.tool()
    def lookup_incident(query: str) -> list[dict]:
        """Search the SOC runbook corpus for runbooks relevant to a query.

        Args:
            query: A natural-language description of the situation (e.g.
                "ransomware on a workstation", "leaked S3 bucket", "prompt injection").

        Returns a ranked list of {runbook, score, snippet}. Returns [] if nothing matches.
        """
        return _search_runbooks(query)

    mcp.run()


def _selftest() -> int:
    print(f"[selftest] runbook corpus: {RUNBOOKS}")
    if not RUNBOOKS.exists():
        print("[selftest] FAIL: runbook corpus not found", file=sys.stderr)
        return 1
    n = len(list(RUNBOOKS.glob("*.md")))
    print(f"[selftest] {n} runbook(s) found")
    for q in ("ransomware on a workstation", "public s3 bucket", "prompt injection"):
        hits = _search_runbooks(q)
        top = hits[0]["runbook"] if hits else "(no match)"
        print(f"[selftest] query={q!r:35s} -> top: {top}")
    if n == 0:
        print("[selftest] FAIL: corpus is empty", file=sys.stderr)
        return 1
    print("[selftest] OK")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Capstone stub MCP incident tool")
    ap.add_argument("--selftest", action="store_true", help="run tool logic directly, no MCP client")
    args = ap.parse_args()
    sys.exit(_selftest() if args.selftest else (_run_mcp_server() or 0))
