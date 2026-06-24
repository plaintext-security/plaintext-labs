#!/usr/bin/env python3
"""
Module 04 — Windows Artifacts demo parser.
Parses pre-shaped event JSONL and registry JSON to surface forensic findings.
In a real investigation: use chainsaw against real EVTX, python-registry against real hives.
"""
import json
import sys
import os

def parse_events(jsonl_path):
    print("=" * 60)
    print("WINDOWS SECURITY EVENT ANALYSIS")
    print("=" * 60)
    events = []
    with open(jsonl_path) as f:
        for line in f:
            events.append(json.loads(line.strip()))

    # Group by event ID
    by_id = {}
    for evt in events:
        eid = evt["Event"]["System"]["EventID"]
        by_id.setdefault(eid, []).append(evt)

    # 4624 — Logons
    if 4624 in by_id:
        print(f"\n[!] Event 4624 — Successful Logons ({len(by_id[4624])} events)")
        for evt in by_id[4624]:
            d = evt["Event"]["EventData"]
            t = evt["Event"]["System"]["TimeCreated"]["SystemTime"]
            print(f"    {t} | User: {d.get('TargetUserName')} | Type: {d.get('LogonType')} | From: {d.get('IpAddress')}")

    # 4625 — Failed logons
    if 4625 in by_id:
        print(f"\n[!] Event 4625 — FAILED Logons ({len(by_id[4625])} events)")
        for evt in by_id[4625]:
            d = evt["Event"]["EventData"]
            t = evt["Event"]["System"]["TimeCreated"]["SystemTime"]
            print(f"    {t} | Target: {d.get('TargetUserName')} | From: {d.get('IpAddress')} | Status: {d.get('Status')}")

    # 4688 — Process creation
    if 4688 in by_id:
        print(f"\n[!] Event 4688 — Process Creation ({len(by_id[4688])} events)")
        for evt in by_id[4688]:
            d = evt["Event"]["EventData"]
            t = evt["Event"]["System"]["TimeCreated"]["SystemTime"]
            proc = d.get('NewProcessName', '').split('\\')[-1]
            parent = d.get('ParentProcessName', '').split('\\')[-1]
            cmdline = d.get('CommandLine', '')[:80]
            print(f"    {t} | {parent} -> {proc}")
            print(f"             CMD: {cmdline}")

    # 1102 — Log cleared
    if 1102 in by_id:
        print(f"\n[!!!!] Event 1102 — SECURITY LOG CLEARED ({len(by_id[1102])} events)")
        for evt in by_id[1102]:
            d = evt["Event"]["EventData"]
            t = evt["Event"]["System"]["TimeCreated"]["SystemTime"]
            print(f"    {t} | Cleared by: {d.get('SubjectUserName')}@{d.get('SubjectDomainName')}")
            print(f"    This is a significant anti-forensics indicator (ATT&CK T1070.001)")

def parse_registry(json_path):
    print("\n" + "=" * 60)
    print("REGISTRY HIVE ANALYSIS (NTUSER.DAT)")
    print("=" * 60)
    with open(json_path) as f:
        data = json.load(f)

    for key_path, key_data in data["keys"].items():
        print(f"\n[KEY] {key_path}")
        print(f"      Last write: {key_data.get('last_write', 'unknown')}")
        for val_name, val_data in key_data.get("values", {}).items():
            val_str = str(val_data.get("data", ""))
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            flag = " <-- SUSPICIOUS" if "enc" in val_str.lower() or "hidden" in val_str.lower() else ""
            print(f"      {val_name} = {val_str}{flag}")

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    events_path = os.path.join(data_dir, "security-events.jsonl")
    registry_path = os.path.join(data_dir, "ntuser-parsed.json")

    print("\nWindows Artifact Analysis — beachhead workstation triage")
    print("Host: BEACHHEAD-WS01.corp.internal")
    print("Window: 2024-03-15 02:09–02:31 UTC\n")

    parse_events(events_path)
    parse_registry(registry_path)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("  - Lateral movement from 10.99.4.22 at 02:09 UTC")
    print("  - svc-backup used for access (logon type 3 = network)")
    print("  - cmd.exe -> powershell.exe execution chain with encoded payload")
    print("  - Encoded PS command in Run key = persistence (ATT&CK T1547.001)")
    print("  - Log cleared at 02:31 UTC — attacker covering tracks (T1070.001)")
    print("  - TypedPaths show navigation to \\FILESHARE-SRV01 and \\10.99.4.22\\drop$")
    print("\nNext: correlate these events in the super-timeline (Module 07)")

if __name__ == "__main__":
    main()
