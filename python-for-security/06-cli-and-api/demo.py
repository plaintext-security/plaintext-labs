#!/usr/bin/env python3
"""Reference demo for Lab 06 — Two Surfaces, One Core.

Drives the SAME core over a real Suricata EVE alert through both surfaces and proves
they agree, then proves the shared input model rejects a malformed EVE line:
  1. the typer CLI (via CliRunner) reads the record from data/eve.json,
  2. the FastAPI endpoint (via TestClient) validates the same record as `AlertEvent`,
  3. both return a byte-identical TriageResult from the shared triage()/models,
  4. a malformed EVE line POSTed to the API is rejected with a 422 by that SAME model.

Fully offline and deterministic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sift_reference"))

from fastapi.testclient import TestClient  # noqa: E402
from typer.testing import CliRunner  # noqa: E402

from sift.api import app as api_app  # noqa: E402
from sift.cli import app as cli_app  # noqa: E402

DIVIDER = "─" * 60
DATA = Path(__file__).parent / "data" / "eve.json"
BAD = Path(__file__).parent / "data" / "eve.bad.json"


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def first_alert() -> tuple[int, str]:
    """Return (line index, raw JSON) of the first `alert` event in the corpus."""
    for i, raw in enumerate(DATA.read_text().splitlines()):
        if json.loads(raw).get("event_type") == "alert":
            return i, raw
    raise SystemExit("no alert event in data/eve.json")


def main() -> int:
    idx, raw = first_alert()
    sig = json.loads(raw)["alert"]["signature"]
    print(f"corpus: {DATA.name} — triaging first alert (line {idx}): {sig!r}")

    section("1. typer CLI surface")
    cli = CliRunner().invoke(cli_app, ["triage", str(DATA), "--line", str(idx)])
    cli_out = json.loads(cli.stdout)
    print(f"  $ sift triage data/eve.json --line {idx}")
    print(f"  -> {cli_out}")

    section("2. FastAPI surface")
    client = TestClient(api_app)
    resp = client.post("/triage", content=raw, headers={"content-type": "application/json"})
    api_out = resp.json()
    print(f"  POST /triage  (raw EVE alert line, {resp.status_code})")
    print(f"  -> {api_out}")

    section("3. Same core → identical result")
    identical = cli_out == api_out
    print(f"  CLI output == API output: {'✓' if identical else '✗'}")

    section("4. Malformed EVE → 422 from the shared AlertEvent model")
    bad_lines = BAD.read_text().splitlines()
    labels = ["alert.severity=5 (out of Suricata 1..3)",
              "event_type=dns (no union member yet)",
              "truncated / non-JSON line"]
    all_422 = True
    for label, bad in zip(labels, bad_lines):
        r = client.post("/triage", content=bad, headers={"content-type": "application/json"})
        ok = r.status_code == 422
        all_422 = all_422 and ok
        print(f"  POST /triage  [{label}] -> {r.status_code} {'✓' if ok else '✗ EXPECTED 422'}")

    section("Result")
    ok = cli.exit_code == 0 and resp.status_code == 200 and identical and all_422
    if not ok:
        print("  DEMO FAILED — see above")
        if cli.exit_code != 0:
            print(cli.output)
        return 1
    print("  one core, two surfaces, identical results — malformed EVE rejected 422 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
