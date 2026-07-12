#!/usr/bin/env python3
"""Reference demo for Lab 06 — Two Surfaces, One Core.

Drives the SAME core through both surfaces and proves they agree:
  1. the typer CLI (via CliRunner),
  2. the FastAPI endpoint (via TestClient),
both returning a byte-identical TriageResult from the shared triage()/models.
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
INDICATOR = {"kind": "domain", "value": "evil-c2.example"}


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def main() -> int:
    section("1. typer CLI surface")
    cli = CliRunner().invoke(cli_app, ["--kind", INDICATOR["kind"], INDICATOR["value"]])
    cli_out = json.loads(cli.stdout)
    print(f"  $ sift scan --kind {INDICATOR['kind']} {INDICATOR['value']}")
    print(f"  -> {cli_out}")

    section("2. FastAPI surface")
    resp = TestClient(api_app).post("/triage", json=INDICATOR)
    api_out = resp.json()
    print(f"  POST /triage {INDICATOR}")
    print(f"  -> {api_out}")

    section("3. Same core → identical result")
    identical = cli_out == api_out
    print(f"  CLI output == API output: {'✓' if identical else '✗'}")

    section("Result")
    ok = cli.exit_code == 0 and resp.status_code == 200 and identical
    print("  one core, two surfaces, identical results ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
