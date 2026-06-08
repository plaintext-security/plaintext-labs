#!/usr/bin/env python3
"""RITA-style C2 beacon hunting over Zeek conn.log.

RITA (Real Intelligence Threat Analytics) scores network sessions for beacon
likelihood by measuring how *regular* the callback intervals are. A human
checking their email is irregular; a C2 implant calling home on a timer is not.

The beacon score here mirrors RITA's three-component model:
  - Interval score:  low coefficient of variation → high score (regular callbacks)
  - Size score:      consistent bytes per connection → high score (same-size checkins)
  - Count score:     more connections to the same dest → higher suspicion

The hunt surfaces the top-scored session and walks the analyst through the
evidence. Beaconing is probabilistic — a CDN health-check can look like a beacon.
The analyst owns the verdict.

Usage:
    python3 beacon_hunt.py [zeek_dir]    # default: data/zeek/
"""
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

ZEEK_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data" / "zeek"


# ── Zeek TSV parser ──────────────────────────────────────────────────────────

def parse_conn_log(path: Path) -> list[dict]:
    fields: list[str] = []
    records: list[dict] = []
    for line in path.read_text().splitlines():
        if line.startswith("#fields"):
            rest = line[len("#fields"):].lstrip("\t ")
            fields = rest.split("\t")
        elif line.startswith("#") or not line.strip():
            continue
        elif fields:
            vals = line.split("\t")
            records.append(dict(zip(fields, vals + [""] * (len(fields) - len(vals)))))
    return records


# ── Beacon scoring ───────────────────────────────────────────────────────────

def score_session(timestamps: list[float], orig_bytes: list[int]) -> dict:
    """Compute beacon score components for one (src, dst, port) session."""
    if len(timestamps) < 3:
        return {"total": 0, "count": len(timestamps)}

    ts_sorted = sorted(timestamps)
    intervals = [ts_sorted[i+1] - ts_sorted[i] for i in range(len(ts_sorted) - 1)]
    avg_interval = mean(intervals)
    sd_interval  = stdev(intervals) if len(intervals) > 1 else 0.0
    cv_interval  = sd_interval / avg_interval if avg_interval > 0 else 1.0

    # Interval score: 0–100, higher = more regular
    interval_score = max(0, 100 - int(cv_interval * 200))

    # Size score: how consistent are the byte counts?
    if orig_bytes and len(orig_bytes) > 1:
        avg_bytes = mean(orig_bytes)
        sd_bytes  = stdev(orig_bytes)
        cv_bytes  = sd_bytes / avg_bytes if avg_bytes > 0 else 1.0
        size_score = max(0, 100 - int(cv_bytes * 100))
    else:
        size_score = 0

    # Count score: more connections = more suspicious (logarithmic)
    import math
    count_score = min(100, int(math.log2(max(1, len(timestamps))) * 20))

    total = int(interval_score * 0.5 + size_score * 0.3 + count_score * 0.2)

    return {
        "total":          total,
        "interval_score": interval_score,
        "size_score":     size_score,
        "count_score":    count_score,
        "count":          len(timestamps),
        "avg_interval":   avg_interval,
        "sd_interval":    sd_interval,
        "cv_interval":    cv_interval,
        "avg_bytes":      mean(orig_bytes) if orig_bytes else 0,
    }


def hunt(conn_records: list[dict], min_connections: int = 3) -> list[dict]:
    sessions: dict = defaultdict(lambda: {"timestamps": [], "orig_bytes": []})

    for r in conn_records:
        try:
            ts = float(r["ts"])
            key = (r["id.orig_h"], r["id.resp_h"], r["id.resp_p"])
            sessions[key]["timestamps"].append(ts)
            ob = int(r.get("orig_bytes", "0") or "0")
            sessions[key]["orig_bytes"].append(ob)
        except (ValueError, KeyError):
            continue

    results = []
    for (src, dst, dport), data in sessions.items():
        if len(data["timestamps"]) < min_connections:
            continue
        score = score_session(data["timestamps"], data["orig_bytes"])
        results.append({
            "src": src, "dst": dst, "dport": dport,
            **score,
        })

    return sorted(results, key=lambda x: x["total"], reverse=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    conn_path = ZEEK_DIR / "conn.log"
    records   = parse_conn_log(conn_path)

    print("=" * 62)
    print("Meridian Financial — Network Beacon Hunt (RITA-style)")
    print(f"Loaded {len(records)} conn records from {conn_path}")
    print("=" * 62)

    results = hunt(records)

    print(f"\n[Ranked beacon candidates — {len(results)} sessions with ≥3 connections]\n")
    print(f"  {'Score':>5}  {'Connections':>11}  {'Avg interval':>12}  {'CV':>6}  {'Src':>12}  Dst:Port")
    print(f"  {'-'*5}  {'-'*11}  {'-'*12}  {'-'*6}  {'-'*12}  {'-'*20}")
    for r in results:
        print(f"  {r['total']:>5}  {r['count']:>11}  {r['avg_interval']:>10.0f}s  "
              f"  {r['cv_interval']:>5.3f}  {r['src']:>12}  {r['dst']}:{r['dport']}")

    if not results:
        print("  (no candidates found)")
        return 0

    top = results[0]
    print(f"\n{'─'*62}")
    print(f"[Deep dive — top candidate (score {top['total']}/100)]")
    print(f"  Host:            {top['src']}")
    print(f"  Destination:     {top['dst']}:{top['dport']}")
    print(f"  Connections:     {top['count']}")
    print(f"  Avg interval:    {top['avg_interval']:.0f}s  (~{top['avg_interval']/60:.1f} min)")
    print(f"  Interval stdev:  {top['sd_interval']:.1f}s")
    print(f"  Interval CV:     {top['cv_interval']:.3f}  (CV < 0.10 = very regular)")
    print(f"  Avg orig bytes:  {int(top['avg_bytes'])} bytes/connection")
    print(f"\n  Score components:")
    print(f"    Interval regularity:  {top['interval_score']}/100  (weight 50%)")
    print(f"    Byte-size consistency:{top['size_score']}/100  (weight 30%)")
    print(f"    Connection count:     {top['count_score']}/100  (weight 20%)")
    print(f"    ────────────────────────")
    print(f"    Total beacon score:   {top['total']}/100")

    # Analysis
    print(f"\n  Analysis:")
    if top["cv_interval"] < 0.10:
        print(f"  ✓ Extremely regular intervals (CV={top['cv_interval']:.3f}) — "
              f"humans don't behave this way.")
    elif top["cv_interval"] < 0.20:
        print(f"  ~ Regular intervals (CV={top['cv_interval']:.3f}) — could be a CDN or update service.")
    else:
        print(f"  ~ Irregular intervals (CV={top['cv_interval']:.3f}) — less characteristic of C2.")

    if top["total"] >= 70:
        print(f"  ⚠ HIGH beacon score — likely automated C2 callback.")
        print(f"     Verdict: C2 CANDIDATE — investigate {top['dst']} in threat intel.")
    elif top["total"] >= 40:
        print(f"  ~ MEDIUM beacon score — worth investigating; could be a legitimate updater.")
    else:
        print(f"  ○ LOW beacon score — likely benign periodic traffic.")

    # Show all candidates with verdict
    if len(results) > 1:
        print(f"\n{'─'*62}")
        print("[Analyst notes on lower-ranked sessions]")
        for r in results[1:]:
            if r["cv_interval"] > 0.4:
                note = "irregular — likely human/CDN traffic"
            elif r["count"] < 5:
                note = "too few connections for confidence"
            else:
                note = "regular but lower count"
            print(f"  Score {r['total']:>3}: {r['src']} → {r['dst']}:{r['dport']}  — {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
