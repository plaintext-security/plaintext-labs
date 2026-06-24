#!/usr/bin/env python3
"""
Module 06 — Memory Forensics demo analyzer.
Parses pre-processed Volatility3 output from data/memory-sample.json
and surfaces forensic findings.

To run against a real memory image:
    vol -f memory.img windows.pslist
    vol -f memory.img windows.pstree
    vol -f memory.img windows.cmdline
    vol -f memory.img windows.netscan
    vol -f memory.img windows.malfind
"""
import json
import base64
import os
import sys

def load_sample(path):
    with open(path) as f:
        return json.load(f)

def analyze_pslist(processes):
    print("\n" + "=" * 60)
    print("PROCESS LIST ANALYSIS (pslist / pstree)")
    print("=" * 60)

    # Build PID map
    pid_map = {p["PID"]: p for p in processes}

    suspicious = []
    for proc in processes:
        flags = []
        name = proc["ImageFileName"]
        ppid = proc.get("PPID", 0)
        parent = pid_map.get(ppid, {}).get("ImageFileName", "unknown")

        # Suspicious path
        if "ProgramData" in proc.get("Path", ""):
            flags.append("SUSPICIOUS PATH (ProgramData)")

        # Process name anomalies
        if name == "svcupd.exe":
            flags.append("NOT A REAL WINDOWS PROCESS")

        if name == "notepad.exe" and parent not in ("explorer.exe", "unknown"):
            flags.append(f"ODD PARENT: {parent}")

        if flags:
            suspicious.append((proc, flags))
            print(f"\n[!] PID {proc['PID']:5d} | {name:20s} | Parent: {parent} ({ppid})")
            for f in flags:
                print(f"    FLAG: {f}")
            if "note" in proc:
                print(f"    NOTE: {proc['note']}")

    if not suspicious:
        print("  No obvious anomalies in process list.")

    # Print parent-child chain for suspicious processes
    print("\n  Key parent-child chain:")
    print("  services.exe (636) → svcupd.exe (1640) → cmd.exe (2856) → powershell.exe (6893)")
    print("  [svchost.exe (1044)] → notepad.exe (3124)  [injection target]")

def analyze_cmdline(cmdlines):
    print("\n" + "=" * 60)
    print("COMMAND LINE ANALYSIS (cmdline)")
    print("=" * 60)
    for entry in cmdlines:
        args = entry.get("Args", "")
        if "-enc" in args.lower() or "-encodedcommand" in args.lower():
            print(f"\n[!] PID {entry['PID']} — {entry['Process']}")
            print(f"    CMD: {args[:100]}")
            # Try to extract and decode the base64 payload
            parts = args.split()
            for i, part in enumerate(parts):
                if part.lower() in ("-enc", "-encodedcommand") and i + 1 < len(parts):
                    b64 = parts[i + 1]
                    try:
                        decoded = base64.b64decode(b64 + "==").decode("utf-16-le", errors="replace")
                        print(f"    DECODED: {decoded[:120]}")
                        print(f"    ANALYSIS: PowerShell reverse shell connecting to C2")
                    except Exception:
                        print(f"    [could not decode — try: echo '{b64}' | base64 -d | iconv -f UTF-16LE]")

def analyze_netscan(connections):
    print("\n" + "=" * 60)
    print("NETWORK CONNECTIONS (netscan)")
    print("=" * 60)
    legit_network_procs = {"chrome.exe", "svchost.exe", "lsass.exe", "services.exe", "spoolsv.exe"}
    for conn in connections:
        proc = conn["Owner"]
        flag = " <-- SUSPICIOUS" if proc not in legit_network_procs else ""
        note = f" | NOTE: {conn['note']}" if "note" in conn else ""
        print(f"  PID {conn['PID']:5d} | {proc:20s} | {conn['LocalAddr']}:{conn['LocalPort']} -> {conn['ForeignAddr']}:{conn['ForeignPort']} [{conn['State']}]{flag}{note}")

def analyze_malfind(hits):
    print("\n" + "=" * 60)
    print("INJECTION ANALYSIS (malfind)")
    print("=" * 60)
    for hit in hits:
        print(f"\n[!] PID {hit['PID']} — {hit['Process']}")
        print(f"    Region: {hit['VadStart']} — {hit['VadEnd']}")
        print(f"    Protection: {hit['Protection']}")
        print(f"    First bytes: {hit['First16Bytes']}")
        print(f"    Header: {'MZ (PE)' if hit['First16Bytes'].startswith('4D 5A') else 'shellcode or other'}")
        if "note" in hit:
            print(f"    FINDING: {hit['note']}")
        print(f"    ATT&CK: T1055 — Process Injection")

def main():
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    sample_path = os.path.join(data_dir, "memory-sample.json")

    print("\nIR — Memory Forensics Analysis")
    print("Host: BEACHHEAD-WS01.corp.internal")
    print("Image captured: 2024-03-15T02:35:00Z\n")

    data = load_sample(sample_path)
    print(f"Source: {data['metadata']['source']}")
    print(f"OS: {data['metadata']['os']}")

    analyze_pslist(data["pslist"])
    analyze_cmdline(data["cmdline"])
    analyze_netscan(data["netscan"])
    analyze_malfind(data["malfind"])

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("  - svcupd.exe: fake Windows service, persistence binary (T1543.003)")
    print("  - cmd.exe -> powershell.exe: execution chain with encoded reverse shell (T1059.001)")
    print("  - Reverse shell connecting to 10.99.4.22:443 (C2)")
    print("  - notepad.exe injected with PE (MZ header) + outbound connection to 10.99.4.22:4444 (T1055)")
    print("  - All connections to 10.99.4.22 — single C2 IP across all techniques")
    print("\nNext: build super-timeline correlating these memory artifacts with disk/log evidence (Module 07)")

if __name__ == "__main__":
    main()
