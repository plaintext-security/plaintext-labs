#!/usr/bin/env python3
"""Offline smoke test for the curriculum MCP server.

Runs with **zero third-party dependencies** (no `mcp` needed) against the bundled
curriculum snapshot, so CI / a learner can prove the parser and query layer work before
ever installing the MCP SDK. Exit 0 = all good; non-zero = a failed assertion.

    python3 tests/smoke_test.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "server"))

from curriculum import Curriculum, default_curriculum_dir  # noqa: E402

PASS = "PASS"
checks = 0
failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global checks
    checks += 1
    status = PASS if cond else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def main() -> int:
    src = default_curriculum_dir()
    print(f"Loading curriculum from: {src}")
    cur = Curriculum(src)

    # 1) The index built and found a non-trivial curriculum.
    stats = cur.stats()
    print(f"Stats: {stats}")
    check("loaded >= 1 track", stats["tracks"] >= 1, str(stats))
    check("loaded >= 1 module", stats["modules"] >= 1, str(stats))
    check("found Learn resources", stats["learn_resources"] >= 1, str(stats))

    # 2) Track resolution: exact, numeric, and loose name forms all resolve.
    any_track = cur.tracks[0]
    check("get_track by exact id", cur.get_track(any_track.track_id) is any_track)
    check("get_track by number", cur.get_track(any_track.number) is any_track)

    # 3) Module resolution: exact ref and loose 'track/number' both work.
    any_mod = cur.all_modules()[0]
    check("get_module by exact ref", cur.get_module(any_mod.ref) is any_mod)
    loose = f"{any_mod.track_id}/{int(any_mod.number)}"  # drop zero-pad
    check("get_module by loose ref", cur.get_module(loose) is any_mod, f"ref={loose}")
    check("unknown ref returns None", cur.get_module("nope/nope") is None)

    # 4) A module README parsed into the expected sections.
    parsed = [m for m in cur.all_modules() if "The core idea" in m.sections]
    check("modules expose 'The core idea'", len(parsed) >= 1,
          f"{len(parsed)} modules had a core-idea section")

    # 5) Learn-path extraction produced real links (title + http url).
    with_learn = [m for m in cur.all_modules() if m.learn]
    check("modules expose a Learn path", len(with_learn) >= 1)
    if with_learn:
        r = with_learn[0].learn[0]
        check("Learn resource has a title", bool(r.title))
        check("Learn resource has an http url", r.url.startswith("http"), r.url)

    # 6) Search returns ranked, relevant results.
    results = cur.search("security", limit=5)
    check("search returns results", len(results) >= 1)
    if results:
        scores = [s for _, s, _ in results]
        check("search results are ranked desc", scores == sorted(scores, reverse=True), str(scores))
    check("empty search returns nothing", cur.search("   ") == [])

    # 7) suggest_next walks the track in order.
    first_track = next((t for t in cur.tracks if len(t.modules) >= 2), None)
    if first_track:
        nxt = cur.suggest_next(first_track.modules[0].ref)
        check("suggest_next gives the following module",
              nxt is not None and nxt.ref == first_track.modules[1].ref,
              f"got {nxt.ref if nxt else None}")

    # 8) The server module imports its tools cleanly (it does NOT import mcp at module
    #    scope for the helpers we test — but we only import if mcp is available).
    try:
        import mcp  # noqa: F401
        sys.path.insert(0, str(ROOT))
        import importlib
        srv = importlib.import_module("server.server")
        out = srv.list_tracks()
        check("server.list_tracks() returns tracks", len(out["tracks"]) == stats["tracks"])
        gm = srv.get_module(any_mod.ref)
        check("server.get_module() returns the title", gm.get("title") == any_mod.title)
        glp = srv.get_learn_path(with_learn[0].ref) if with_learn else {"resource_count": 0}
        check("server.get_learn_path() returns resources", glp["resource_count"] >= 1)
        sc = srv.search_curriculum("network", limit=3)
        check("server.search_curriculum() returns results", sc["count"] >= 0)
    except ImportError:
        print("  [skip] mcp not installed — skipped server-layer checks "
              "(install server/requirements.txt to exercise them)")

    print()
    if failures:
        print(f"SMOKE TEST FAILED: {len(failures)}/{checks} checks failed: {failures}")
        return 1
    print(f"SMOKE TEST PASSED: {checks}/{checks} checks green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
