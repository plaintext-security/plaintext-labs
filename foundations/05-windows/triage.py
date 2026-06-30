#!/usr/bin/env python3
"""
Windows Triage Lab — analyze a bundled EVTX-shaped event log sample.

Models the Get-WinEvent analysis you'd run on a Windows host.
For the live VM steps (local admin enumeration, auto-start services,
Run keys), see the companion PowerShell script: collect.ps1

Usage:
    python3 triage.py             # demo: analyze bundled sample
    python3 triage.py my_events.json  # analyze your own exported JSON
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DIVIDER = "─" * 64

LOGON_TYPES = {
    2:  "Interactive (local console)",
    3:  "Network (SMB, net use, etc.)",
    4:  "Batch (scheduled task)",
    5:  "Service",
    7:  "Unlock",
    8:  "NetworkCleartext",
    9:  "NewCredentials (runas /netonly)",
    10: "RemoteInteractive (RDP/TS)",
    11: "CachedInteractive",
}

SUSPICIOUS_LOGON_TYPES = {3, 9, 10}  # lateral movement, RDP
EXTERNAL_PREFIX_EXCLUSIONS = {"127.", "10.", "192.168.", "172.16.", "172.17.",
                               "172.18.", "172.19.", "172.20.", "172.21.", "172.22.",
                               "172.23.", "172.24.", "172.25.", "172.26.", "172.27.",
                               "172.28.", "172.29.", "172.30.", "172.31.", "-", "::1"}

EVENT_LABELS = {
    4624: "Logon success",
    4625: "Logon failure",
    4688: "Process created",
    4698: "Scheduled task created",
    4657: "Registry value modified",
    7045: "New service installed",
}


def is_external(ip: str) -> bool:
    if not ip or ip == "-":
        return False
    return not any(ip.startswith(p) for p in EXTERNAL_PREFIX_EXCLUSIONS)


def analyze(events: list[dict]) -> None:
    print("=" * 64)
    print("Windows Event Log Triage")
    print(f"Loaded {len(events)} event(s)")
    print("=" * 64)

    # ── Event ID breakdown ──────────────────────────────────────────────
    from collections import Counter
    id_counts = Counter(e["EventID"] for e in events)
    print(f"\n{DIVIDER}")
    print("[Event ID breakdown]")
    print(DIVIDER)
    for eid, count in sorted(id_counts.items()):
        label = EVENT_LABELS.get(eid, "")
        print(f"  EventID {eid:5d}  ({label:40s})  {count} event(s)")

    # ── Logon events ────────────────────────────────────────────────────
    logons = [e for e in events if e["EventID"] in (4624, 4625)]
    if logons:
        print(f"\n{DIVIDER}")
        print("[Logon events — 4624 success / 4625 failure]")
        print(DIVIDER)
        print()
        for e in logons:
            eid = e["EventID"]
            ltype = e.get("LogonType", 0)
            ltype_name = LOGON_TYPES.get(ltype, f"Type {ltype}")
            ip = e.get("IpAddress", "-")
            user = f"{e.get('TargetDomainName','')}\\{e.get('TargetUserName','')}"
            ts = e["TimeCreated"][:19]
            status = "SUCCESS" if eid == 4624 else "FAILURE"
            ext_flag = "  ← EXTERNAL IP" if is_external(ip) else ""
            susp_flag = "  ← SUSPICIOUS LOGON TYPE" if eid == 4624 and ltype in SUSPICIOUS_LOGON_TYPES else ""
            print(f"  {ts}  {status}  user={user:<25s}  type={ltype_name}")
            print(f"    Computer={e.get('Computer','?')}  IP={ip}{ext_flag}{susp_flag}")
            if e.get("note"):
                print(f"    Note: {e['note']}")
            print()

    # ── Process-creation events (4688) ──────────────────────────────────
    procs = [e for e in events if e["EventID"] == 4688]
    if procs:
        print(f"\n{DIVIDER}")
        print("[Process creation — 4688]")
        print(DIVIDER)
        print()
        for e in procs:
            ts = e["TimeCreated"][:19]
            new_proc = e.get("NewProcessName", "?")
            parent = e.get("ParentProcessName", "?")
            print(f"  {ts}  {new_proc}")
            print(f"    Parent: {parent}")
            cmd = e.get("CommandLine", "")
            if cmd:
                print(f"    CommandLine: {cmd}")
            if e.get("note"):
                print(f"    Note: {e['note']}")
            # NOTE (lab exercise — 'Automate & own it'): this prints the
            # command line but does NOT yet flag/decode the -EncodedCommand
            # blob. Extending triage.py to catch and base64-decode encoded
            # PowerShell (T1059.001) is the learner's job.
            print()

    # ── Persistence events ──────────────────────────────────────────────
    persist = [e for e in events if e["EventID"] in (4698, 4657, 7045)]
    if persist:
        print(f"\n{DIVIDER}")
        print("[Persistence indicators — scheduled tasks, Run keys, new services]")
        print(DIVIDER)
        print()
        for e in persist:
            eid = e["EventID"]
            ts = e["TimeCreated"][:19]
            label = EVENT_LABELS.get(eid, "")
            print(f"  {ts}  EventID {eid}  ({label})")
            if eid == 4698:
                print(f"    Task: {e.get('TaskName','?')}  →  {e.get('TaskContent','?')}")
            elif eid == 4657:
                print(f"    Key: {e.get('ObjectName','?')}\\{e.get('ObjectValueName','?')}")
                print(f"    Value: {e.get('NewValue','?')}")
            elif eid == 7045:
                print(f"    Service: {e.get('ServiceName','?')}")
                print(f"    Path: {e.get('ImagePath','?')}")
                # Check for unquoted path with spaces
                path = e.get("ImagePath", "")
                if " " in path and not path.startswith('"'):
                    print(f"    ⚠ Unquoted path with spaces — exploitable (T1574.009)")
            if e.get("note"):
                print(f"    Note: {e['note']}")
            print()

    # ── Key answers ─────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Key answers for the lab]")
    print(DIVIDER)
    print()
    print("  Q: What is the Event ID for a successful logon?")
    print("  A: 4624  (4625 = failure)")
    print()
    print("  Q: Which logon type indicates a remote/RDP logon?")
    print("  A: Type 10 = RemoteInteractive (RDP/TS)")
    print("     Type 3  = Network (lateral movement via SMB)")
    print()
    print("  Q: What Event ID shows a Run key was written (T1547.001)?")
    print("  A: 4657 (Registry Value Set)  or Sysmon EventID 13")
    print()
    print("  Q: What does an unquoted service path (T1574.009) enable?")
    print("  A: If C:\\Program Files (x86)\\Vendor\\Service\\svc.exe is unquoted,")
    print("     Windows searches C:\\Program.exe first — an attacker who can write")
    print("     there gets code execution when the service starts.")
    print()

    # ── PowerShell reference ─────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[PowerShell commands to run on your Windows VM]")
    print(DIVIDER)
    print("""
  # List local administrators
  Get-LocalGroupMember -Group "Administrators"
  net localgroup Administrators

  # List auto-start services
  Get-Service | Where-Object {$_.StartType -eq 'Automatic'} | Select Name, Status, StartType

  # Find Run key entries (persistence check)
  Get-ItemProperty "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
  Get-ItemProperty "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"

  # Query last 50 logon events (EventID 4624) with PowerShell
  Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} -MaxEvents 50 |
    Select TimeCreated,
           @{n='User';e={$_.Properties[5].Value}},
           @{n='Type';e={$_.Properties[8].Value}},
           @{n='IP';e={$_.Properties[18].Value}} |
    Format-Table -AutoSize

  # Open a downloaded .evtx file
  Get-WinEvent -Path C:\\path\\to\\sample.evtx | Select -First 20 | Format-List
""")


def demo() -> None:
    sample = DATA_DIR / "evtx_sample.json"
    events = json.loads(sample.read_text())
    analyze(events)
    print(f"{'=' * 64}")
    print("Deliverable: windows-triage.md with:")
    print("  - The two attacker moves by Event ID:")
    print("      service install (7045 -> T1543.003) and")
    print("      encoded PowerShell (4688 -> T1059.001)")
    print("  - The decoded -EncodedCommand blob, in plain English")
    print("  - Why a Run key write (EventID 4657) indicates persistence")
    print("  - A 3-sentence attacker timeline")
    print("Next: extend triage.py to flag the 4688 -EncodedCommand")
    print("      automatically (see 'Automate & own it' in lab.md).")
    print(f"{'=' * 64}\n")


def load_events(source: str) -> list[dict]:
    """Load events from native triage JSON, a real .evtx, evtx_dump output, or
    stdin (`-`). The evtx_to_triage aid is imported lazily so the bundled-sample
    demo path stays stdlib-only (no evtx_dump dependency for `make demo`)."""
    if source == "-":
        from evtx_to_triage import normalize_text
        return normalize_text(sys.stdin.read())
    if Path(source).suffix.lower() == ".evtx":
        from evtx_to_triage import convert
        return convert(source)
    text = Path(source).read_text()
    try:
        data = json.loads(text)
        if isinstance(data, list) and (not data or "EventID" in data[0]):
            return data  # native triage schema
    except json.JSONDecodeError:
        pass
    from evtx_to_triage import normalize_text  # saved evtx_dump output
    return normalize_text(text)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze(load_events(sys.argv[1]))
    else:
        demo()
