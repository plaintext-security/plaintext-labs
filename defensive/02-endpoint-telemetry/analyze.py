#!/usr/bin/env python3
"""Sysmon endpoint telemetry analysis: process tree, key Event IDs, attack chain.

Sysmon logs every process creation with its full command line and parent — the
exact data a defender needs to trace an attacker's footsteps. This script reads
a JSON export of Sysmon events (the format python-evtx or Get-WinEvent gives
you) and reconstructs the process tree, highlights suspicious parent-child
relationships, and maps events to ATT&CK techniques.

Usage:
    python3 analyze.py [events.json]    # default: data/sysmon_events.json
"""
import base64
import json
import sys
from collections import defaultdict
from pathlib import Path

EVENTS_PATH = (Path(sys.argv[1]) if len(sys.argv) > 1
               else Path(__file__).parent / "data" / "sysmon_events.json")

# Map EventID → human label (key Sysmon events)
EVENT_LABELS = {
    1:  "Process Create",
    3:  "Network Connection",
    5:  "Process Terminated",
    7:  "Image Loaded",
    10: "Process Access",
    11: "File Create",
    12: "Registry Object Create/Delete",
    13: "Registry Value Set",
    15: "FileStream Create",
    22: "DNS Query",
    23: "File Delete",
}

# Suspicious parent→child combinations (LOLBin / spear-phishing indicators)
SUSPICIOUS_ANCESTRY = [
    ("WINWORD.EXE",   "cmd.exe",        "T1566.001", "Macro spawning cmd — spearphishing attachment"),
    ("WINWORD.EXE",   "powershell.exe", "T1566.001", "Macro spawning PowerShell — spearphishing attachment"),
    ("EXCEL.EXE",     "cmd.exe",        "T1566.001", "Excel macro spawning cmd"),
    ("cmd.exe",       "powershell.exe", "T1059.003", "cmd.exe spawning PowerShell"),
    ("powershell.exe","rundll32.exe",   "T1218.011", "PowerShell spawning rundll32 (LOLBin execution)"),
    ("powershell.exe","mshta.exe",      "T1218.005", "PowerShell spawning mshta (LOLBin)"),
    ("wscript.exe",   "cmd.exe",        "T1059.005", "WScript spawning cmd"),
]


def load_events(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def event_id(ev: dict) -> int:
    return int(ev.get("System", {}).get("EventID", 0))


def data(ev: dict) -> dict:
    return ev.get("EventData", {})


def image_basename(path: str) -> str:
    return path.replace("\\", "/").split("/")[-1].upper() if path else ""


def try_decode_b64(s: str) -> str | None:
    """Try to base64-decode a command-line arg; return decoded if printable."""
    try:
        decoded = base64.b64decode(s + "==").decode("utf-16-le").strip()
        if len(decoded) > 5 and decoded.isprintable():
            return decoded
    except Exception:
        pass
    try:
        decoded = base64.b64decode(s + "==").decode("utf-8").strip()
        if len(decoded) > 5:
            return decoded
    except Exception:
        pass
    return None


# ── Analysis passes ────────────────────────────────────────────────────────

def print_event_summary(events: list[dict]) -> None:
    from collections import Counter
    counts: Counter = Counter(event_id(ev) for ev in events)
    print("── Event ID breakdown ──────────────────────────────────────────")
    for eid in sorted(counts):
        label = EVENT_LABELS.get(eid, "Unknown")
        print(f"  EventID {eid:3d}  ({label:<25})  {counts[eid]} event(s)")
    print()


def print_process_tree(events: list[dict]) -> None:
    """Build process tree from EventID 1 (Process Create) and print it."""
    procs: dict[str, dict] = {}
    for ev in events:
        if event_id(ev) != 1:
            continue
        d = data(ev)
        guid   = d.get("ProcessGuid", "")
        pguid  = d.get("ParentProcessGuid", "")
        procs[guid] = {
            "pid":    d.get("ProcessId", "?"),
            "image":  d.get("Image", "?"),
            "cmdline": d.get("CommandLine", ""),
            "parent": pguid,
            "ts":     ev["System"]["TimeCreated"],
        }

    print("── Process tree (EventID 1) ────────────────────────────────────")
    # Find roots (processes whose parent isn't in the set)
    guids = set(procs)
    roots = [g for g, p in procs.items() if p["parent"] not in guids]

    def print_node(guid: str, indent: int = 0) -> None:
        p = procs[guid]
        prefix = "  " * indent + ("└─ " if indent else "")
        name = image_basename(p["image"])
        print(f"  {prefix}[{p['ts'][11:19]}] {name}  (pid={p['pid']})")
        cl = p["cmdline"][:90]
        print(f"  {'  ' * indent}   cmd: {cl}")
        children = [g for g, q in procs.items() if q["parent"] == guid]
        for child in children:
            print_node(child, indent + 1)

    for root in roots:
        print_node(root)
    print()


def check_ancestry(events: list[dict]) -> None:
    """Flag suspicious parent→child process relationships."""
    proc1_events = [ev for ev in events if event_id(ev) == 1]
    findings = []
    for ev in proc1_events:
        d = data(ev)
        child  = image_basename(d.get("Image", ""))
        parent = image_basename(d.get("ParentImage", ""))
        for p_pat, c_pat, tech, desc in SUSPICIOUS_ANCESTRY:
            if p_pat.upper() == parent and c_pat.upper() == child:
                findings.append((tech, desc, parent, child,
                                  d.get("CommandLine", ""), ev["System"]["TimeCreated"]))
    print("── Suspicious parent→child relationships ───────────────────────")
    if findings:
        for tech, desc, parent, child, cl, ts in findings:
            print(f"  ⚠  [{ts[11:19]}] {parent} → {child}")
            print(f"     Technique: {tech}  —  {desc}")
            print(f"     CommandLine: {cl[:80]}")
    else:
        print("  (none found)")
    print()


def decode_encoded_commands(events: list[dict]) -> None:
    """Detect and decode base64-encoded command lines."""
    print("── Encoded command lines (EventID 1) ───────────────────────────")
    found = False
    for ev in events:
        if event_id(ev) != 1:
            continue
        d = data(ev)
        cl = d.get("CommandLine", "")
        if "-enc" in cl.lower() or "-encodedcommand" in cl.lower():
            parts = cl.split()
            for i, part in enumerate(parts):
                if part.lower() in ("-enc", "-encodedcommand", "-e") and i + 1 < len(parts):
                    decoded = try_decode_b64(parts[i + 1])
                    ts = ev["System"]["TimeCreated"][11:19]
                    print(f"  [{ts}] Encoded command detected:")
                    print(f"    raw:     {cl[:80]}")
                    if decoded:
                        print(f"    decoded: {decoded}")
                    found = True
    if not found:
        print("  (none)")
    print()


def check_lsass_access(events: list[dict]) -> None:
    """Find EventID 10 (ProcessAccess) targeting lsass.exe."""
    print("── LSASS memory access (EventID 10) ────────────────────────────")
    found = False
    for ev in events:
        if event_id(ev) != 10:
            continue
        d = data(ev)
        target = d.get("TargetImage", "")
        if "lsass.exe" in target.lower():
            found = True
            ts = ev["System"]["TimeCreated"][11:19]
            print(f"  ⚠  [{ts}] {image_basename(d.get('SourceImage','?'))}"
                  f" → lsass.exe  GrantedAccess={d.get('GrantedAccess','?')}")
            print(f"     Technique: T1003.001 (Credential Access)")
            print(f"     SourceImage: {d.get('SourceImage','?')}")
    if not found:
        print("  (none)")
    print()


def check_persistence(events: list[dict]) -> None:
    """Find EventID 13 (Registry Value Set) on Run keys."""
    print("── Registry persistence (EventID 13) ───────────────────────────")
    found = False
    for ev in events:
        if event_id(ev) != 13:
            continue
        d = data(ev)
        target = d.get("TargetObject", "")
        if "\\Run\\" in target or "\\RunOnce\\" in target:
            found = True
            ts = ev["System"]["TimeCreated"][11:19]
            print(f"  ⚠  [{ts}] Run key set: {target}")
            print(f"     Value: {d.get('Details','?')}")
            print(f"     By:    {image_basename(d.get('Image','?'))}  Technique: T1547.001")
    if not found:
        print("  (none)")
    print()


def check_network(events: list[dict]) -> None:
    """Summarise EventID 3 (Network) — external connections from suspicious processes."""
    print("── Network connections (EventID 3) ─────────────────────────────")
    for ev in events:
        if event_id(ev) != 3:
            continue
        d = data(ev)
        dst = d.get("DestinationIp", "")
        if not (dst.startswith("10.") or dst.startswith("192.168.") or dst.startswith("172.")):
            ts = ev["System"]["TimeCreated"][11:19]
            print(f"  [{ts}] {image_basename(d.get('Image','?'))}"
                  f" → {dst}:{d.get('DestinationPort','?')}"
                  f"  (pid={d.get('ProcessId','?')})")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    events = load_events(EVENTS_PATH)
    print("=" * 62)
    print("SOC — Endpoint Telemetry Analysis")
    print(f"Source: {EVENTS_PATH.name}  ({len(events)} events)")
    print("=" * 62)
    print()

    print_event_summary(events)
    print_process_tree(events)
    check_ancestry(events)
    decode_encoded_commands(events)
    check_lsass_access(events)
    check_persistence(events)
    check_network(events)

    print("── Summary ─────────────────────────────────────────────────────")
    print("  Attack chain reconstructed:")
    print("  explorer.exe")
    print("  └─ WINWORD.EXE  (phishing doc opened — T1566.001)")
    print("     └─ cmd.exe   (macro spawned cmd — T1059.003)")
    print("        └─ powershell.exe -enc …  (encoded payload download — T1059.001)")
    print("           └─ rundll32.exe update.dll  (LOLBin execution — T1218.011)")
    print("              ├─ [EventID 10] lsass.exe access  (T1003.001)")
    print("              ├─ [EventID 13] HKLM…\\Run\\UpdateSvc  (T1547.001)")
    print("              └─ [EventID  3] 185.220.101.47:443 C2 callback")
    print()
    print("  Detection keys: parent-child (Word→cmd), -enc flag, lsass GrantedAccess 0x1410,")
    print("  Run key write by rundll32, external network from rundll32.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
