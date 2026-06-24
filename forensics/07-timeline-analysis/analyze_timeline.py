#!/usr/bin/env python3
"""
Module 07 — Timeline Analysis demo script.
Reads data/timeline.csv (pre-computed plaso-style output) and surfaces key events.

In a real investigation:
    log2timeline.py /tmp/timeline.plaso data/artifacts/
    psort.py -o l2tcsv --slice "2024-03-15T02:00:00" --slice_size 35 /tmp/timeline.plaso
"""
import csv
import sys
import os
from datetime import datetime, timezone

INCIDENT_START = datetime(2024, 3, 15, 2, 0, 0, tzinfo=timezone.utc)
INCIDENT_END   = datetime(2024, 3, 15, 2, 36, 0, tzinfo=timezone.utc)

# Key indicators to flag
HIGH_VALUE_KEYWORDS = [
    "LOG CLEARED", "FAILED LOGON", "LOGON SUCCESS", "PROCESS CREATED",
    "INJECTION", "C2", "SEARCH TERM", "downloaded", "INSTALLED", "ESTABLISHED",
    "restricted"
]

def parse_dt(s):
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None

def load_timeline(path):
    events = []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_dt(row["datetime"])
            if dt:
                row["_dt"] = dt
                events.append(row)
    return sorted(events, key=lambda x: x["_dt"])

def is_high_value(event):
    msg = event["message"].upper()
    return any(kw.upper() in msg for kw in HIGH_VALUE_KEYWORDS)

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    timeline_path = os.path.join(data_dir, "timeline.csv")

    print("\nIR — Super-Timeline Analysis (BEACHHEAD-WS01)")
    print("Incident Window: 2024-03-15 02:00:00 – 02:35:00 UTC\n")

    events = load_timeline(timeline_path)
    incident_events = [e for e in events if INCIDENT_START <= e["_dt"] <= INCIDENT_END]

    print(f"Total events in timeline   : {len(events)}")
    print(f"Events in incident window  : {len(incident_events)}")
    print()

    print("=" * 70)
    print("INCIDENT WINDOW TIMELINE (chronological)")
    print("=" * 70)
    prev_dt = None
    for evt in incident_events:
        dt = evt["_dt"]
        gap = ""
        if prev_dt:
            delta = (dt - prev_dt).total_seconds()
            if delta > 300:
                print(f"\n  *** GAP: {int(delta//60)}m {int(delta%60)}s — no events from any source ***\n")
        flag = " <-- HIGH VALUE" if is_high_value(evt) else ""
        print(f"  {dt.strftime('%H:%M:%S')} [{evt['source']:7s}] {evt['message'][:80]}{flag}")
        prev_dt = dt

    print("\n" + "=" * 70)
    print("HIGH-VALUE EVENTS SUMMARY")
    print("=" * 70)
    for evt in incident_events:
        if is_high_value(evt):
            print(f"  {evt['_dt'].strftime('%H:%M:%S')} | {evt['source_long']}")
            print(f"    {evt['message'][:100]}")

    print("\n" + "=" * 70)
    print("ATTACKER TIMELINE (narrative)")
    print("=" * 70)
    print("""
  02:00 — Malware dropped: svcupd.exe created in C:\\ProgramData (timestomped $SI to 2019)
  02:05 — Browser searches for exfiltration methods (attacker using browser during intrusion)
  02:09 — Failed logon attempt from 10.99.4.22 against Administrator account
  02:09 — update_patch.exe downloaded from pastebin.com (second-stage payload)
  02:10 — Successful network logon as jsmith from 10.99.4.22
  02:11 — Execution chain: svcupd.exe -> cmd.exe -> powershell.exe -enc [reverse shell]
  02:11 — C2 connection established: powershell.exe -> 10.99.4.22:443
  02:11 — Persistence installed: Registry Run key with encoded PowerShell dropper (T1547.001)
  02:12 — notepad.exe injected with PE payload; outbound connection to 10.99.4.22:4444 (T1055)
  02:15 — File access begins on \\\\FILESHARE-SRV01\\finance\\restricted (Q1_2024_payroll.xlsx)
  02:17 — Additional restricted files accessed (board_minutes_confidential.docx)
  02:20 — Service installed for persistence: svcupd as Windows service (T1543.003)
  02:28 — Browser search for log clearing techniques
  02:31 — Security log cleared (Event 1102) — attacker covering tracks (T1070.001)
  02:35 — Memory image captured by IR team

  TOTAL DWELL TIME (from drop to memory capture): ~35 minutes
  C2 IP: 10.99.4.22 (appears in: network logon, C2 connections, reverse shell payload)
""")

if __name__ == "__main__":
    main()
