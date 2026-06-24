#!/bin/sh
# demo.sh — runs hayabusa and chainsaw over EVTX data, then parses CloudTrail events.
set -e

echo "============================================================"
echo "  Log & Cloud Forensics Demo (anchor: Lunar Spider intrusion)"
echo "============================================================"
echo ""

EVTX_DIR=/data/evtx
CT_DIR=/data/cloudtrail

# --- Hayabusa over EVTX ---
echo "--- Part 1: Hayabusa EVTX Triage ---"
if command -v hayabusa >/dev/null 2>&1; then
    hayabusa csv-timeline --quiet --no-wizard \
        --directory "$EVTX_DIR" \
        2>/dev/null | head -40 || \
    echo "(Hayabusa output — install binary in container to see live results)"
else
    echo "Hayabusa not found — showing synthetic triage output from seed data:"
    cat /data/evtx_triage_summary.txt 2>/dev/null || true
fi
echo ""

# --- Chainsaw EVTX search ---
echo "--- Part 1b: Chainsaw account search (jsmith) ---"
if command -v chainsaw >/dev/null 2>&1; then
    chainsaw search --json -t "SubjectUserName: jsmith" "$EVTX_DIR" 2>/dev/null || true
else
    echo "Chainsaw not found — showing synthetic search output:"
    cat /data/chainsaw_summary.txt 2>/dev/null || true
fi
echo ""

# --- CloudTrail parsing ---
echo "--- Part 2: CloudTrail API Event Timeline ---"
python3 /scripts/parse_cloudtrail.py "$CT_DIR"
