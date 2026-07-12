#!/usr/bin/env python3
"""Reference demo for Lab 03 — Data at Scale & Structured Logs.

Generates a large feed, then shows the three techniques the copilot skips:
  1. STREAM the parse (flat memory) instead of loading the whole file,
  2. answer a triage question with a duckdb columnar query (not a Python loop),
  3. emit structlog JSON events (not print()).
The learner points the same code at the real URLhaus dump (needs an Auth-Key).
"""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

import duckdb

LAB = Path(__file__).parent
sys.path.insert(0, str(LAB / "sift_reference"))
from sift.obs import get_logger  # noqa: E402
from sift.stream import stream_alerts  # noqa: E402

DIVIDER = "─" * 60
SOURCES = ["suricata", "zeek", "sysmon", "urlhaus", "otx"]
N = 50_000


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def make_feed(path: Path, n: int) -> None:
    # Deterministic synthetic feed — stands in for the real URLhaus CSV dump.
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "source", "indicator", "severity"])
        for i in range(n):
            src = SOURCES[i % len(SOURCES)]
            sev = ["low", "medium", "high", "critical"][i % 4]
            w.writerow([i, src, f"10.0.{i % 256}.{i % 100}", sev])


def main() -> int:
    tmp = Path(tempfile.mkdtemp()) / "feed.csv"
    make_feed(tmp, N)
    log = get_logger()

    section(f"1. Stream {N:,} rows (constant memory — no whole-file load)")
    count = sum(1 for _ in stream_alerts(tmp))   # generator: one row at a time
    print(f"  streamed {count:,} rows without loading the file into memory")

    section("2. Triage question via duckdb columnar query (SQL over the file)")
    rows = duckdb.sql(
        f"SELECT source, count(*) AS n FROM read_csv_auto('{tmp}') "
        "GROUP BY source ORDER BY n DESC"
    ).fetchall()
    for src, n in rows:
        print(f"  {src:<10} {n:>7,}")

    section("3. Structured JSON logs (searchable events, not print())")
    top_source, top_n = rows[0]
    log.info("triage_complete", rows=count, top_source=top_source, top_count=top_n)

    section("Result")
    ok = count == N and sum(n for _, n in rows) == N
    print("  streamed at scale, queried columnar, logged structured ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
