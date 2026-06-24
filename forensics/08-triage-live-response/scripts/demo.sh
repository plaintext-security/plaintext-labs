#!/bin/sh
# demo.sh — runs three VQL artifact collections offline and prints structured results.
# Simulates what a Velociraptor hunt produces on a live endpoint.
# Runs entirely from seed data in /data — no server connection required for the demo.

set -e

echo "============================================================"
echo "  BEACHHEAD-WS01 — Live Response Demo"
echo "  Simulated VQL artifact collection"
echo "  (modeled on the DFIR Report 'Lunar Spider' intrusion)"
echo "============================================================"
echo ""

echo "--- Artifact: System.Process.List (pslist) ---"
cat /data/pslist.json | python3 -c "
import json, sys
rows = json.load(sys.stdin)
print(f'{'PID':<8} {'PPID':<8} {'Name':<28} {'CommandLine'}")
print('-'*80)
for r in rows:
    print(f\"{r.get('Pid',''):<8} {r.get('PPid',''):<8} {r.get('Name',''):<28} {r.get('CommandLine','')[:60]}\")
"
echo ""

echo "--- Artifact: System.Network.Netstat (connections) ---"
cat /data/netstat.json | python3 -c "
import json, sys
rows = json.load(sys.stdin)
print(f'{'PID':<8} {'Proto':<8} {'LocalAddr':<24} {'RemoteAddr':<24} {'State'}")
print('-'*80)
for r in rows:
    print(f\"{r.get('Pid',''):<8} {r.get('Type',''):<8} {r.get('Laddr',''):<24} {r.get('Raddr',''):<24} {r.get('Status','')}\")
"
echo ""

echo "--- Artifact: System.VFS.ListDirectory — recent writes under /tmp ---"
cat /data/recent_files.json | python3 -c "
import json, sys
rows = json.load(sys.stdin)
print(f'{'Modified':<22} {'Size':<10} {'Path'}")
print('-'*80)
for r in rows:
    print(f\"{r.get('Mtime',''):<22} {str(r.get('Size','')):<10} {r.get('FullPath','')}\")
"
echo ""

echo "============================================================"
echo "  FINDINGS SUMMARY"
echo "  - PID 3847 'sihosts.exe' has PPID=3201 (bash) — anomalous parent"
echo "  - PID 3847 has outbound TCP to 198.51.100.42:4444 (ESTABLISHED)"
echo "  - /tmp/.s (0 bytes, hidden name) written 90s ago"
echo "  Action: escalate BEACHHEAD-WS01 to full imaging queue."
echo "============================================================"
