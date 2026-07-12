"""Streaming ingest — read the feed one row at a time, never the whole thing.

A generator keeps memory flat whether the feed is 100 rows or 100 million. The
copilot writes `json.load(open(f))` / `pd.read_csv(f)` and loads it all; this
yields row by row so `sift` scales to the real URLhaus dump.
"""
from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path


def stream_alerts(path: str | Path) -> Iterator[dict[str, str]]:
    """Yield one alert dict at a time from a CSV feed (constant memory)."""
    with open(path, newline="") as f:
        yield from csv.DictReader(f)
