#!/bin/sh
# demo.sh — runs Zeek over capture.pcap and prints highlights from each log.
set -e

PCAP=/data/capture.pcap

echo "============================================================"
echo "  Network Forensics Demo"
echo "  Running Zeek over: $PCAP"
echo "  (real Redline Stealer capture if fetched; synthetic fallback otherwise)"
echo "============================================================"
echo ""

cd /tmp && mkdir -p zeek-out && cd zeek-out

zeek -r "$PCAP" LogAscii::use_json=T 2>/dev/null || zeek -r "$PCAP" 2>/dev/null

echo "--- conn.log (all connections) ---"
if [ -f conn.log ]; then
    echo "ts | proto | src | dst | duration | orig_bytes | resp_bytes"
    echo "--------------------------------------------------------------"
    python3 -c "
import json, sys
with open('conn.log') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            r = json.loads(line)
            print(f\"{r.get('ts',''):.0f} | {r.get('proto','')} | {r.get('id.orig_h',''):<16} | {r.get('id.resp_h',''):<16} | {r.get('duration','N/A')} | {r.get('orig_bytes','N/A')} | {r.get('resp_bytes','N/A')}\")
        except Exception:
            pass
" 2>/dev/null || cat conn.log | grep -v "^#" | awk '{print $1" "$6" "$3" "$5" "$9" "$10" "$11}' | head -20
fi
echo ""

echo "--- dns.log (DNS queries and responses) ---"
if [ -f dns.log ]; then
    echo "src | query | answers"
    echo "--------------------------------------------------------------"
    python3 -c "
import json, sys
with open('dns.log') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            r = json.loads(line)
            answers = ', '.join(r.get('answers', [])) if isinstance(r.get('answers'), list) else r.get('answers','')
            print(f\"{r.get('id.orig_h',''):<16} | {r.get('query',''):<30} | {answers}\")
        except Exception:
            pass
" 2>/dev/null || cat dns.log | grep -v "^#" | awk '{print $3" "$10" "$23}' | head -20
fi
echo ""

echo "--- http.log (HTTP transactions) ---"
if [ -f http.log ]; then
    echo "src | dst | method | uri | mime_type | status"
    echo "--------------------------------------------------------------"
    python3 -c "
import json, sys
with open('http.log') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            r = json.loads(line)
            print(f\"{r.get('id.orig_h',''):<16} | {r.get('id.resp_h',''):<16} | {r.get('method',''):<6} | {r.get('uri',''):<20} | {r.get('resp_mime_types',''):<30} | {r.get('status_code','')}\")
        except Exception:
            pass
" 2>/dev/null || cat http.log | grep -v "^#" | head -10
fi
echo ""

echo "============================================================"
echo "  WHAT TO LOOK FOR:"
echo "  - REAL PCAP (Redline Stealer, 2024-10-23): correlate dns.log /"
echo "    conn.log / http.log against the published IOCs file. Identify the"
echo "    C2 host(s), the stealer's HTTP/POST exfil, and any transferred file"
echo "    hash. Submit hashes to VirusTotal; do not replay the traffic."
echo "  - SYNTHETIC fallback: DNS for workspacin.cloud -> 198.51.100.42, then"
echo "    HTTP GET /update.bin returning application/octet-stream."
echo "  Action: flag the C2 session for file extraction and hash check."
echo "============================================================"
