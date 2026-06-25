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
print('%-8s %-8s %-28s %s' % ('PID', 'PPID', 'Name', 'CommandLine'))
print('-'*80)
for r in rows:
    print('%-8s %-8s %-28s %s' % (r.get('Pid',''), r.get('PPid',''), r.get('Name',''), str(r.get('CommandLine',''))[:60]))
"
echo ""

echo "--- Artifact: System.Network.Netstat (connections) ---"
cat /data/netstat.json | python3 -c "
import json, sys
rows = json.load(sys.stdin)
print('%-8s %-8s %-24s %-24s %s' % ('PID', 'Proto', 'LocalAddr', 'RemoteAddr', 'State'))
print('-'*80)
for r in rows:
    print('%-8s %-8s %-24s %-24s %s' % (r.get('Pid',''), r.get('Type',''), r.get('Laddr',''), r.get('Raddr',''), r.get('Status','')))
"
echo ""

echo "--- Artifact: System.VFS.ListDirectory — recent writes under /tmp ---"
cat /data/recent_files.json | python3 -c "
import json, sys
rows = json.load(sys.stdin)
print('%-22s %-10s %s' % ('Modified', 'Size', 'Path'))
print('-'*80)
for r in rows:
    print('%-22s %-10s %s' % (r.get('Mtime',''), str(r.get('Size','')), r.get('FullPath','')))
"
echo ""

echo "============================================================"
echo "  FINDINGS SUMMARY"
echo "  - PID 3847 'sihosts.exe' has PPID=3201 (bash) — anomalous parent"
echo "  - PID 3847 has outbound TCP to 198.51.100.42:4444 (ESTABLISHED)"
echo "  - /tmp/.s (0 bytes, hidden name) written 90s ago"
echo "  Action: escalate BEACHHEAD-WS01 to full imaging queue."
echo "============================================================"
