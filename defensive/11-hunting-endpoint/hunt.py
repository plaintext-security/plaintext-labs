#!/usr/bin/env python3
"""Hypothesis-driven endpoint hunt over Sysmon event data.

This harness loads Sysmon-shaped JSON events into SQLite so you can
query them with real SQL — the same pattern as Velociraptor VQL or
osquery, without the infrastructure overhead.

Usage:
    python3 hunt.py            # demo mode — runs the Meridian hunt
    python3 hunt.py --shell    # interactive SQL REPL
"""
import base64
import json
import re
import sqlite3
import sys
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "sysmon_events.json"

DIVIDER = "─" * 62


def load_db(path: Path) -> sqlite3.Connection:
    records = json.loads(path.read_text())
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Collect all keys across all records to build a single flat table.
    all_keys: list[str] = []
    seen: set[str] = set()
    for r in records:
        for k in r:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
    cols = ", ".join(f'"{k}" TEXT' for k in all_keys)
    conn.execute(f"CREATE TABLE events ({cols})")
    for r in records:
        row = {k: str(r[k]) if r.get(k) is not None else None for k in all_keys}
        placeholders = ", ".join("?" for _ in all_keys)
        conn.execute(
            f"INSERT INTO events VALUES ({placeholders})",
            [row.get(k) for k in all_keys],
        )
    conn.commit()
    return conn


def query(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    return conn.execute(sql).fetchall()


def print_rows(rows: list[sqlite3.Row], cols: list[str] | None = None) -> None:
    if not rows:
        print("  (no results)")
        return
    if cols is None:
        cols = list(rows[0].keys())
    for row in rows:
        for col in cols:
            val = row[col]
            if val and len(val) > 100:
                val = val[:97] + "…"
            if val:
                print(f"  {col}: {val}")
        print()


def decode_b64_command(cmdline: str) -> str | None:
    m = re.search(r"-enc(?:odedcommand)?\s+([A-Za-z0-9+/=]+)", cmdline, re.IGNORECASE)
    if not m:
        return None
    try:
        return base64.b64decode(m.group(1)).decode("utf-16-le", errors="replace")
    except Exception:
        return None


# ── Demo hunt ────────────────────────────────────────────────────────────────

def demo(conn: sqlite3.Connection) -> int:
    print("=" * 62)
    print("Meridian Financial — Endpoint Hunt")
    print(f"Loaded {conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]} Sysmon events")
    print("=" * 62)

    print("""
Hypothesis: An attacker used a malicious Office macro to establish
persistence via a scheduled task or registry Run key on jsmith's
workstation (T1059.001 + T1547.001).

Source: threat-intel tip — jsmith downloaded an unusual .docm file.
""")

    # Step 1: Was a suspicious Office document opened?
    print(DIVIDER)
    print("Step 1 — Office document execution (EventID 1, WINWORD parent of cmd/ps1)")
    print()
    office_spawn = query(conn, """
        SELECT UtcTime, ProcessId, Image, CommandLine, ParentImage
        FROM events
        WHERE EventID = '1'
          AND ParentImage LIKE '%WINWORD%'
        ORDER BY UtcTime
    """)
    if office_spawn:
        print(f"  ✓ Found {len(office_spawn)} process(es) spawned by WINWORD.EXE:\n")
        print_rows(office_spawn, ["UtcTime", "ProcessId", "Image", "CommandLine"])
    else:
        print("  ✗ No suspicious Office macro spawning found.")

    # Step 2: Was an encoded PowerShell command used?
    print(DIVIDER)
    print("Step 2 — Encoded PowerShell (T1059.001 obfuscation indicator)")
    print()
    ps_enc = query(conn, """
        SELECT UtcTime, ProcessId, CommandLine
        FROM events
        WHERE EventID = '1'
          AND Image LIKE '%powershell.exe'
          AND CommandLine LIKE '%-enc%'
        ORDER BY UtcTime
    """)
    if ps_enc:
        print(f"  ✓ Found {len(ps_enc)} encoded PowerShell invocation(s):\n")
        for row in ps_enc:
            print(f"  PID {row['ProcessId']} @ {row['UtcTime']}")
            decoded = decode_b64_command(row["CommandLine"])
            if decoded:
                print(f"  Decoded payload → {decoded}")
            print()
    else:
        print("  ✗ No encoded PowerShell found.\n")

    # Step 3: Was a scheduled task created?
    print(DIVIDER)
    print("Step 3 — Scheduled task creation (T1053.005)")
    print()
    schtasks = query(conn, """
        SELECT UtcTime, ProcessId, CommandLine, ParentImage
        FROM events
        WHERE EventID = '1'
          AND Image LIKE '%schtasks.exe'
        ORDER BY UtcTime
    """)
    if schtasks:
        print(f"  ✓ Found {len(schtasks)} schtasks.exe execution(s):\n")
        print_rows(schtasks, ["UtcTime", "ProcessId", "CommandLine", "ParentImage"])
    else:
        print("  ✗ No scheduled task creation found.\n")

    # Step 4: Was a Run key modified?
    print(DIVIDER)
    print("Step 4 — Registry Run key persistence (T1547.001)")
    print()
    runkeys = query(conn, """
        SELECT UtcTime, ProcessId, TargetObject, Details, Image
        FROM events
        WHERE EventID = '13'
          AND TargetObject LIKE '%\\CurrentVersion\\Run%'
        ORDER BY UtcTime
    """)
    if runkeys:
        print(f"  ✓ Found {len(runkeys)} Run key write(s):\n")
        print_rows(runkeys, ["UtcTime", "TargetObject", "Details", "Image"])
    else:
        print("  ✗ No Run key modifications found.\n")

    # Step 5: Was a dropper tool (certutil) used?
    print(DIVIDER)
    print("Step 5 — LOLBin download (certutil, T1105 / T1218)")
    print()
    lolbin = query(conn, """
        SELECT UtcTime, ProcessId, CommandLine, ParentImage
        FROM events
        WHERE EventID = '1'
          AND Image LIKE '%certutil.exe'
        ORDER BY UtcTime
    """)
    if lolbin:
        print(f"  ✓ Found {len(lolbin)} certutil.exe execution(s):\n")
        print_rows(lolbin, ["UtcTime", "ProcessId", "CommandLine", "ParentImage"])
    else:
        print("  ✗ No certutil executions found.\n")

    # Step 6: Network connection to attacker C2
    print(DIVIDER)
    print("Step 6 — Network pivot — did the payload phone home? (EventID 3)")
    print()
    c2_net = query(conn, """
        SELECT UtcTime, Image, ProcessId, DestinationIp, DestinationPort
        FROM events
        WHERE EventID = '3'
          AND DestinationIp NOT IN ('142.250.185.46','40.101.5.130','8.8.8.8')
        ORDER BY UtcTime
    """)
    if c2_net:
        print(f"  ✓ Found {len(c2_net)} non-baseline network connection(s):\n")
        print_rows(c2_net, ["UtcTime", "Image", "ProcessId", "DestinationIp", "DestinationPort"])
    else:
        print("  ✗ No non-baseline network connections found.\n")

    # Step 7: Was the payload executed later?
    print(DIVIDER)
    print("Step 7 — Payload execution — did the dropped binary run?")
    print()
    payload_exec = query(conn, """
        SELECT UtcTime, ProcessId, ParentProcessId, Image, CommandLine, ParentImage
        FROM events
        WHERE EventID = '1'
          AND Image LIKE '%updater.exe'
        ORDER BY UtcTime
    """)
    if payload_exec:
        print(f"  ✓ Dropped payload executed {len(payload_exec)} time(s):\n")
        print_rows(payload_exec, ["UtcTime", "ProcessId", "ParentImage", "Image", "CommandLine"])
    else:
        print("  ✗ Payload execution not observed in this window.\n")

    # Verdict
    print("=" * 62)
    print("Hunt verdict")
    print("=" * 62)
    print("""
Hypothesis CONFIRMED. Evidence chain:

  1. jsmith opened Invoice_March2024.docm (WINWORD.EXE)
  2. Macro spawned cmd.exe → powershell.exe -enc (encoded payload)
  3. PowerShell dropped stage1.exe to %TEMP%
  4. certutil.exe fetched updater.exe from 185.220.101.47
  5. schtasks.exe created "WindowsUpdateHelper" (ONLOGON trigger)
  6. reg.exe wrote HKCU Run\\WindowsUpdateHelper
  7. updater.exe later ran via taskhostw.exe (scheduled task)

Persistence mechanism: T1547.001 (Run key) + T1053.005 (scheduled task)
C2 indicator: 185.220.101.47 (feeds → module 14 threat-intel enrichment)

Detection idea (draft Sigma rule):
  title: Office Macro Spawns Encoded PowerShell
  condition: EventID=1 AND ParentImage ENDSWITH WINWORD.EXE|EXCEL.EXE
             AND CommandLine CONTAINS -enc
  response: isolate host, revoke jsmith credentials, pull full memory
""")
    return 0


def shell(conn: sqlite3.Connection) -> int:
    print("Endpoint hunt REPL — type SQL queries, 'cols' to list columns, 'exit' to quit.\n")
    print("Table: events")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(events)").fetchall()]
    print(f"Columns: {', '.join(cols)}\n")
    while True:
        try:
            line = input("hunt> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line.lower() == "exit":
            break
        if line.lower() == "cols":
            print(", ".join(cols))
            continue
        try:
            rows = query(conn, line)
            print_rows(rows)
            print(f"  [{len(rows)} row(s)]\n")
        except sqlite3.Error as e:
            print(f"  Error: {e}\n")
    return 0


if __name__ == "__main__":
    conn = load_db(DATA_FILE)
    if "--shell" in sys.argv:
        sys.exit(shell(conn))
    sys.exit(demo(conn))
