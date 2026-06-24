#!/usr/bin/env python3
"""Minimal SIEM harness for the SOC.

Demonstrates the four core SIEM operations:
  1. Ingest & normalize multi-source events into a common schema.
  2. Apply correlation rules across event streams.
  3. Fire alerts when rule conditions match.
  4. Query the event store (a real SIEM uses Elasticsearch/OpenSearch;
     here we use SQLite for the same SQL semantics without the infra).

Correlation rules live at the bottom of this file as plain Python
functions. Each rule is decorated with @rule(...) and receives the
event store — it queries it and returns zero or more Alert dicts.

Usage:
    python3 siem.py            # demo mode — ingest, correlate, report
    python3 siem.py --query    # interactive SQL over the event store
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "events.json"
DIVIDER = "─" * 64


# ── Normalizer ────────────────────────────────────────────────────────────────

def normalize(raw: dict) -> dict:
    """Map source-specific field names to a common schema."""
    ev = {
        "source":    raw.get("source", "unknown"),
        "event_id":  str(raw.get("EventID", "")),
        "ts":        raw.get("ts", ""),
        "host":      raw.get("host", ""),
        "user":      raw.get("user", ""),
        "src_ip":    raw.get("src_ip", raw.get("DestinationIp", "")),
        "dst_ip":    raw.get("dst_ip", ""),
        "dst_port":  str(raw.get("dst_port", raw.get("DestinationPort", ""))),
        "process":   raw.get("Image", ""),
        "parent":    raw.get("ParentImage", ""),
        "cmdline":   raw.get("CommandLine", ""),
        "reg_key":   raw.get("TargetObject", ""),
        "reg_val":   raw.get("Details", ""),
        "signature": raw.get("signature", raw.get("message", "")),
        "orig_bytes":str(raw.get("orig_bytes", 0)),
    }
    return ev


# ── Event store ───────────────────────────────────────────────────────────────

def build_store(records: list[dict]) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE events (
            source TEXT, event_id TEXT, ts TEXT, host TEXT, user TEXT,
            src_ip TEXT, dst_ip TEXT, dst_port TEXT, process TEXT,
            parent TEXT, cmdline TEXT, reg_key TEXT, reg_val TEXT,
            signature TEXT, orig_bytes TEXT
        )
    """)
    for r in records:
        ev = normalize(r)
        conn.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            list(ev.values()),
        )
    conn.commit()
    return conn


def q(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    return conn.execute(sql).fetchall()


# ── Rule engine ───────────────────────────────────────────────────────────────

RULES: list = []

def rule(title: str, severity: str, technique: str):
    def decorator(fn):
        RULES.append((title, severity, technique, fn))
        return fn
    return decorator


@rule(
    title="Office Application Spawns Encoded PowerShell",
    severity="HIGH",
    technique="T1059.001 + T1566.001",
)
def rule_office_macro_ps(conn):
    rows = q(conn, """
        SELECT ts, host, user, parent, cmdline
        FROM events
        WHERE source = 'sysmon' AND event_id = '1'
          AND (parent LIKE '%WINWORD%' OR parent LIKE '%EXCEL%' OR parent LIKE '%OUTLOOK%')
          AND cmdline LIKE '%-enc%'
    """)
    alerts = []
    for r in rows:
        alerts.append({
            "host": r["host"], "user": r["user"], "ts": r["ts"],
            "detail": f"Office parent: {Path(r['parent']).name} | cmd: {r['cmdline'][:80]}…",
        })
    return alerts


@rule(
    title="Registry Run Key Persistence",
    severity="HIGH",
    technique="T1547.001",
)
def rule_run_key(conn):
    rows = q(conn, """
        SELECT ts, host, user, reg_key, reg_val
        FROM events
        WHERE source = 'sysmon' AND event_id = '13'
          AND reg_key LIKE '%\\CurrentVersion\\Run%'
          AND reg_val NOT LIKE '%OneDrive%'
          AND reg_val NOT LIKE '%Microsoft%'
    """)
    alerts = []
    for r in rows:
        alerts.append({
            "host": r["host"], "user": r["user"], "ts": r["ts"],
            "detail": f"Key: {r['reg_key'].split(chr(92))[-1]} → {r['reg_val']}",
        })
    return alerts


@rule(
    title="SSH Brute Force — Multiple Failures from Single Source",
    severity="MEDIUM",
    technique="T1110.001",
)
def rule_ssh_brute(conn):
    rows = q(conn, """
        SELECT src_ip, COUNT(*) AS fails, GROUP_CONCAT(DISTINCT user) AS users
        FROM events
        WHERE source = 'sshd' AND event_id = 'auth_fail'
        GROUP BY src_ip
        HAVING fails >= 3
    """)
    alerts = []
    for r in rows:
        alerts.append({
            "host": "SRV-01", "user": r["users"], "ts": "multiple",
            "detail": f"Source {r['src_ip']} — {r['fails']} failures across users: {r['users']}",
        })
    return alerts


@rule(
    title="Brute Force Followed by Successful Login",
    severity="CRITICAL",
    technique="T1110.001 (success)",
)
def rule_ssh_brute_success(conn):
    fail_ips = {r["src_ip"] for r in q(conn, """
        SELECT DISTINCT src_ip FROM events
        WHERE source = 'sshd' AND event_id = 'auth_fail'
        GROUP BY src_ip HAVING COUNT(*) >= 3
    """)}
    success_rows = q(conn, """
        SELECT ts, host, user, src_ip
        FROM events
        WHERE source = 'sshd' AND event_id = 'auth_success'
    """)
    alerts = []
    for r in success_rows:
        if r["src_ip"] in fail_ips:
            alerts.append({
                "host": r["host"], "user": r["user"], "ts": r["ts"],
                "detail": f"Login SUCCESS after brute force from {r['src_ip']} as {r['user']}",
            })
    return alerts


@rule(
    title="Unusually Large Outbound Transfer",
    severity="MEDIUM",
    technique="T1041",
)
def rule_large_outbound(conn):
    rows = q(conn, """
        SELECT ts, host, src_ip, dst_ip, dst_port, orig_bytes
        FROM events
        WHERE source = 'zeek' AND CAST(orig_bytes AS INTEGER) > 1000000
    """)
    alerts = []
    for r in rows:
        mb = int(r["orig_bytes"]) / 1_000_000
        alerts.append({
            "host": r["host"], "user": "", "ts": r["ts"],
            "detail": f"{r['src_ip']} → {r['dst_ip']}:{r['dst_port']} — {mb:.1f} MB outbound",
        })
    return alerts


@rule(
    title="IDS Alert — PE/EXE Download over HTTP",
    severity="HIGH",
    technique="T1105",
)
def rule_ids_pe_download(conn):
    rows = q(conn, """
        SELECT ts, host, src_ip, dst_ip, signature
        FROM events
        WHERE source = 'suricata' AND signature LIKE '%PE EXE%'
    """)
    alerts = []
    for r in rows:
        alerts.append({
            "host": r["host"], "user": "", "ts": r["ts"],
            "detail": f"{r['src_ip']} → {r['dst_ip']} | sig: {r['signature']}",
        })
    return alerts


# ── Reporting ─────────────────────────────────────────────────────────────────

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def demo(conn: sqlite3.Connection) -> int:
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    sources = conn.execute(
        "SELECT source, COUNT(*) AS n FROM events GROUP BY source ORDER BY n DESC"
    ).fetchall()

    print("=" * 64)
    print("SOC SIEM — Correlation Run")
    print("=" * 64)
    print(f"\n[Ingested {total} normalized events]")
    for row in sources:
        print(f"  {row['source']:12s}  {row['n']:>3} events")

    all_alerts: list[tuple[str, str, str, dict]] = []
    for title, severity, technique, fn in RULES:
        hits = fn(conn)
        for h in hits:
            all_alerts.append((title, severity, technique, h))

    all_alerts.sort(key=lambda x: SEVERITY_ORDER.get(x[1], 9))

    print(f"\n[{len(all_alerts)} alert(s) fired across {len(RULES)} correlation rules]\n")
    print(DIVIDER)

    for title, severity, technique, hit in all_alerts:
        sev_label = {"CRITICAL": "!!! CRITICAL", "HIGH": "!!  HIGH    ",
                     "MEDIUM":   " !  MEDIUM  ", "LOW": "    LOW    "}.get(severity, severity)
        print(f"{sev_label}  {title}")
        print(f"    ATT&CK: {technique}")
        print(f"    Time:   {hit['ts']}")
        if hit.get("host"):
            print(f"    Host:   {hit['host']}")
        if hit.get("user"):
            print(f"    User:   {hit['user']}")
        print(f"    Detail: {hit['detail']}")
        print()

    print(DIVIDER)
    print("\n[Dashboard summary — alert count by severity]")
    from collections import Counter
    severity_counts = Counter(a[1] for a in all_alerts)
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = severity_counts.get(sev, 0)
        bar = "█" * count
        print(f"  {sev:8s}  {bar or '(none)':20s}  {count}")

    print(f"""
[Analyst recommendation]
  Priority 1 — Investigate WIN10-01 immediately: Office macro →
    encoded PS → certutil download → Run key persistence + IDS hit.
  Priority 2 — Contain 45.155.204.42: brute force succeeded as
    svc-backup; rotate credentials, review access logs.
  Cross-reference: 185.220.101.47 appears in both the Windows exfil
    (8.6 MB) and the IDS PE-download alert — same C2 as module 12.
""")
    return 0


def query_shell(conn: sqlite3.Connection) -> int:
    print("SIEM query shell — type SQL, 'cols' for schema, 'exit' to quit.\n")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(events)")]
    print(f"Table: events | Columns: {', '.join(cols)}\n")
    while True:
        try:
            line = input("siem> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line or line.lower() == "exit":
            break
        if line.lower() == "cols":
            print(", ".join(cols))
            continue
        try:
            rows = conn.execute(line).fetchall()
            for row in rows:
                print(dict(row))
            print(f"[{len(rows)} row(s)]\n")
        except sqlite3.Error as e:
            print(f"Error: {e}\n")
    return 0


if __name__ == "__main__":
    records = json.loads(DATA_FILE.read_text())
    conn = build_store(records)
    if "--query" in sys.argv:
        sys.exit(query_shell(conn))
    sys.exit(demo(conn))
