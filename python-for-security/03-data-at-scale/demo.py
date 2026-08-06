#!/usr/bin/env python3
"""Reference demo for Lab 03 — Data at Scale & Structured Logs.

Runs over a REAL Suricata `eve.json` — the events Suricata (ET Open) emitted over the
Malware-Traffic-Analysis.net 2024-07-30 "You dirty rat!" STRRAT infection capture
(875 events: 114 alerts incl. "ET MALWARE STRRAT CnC Checkin", plus dns/tls/flow/smb/...).

It shows the three techniques the copilot skips on a feed this size:
  1. STREAM the parse — validate each line into the EVE `AlertEvent` model, flat memory,
     and prove it by replaying the real corpus 200x (~175k events) while memory stays put;
     the copilot's slurp-into-a-list balloons.
  2. answer triage questions with a duckdb columnar query over real EVE fields
     (top alert.signature, loudest-talker dest_ip, per-hour volume) — not a Python loop.
  3. emit structlog JSON events over real fields (signature, dest_ip, verdict) — not print().

The full lab regenerates a much larger `eve.json` by running Suricata over the fetched PCAP;
here the committed 875-event corpus is REPLAYED to demonstrate scale offline and deterministically.
"""
from __future__ import annotations

import sys
import tracemalloc
from pathlib import Path

import duckdb

LAB = Path(__file__).parent
DATA = LAB / "data" / "eve.json"
sys.path.insert(0, str(LAB / "sift_reference"))
from sift.obs import get_logger, verdict_for_severity  # noqa: E402
from sift.stream import StreamStats, stream_alerts  # noqa: E402

DIVIDER = "─" * 64
REPLAY = 200  # replay the real corpus this many times → ~175k events streamed


def section(t: str) -> None:
    print(f"\n{DIVIDER}\n{t}\n{DIVIDER}")


def _mb(n_bytes: int) -> float:
    return n_bytes / (1024 * 1024)


def main() -> int:
    log = get_logger()

    corpus_lines = sum(1 for line in DATA.open() if line.strip())
    section(f"Corpus: real Suricata eve.json — {corpus_lines} events (STRRAT infection)")

    # 1a. STREAM the real feed, replayed REPLAY× → ~175k events, at flat memory.
    section(f"1. Stream the real feed replayed {REPLAY}× (constant memory)")
    stats = StreamStats()
    tracemalloc.start()
    for _ in range(REPLAY):
        for _event in stream_alerts(DATA, stats):
            pass  # generator: one validated AlertEvent at a time, nothing accumulates
    _, stream_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  streamed {stats.read:,} events → {stats.alerts:,} alerts validated, "
          f"{stats.quarantined:,} quarantined (non-alert/malformed)")
    print(f"  peak memory while streaming: {_mb(stream_peak):.1f} MB (flat, independent of feed size)")

    # 1b. The copilot's default: slurp every event into a list. It balloons.
    tracemalloc.start()
    slurped = []
    import json
    for _ in range(REPLAY):
        with DATA.open() as f:
            slurped.extend(json.loads(line) for line in f if line.strip())
    _, slurp_peak = tracemalloc.get_traced_memory()
    slurped_len = len(slurped)
    del slurped
    tracemalloc.stop()
    print(f"  slurp-into-a-list held {slurped_len:,} dicts → "
          f"peak memory: {_mb(slurp_peak):.1f} MB ({slurp_peak / max(stream_peak, 1):.0f}× the stream)")

    # 2. Triage questions via duckdb columnar query over REAL EVE fields (no Python loops).
    section("2. Columnar triage via duckdb (SQL over real eve.json)")
    con = duckdb.connect()
    con.execute(
        "CREATE VIEW eve AS "
        "SELECT json_extract_string(json, '$.event_type')       AS event_type, "
        "       json_extract_string(json, '$.alert.signature')  AS signature, "
        "       CAST(json_extract_string(json, '$.alert.severity') AS INTEGER) AS severity, "
        "       json_extract_string(json, '$.dest_ip')          AS dest_ip, "
        "       json_extract_string(json, '$.timestamp')        AS ts "
        f"FROM read_json_objects('{DATA}', format='newline_delimited')"
    )

    print("  top alert.signature by count:")
    top_sigs = con.execute(
        "SELECT signature, count(*) n FROM eve WHERE event_type='alert' "
        "GROUP BY signature ORDER BY n DESC LIMIT 20"
    ).fetchall()
    for sig, n in top_sigs[:5]:
        print(f"    {n:>4}  {sig}")

    print("  loudest-talker dest_ip (alerts):")
    top_dest = con.execute(
        "SELECT dest_ip, count(*) n FROM eve WHERE event_type='alert' "
        "GROUP BY dest_ip ORDER BY n DESC LIMIT 5"
    ).fetchall()
    for ip, n in top_dest:
        print(f"    {n:>4}  {ip}")

    print("  alert volume per hour:")
    per_hour = con.execute(
        "SELECT substr(ts, 1, 13) hour_bucket, count(*) n FROM eve WHERE event_type='alert' "
        "GROUP BY hour_bucket ORDER BY hour_bucket"
    ).fetchall()
    for hour_bucket, n in per_hour:
        print(f"    {hour_bucket}:00  {n:>4}")

    # A stretch-flavoured columnar query over the growing union: non-alert event mix.
    event_mix = con.execute(
        "SELECT event_type, count(*) n FROM eve GROUP BY event_type ORDER BY n DESC"
    ).fetchall()

    # 3. Structured JSON logs over REAL EVE fields (searchable events, not print()).
    section("3. Structured JSON logs (signature, dest_ip, verdict)")
    top_sig, top_sig_n = top_sigs[0]
    top_ip, top_ip_n = top_dest[0]
    # verdict from the loudest signature's severity
    sev = con.execute(
        "SELECT severity FROM eve WHERE event_type='alert' AND signature=? LIMIT 1",
        [top_sig],
    ).fetchone()[0]
    log.info(
        "triaged",
        signature=top_sig,
        dest_ip=top_ip,
        hits=top_sig_n,
        verdict=verdict_for_severity(sev),
    )
    log.info(
        "triage_summary",
        events_streamed=stats.read,
        alerts=stats.alerts,
        quarantined=stats.quarantined,
        distinct_signatures=len(top_sigs),
        loudest_talker=top_ip,
        loudest_talker_hits=top_ip_n,
        event_types={et: n for et, n in event_mix},
    )

    # Result — assert the real-feed invariants (do not weaken these).
    section("Result")
    ok = (
        stats.read == corpus_lines * REPLAY
        and stats.alerts == 114 * REPLAY
        and stats.quarantined == (corpus_lines - 114) * REPLAY
        and stream_peak < slurp_peak            # streaming stays flat; slurp balloons
        and "STRRAT" in top_sig                 # the real CnC signature dominates
        and top_ip == "141.98.10.79"            # the real STRRAT CnC dest_ip
        and verdict_for_severity(sev) == "malicious"
    )
    print("  streamed at scale, queried columnar, logged structured over real EVE ✓" if ok
          else "  DEMO FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
