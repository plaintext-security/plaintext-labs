#!/usr/bin/env python3
"""Plaintext Curriculum MCP server — a context-aware tutor over the Plaintext curriculum.

Exposes the Plaintext security curriculum (tracks, module concepts, Learn paths, and labs)
to any MCP-compatible client — Claude Desktop, Claude Code, Cursor — as a set of tools,
resources, and a tutor prompt. Point your client at this server and the model can pull the
real module text on demand instead of hallucinating it: "walk me through the MCP servers
module", "what's the Learn path for web injection", "what should I study after RAG".

Tools (the model calls these):
  - list_tracks()                         The 13-track curriculum map.
  - list_modules(track)                   Modules in a track, in order.
  - get_module(ref)                       A module's concept ("the bridge") + objective.
  - get_learn_path(ref)                   The curated, grouped Learn resources for a module.
  - get_lab(ref)                          The hands-on lab: scenario, steps, deliverables.
  - search_curriculum(query)              Keyword search across every module and lab.
  - suggest_next(ref)                     The next module in the same track.
  - curriculum_stats()                    Counts (tracks / modules / labs / resources).

Resources (the model can read these as context):
  - curriculum://overview                 The whole-curriculum map as Markdown.
  - curriculum://module/{track}/{module}  A single module's full README text.

Prompt:
  - tutor(topic)                          A ready-made "be my Plaintext tutor" prompt.

The curriculum text is parsed by curriculum.py (pure stdlib). This file is only the MCP
wiring. Source defaults to the bundled snapshot in ../data/tracks; set CURRICULUM_DIR to a
full `plaintext/tracks` checkout to tutor over the entire curriculum.

Run:
    python3 server/server.py            # stdio transport (what MCP clients launch)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Import the parser whether launched as a script (`python server/server.py`, where the
# script's own dir is on sys.path) or as a module (`python -m server.server`).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum import Curriculum, Module, default_curriculum_dir  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - helpful message when deps are missing
    sys.stderr.write(
        "error: the 'mcp' package is required to run the server.\n"
        "       pip install -r server/requirements.txt\n"
        "       (curriculum.py and the smoke test run without it.)\n"
    )
    raise

# Build the index once at import time so every tool call is a fast in-memory lookup.
CURRICULUM = Curriculum(default_curriculum_dir())

mcp = FastMCP(
    name="plaintext-curriculum",
    instructions=(
        "You are a tutor for the Plaintext open security-education curriculum. Use these "
        "tools to ground every answer in the actual module text — never invent module "
        "numbers, Learn links, or lab steps. Workflow: call list_tracks / search_curriculum "
        "to locate the right module, get_module for the concept, get_learn_path for the "
        "study resources, get_lab for the hands-on project, and suggest_next to chart a path. "
        "Always cite the module by its ref (e.g. '12-ai-augmented-ops/05-building-mcp-servers')."
    ),
)


def _module_or_error(ref: str) -> Module | dict:
    mod = CURRICULUM.get_module(ref)
    if mod is None:
        return {
            "error": f"No module found for ref '{ref}'.",
            "hint": "Use list_tracks() then list_modules(track), or search_curriculum(query). "
                    "A ref looks like '12-ai-augmented-ops/05-building-mcp-servers' "
                    "(loose forms like 'ai/5' also work).",
        }
    return mod


# --------------------------------------------------------------------------- tools


@mcp.tool()
def list_tracks() -> dict:
    """List all tracks in the Plaintext curriculum (the top-level map).

    Returns each track's ref, title, one-line overview, and module count. Start here to
    orient, then call list_modules(track) to drill into one.
    """
    return {
        "tracks": [
            {
                "ref": tr.track_id,
                "number": tr.number,
                "title": tr.title,
                "modules": len(tr.modules),
                "overview": tr.overview.split("\n\n")[0].strip()[:300],
            }
            for tr in CURRICULUM.tracks
        ]
    }


@mcp.tool()
def list_modules(track: str) -> dict:
    """List the modules of one track, in curriculum order.

    Args:
        track: A track ref, number, or name — '12-ai-augmented-ops', '12', or 'ai'.
    """
    tr = CURRICULUM.get_track(track)
    if tr is None:
        return {"error": f"No track found for '{track}'. Call list_tracks() to see valid refs."}
    return {
        "track": tr.track_id,
        "title": tr.title,
        "modules": [
            {
                "ref": m.ref,
                "number": m.number,
                "title": m.title,
                "has_lab": m.lab_path is not None,
                "summary": m.summary()[:200],
            }
            for m in tr.modules
        ],
    }


@mcp.tool()
def get_module(ref: str) -> dict:
    """Get a module's concept — the 'bridge' prose, objective, and key concepts.

    This is the teaching content (not the lab). Use it to explain a topic. For the study
    links use get_learn_path; for the hands-on project use get_lab.

    Args:
        ref: Module ref, e.g. '12-ai-augmented-ops/05-building-mcp-servers' (loose like 'ai/5' works).
    """
    mod = _module_or_error(ref)
    if isinstance(mod, dict):
        return mod
    return {
        "ref": mod.ref,
        "track": mod.track_id,
        "number": mod.number,
        "title": mod.title,
        "why_this_matters": mod.sections.get("Why this matters", ""),
        "objective": mod.sections.get("Objective", ""),
        "core_idea": mod.sections.get("The core idea", ""),
        "key_concepts": mod.sections.get("Key concepts", ""),
        "ai_acceleration": mod.sections.get("AI acceleration", ""),
        "has_lab": mod.lab_path is not None,
    }


@mcp.tool()
def get_learn_path(ref: str) -> dict:
    """Get the curated, time-boxed Learn path (study resources) for a module.

    Returns the grouped resources — title, URL, the sub-topic group, and the why-line for
    each. This is the opinionated reading/watching list for the topic.

    Args:
        ref: Module ref (e.g. '01-offensive/06-web-injection').
    """
    mod = _module_or_error(ref)
    if isinstance(mod, dict):
        return mod
    return {
        "ref": mod.ref,
        "title": mod.title,
        "resource_count": len(mod.learn),
        "resources": [
            {"group": r.group, "title": r.title, "url": r.url, "why": r.note}
            for r in mod.learn
        ],
    }


@mcp.tool()
def get_lab(ref: str) -> dict:
    """Get a module's hands-on lab — scenario, the ordered 'Do' steps, and deliverables.

    Returns the lab sections as text. Use this when the learner wants to *do* the exercise,
    not just read about it.

    Args:
        ref: Module ref (e.g. '02-defensive/08-detection-as-code').
    """
    mod = _module_or_error(ref)
    if isinstance(mod, dict):
        return mod
    if mod.lab_path is None:
        return {"ref": mod.ref, "title": mod.title, "has_lab": False,
                "message": "This module has no lab.md."}
    s = mod.lab_sections
    return {
        "ref": mod.ref,
        "title": mod.title,
        "has_lab": True,
        "setup": s.get("Setup", ""),
        "scenario": s.get("Scenario", ""),
        "do": s.get("Do", ""),
        "success_criteria": s.get("Success criteria — you're done when", "")
        or s.get("Success criteria", ""),
        "deliverables": s.get("Deliverables", ""),
        "automate_and_own_it": s.get("Automate & own it", ""),
        "connects_forward": s.get("Connects forward", ""),
    }


@mcp.tool()
def search_curriculum(query: str, limit: int = 8) -> dict:
    """Search the whole curriculum (module concepts and labs) for a keyword or phrase.

    Deterministic keyword search across every module README and lab. Returns the best
    matches with a ref, title, score, and a text snippet. Use it to find which module
    covers a topic before fetching it with get_module / get_lab.

    Args:
        query: Search terms, e.g. 'kerberos delegation', 'pcap analysis', 'prompt injection'.
        limit: Max results to return (default 8, capped at 25).
    """
    if not query or not query.strip():
        return {"error": "Query cannot be empty."}
    limit = max(1, min(int(limit), 25))
    results = CURRICULUM.search(query, limit=limit)
    return {
        "query": query,
        "count": len(results),
        "results": [
            {"ref": m.ref, "title": m.title, "score": score, "snippet": snippet}
            for m, score, snippet in results
        ],
    }


@mcp.tool()
def suggest_next(ref: str) -> dict:
    """Suggest the next module to study after the given one (next in the same track).

    Args:
        ref: The module the learner just finished, e.g. '12-ai-augmented-ops/04-rag'.
    """
    mod = _module_or_error(ref)
    if isinstance(mod, dict):
        return mod
    nxt = CURRICULUM.suggest_next(mod.ref)
    if nxt is None:
        return {
            "from": mod.ref,
            "next": None,
            "message": f"'{mod.title}' is the last module in its track. "
                       f"Call list_tracks() to pick the next track.",
        }
    return {
        "from": mod.ref,
        "next": {"ref": nxt.ref, "title": nxt.title, "summary": nxt.summary()[:200]},
    }


@mcp.tool()
def curriculum_stats() -> dict:
    """Return counts for the loaded curriculum: tracks, modules, labs, Learn resources."""
    return CURRICULUM.stats()


# ----------------------------------------------------------------------- resources


@mcp.resource("curriculum://overview")
def overview_resource() -> str:
    """The whole-curriculum map as Markdown — every track and its modules."""
    lines = ["# Plaintext Curriculum Map", ""]
    for tr in CURRICULUM.tracks:
        lines.append(f"## {tr.title}  `({tr.track_id})`")
        for m in tr.modules:
            lab = " · lab" if m.lab_path else ""
            lines.append(f"- `{m.ref}` — {m.title}{lab}")
        lines.append("")
    return "\n".join(lines)


@mcp.resource("curriculum://module/{track}/{module}")
def module_resource(track: str, module: str) -> str:
    """The full README Markdown of a single module (concept + Learn path)."""
    mod = CURRICULUM.get_module(f"{track}/{module}")
    if mod is None:
        return f"# Not found\n\nNo module for '{track}/{module}'."
    return mod.readme_text or f"# {mod.title}\n\n(empty README)"


# -------------------------------------------------------------------------- prompt


@mcp.prompt()
def tutor(topic: str = "") -> str:
    """A ready-made prompt that turns the client into a Plaintext curriculum tutor."""
    focus = f" The learner wants to focus on: {topic}." if topic else ""
    return (
        "Act as my tutor for the Plaintext open security-education curriculum. Use the "
        "plaintext-curriculum MCP tools to ground everything you say in the real module "
        "text — search_curriculum to locate a topic, get_module for the concept, "
        "get_learn_path for the study resources, and get_lab for the hands-on project. "
        "Cite the module ref for anything you pull, and never invent module numbers or "
        f"links.{focus} Start by orienting me with list_tracks() if I haven't picked a track."
    )


if __name__ == "__main__":
    # A tiny self-check so `python3 server/server.py --selfcheck` proves it wired up
    # without needing an MCP client.
    if "--selfcheck" in sys.argv:
        print(json.dumps({"ok": True, **CURRICULUM.stats()}))
        sys.exit(0)
    mcp.run(transport="stdio")
