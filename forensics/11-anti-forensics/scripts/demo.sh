#!/bin/sh
# demo.sh — demonstrates anti-forensics detection on the lab disk image.
set -e

IMG=/data/disk.img

echo "============================================================"
echo "  Anti-Forensics Detection Demo (anchor: Lunar Spider)"
echo "  Image: $IMG"
echo "============================================================"
echo ""

if [ ! -f "$IMG" ]; then
    echo "ERROR: disk.img not found at $IMG"
    echo "Run 'make create-image' first (requires Linux host with root)."
    exit 1
fi

echo "--- File System Info (fsstat) ---"
fsstat "$IMG" 2>&1 | head -20
echo ""

echo "--- File Listing (fls -r) ---"
fls -r "$IMG" 2>&1
echo ""

echo "--- Deleted files (fls -d flag) ---"
fls -r -d "$IMG" 2>&1 || echo "(no deleted file entries found via fls -d)"
echo ""

echo "--- All entries including deleted (fls -ra) ---"
fls -r -a "$IMG" 2>&1
echo ""

echo "--- Inode detail for sihosts.exe ---"
# Find the inode for sihosts.exe (renamed rclone, per the Lunar Spider exfil chain)
INODE=$(fls -r "$IMG" 2>/dev/null | grep -i "sihosts" | grep -oE '[0-9]+:' | head -1 | tr -d ':')
if [ -n "$INODE" ]; then
    echo "Inode: $INODE"
    istat "$IMG" "$INODE" 2>&1
else
    echo "(sihosts.exe not found in listing — check fls output above)"
fi
echo ""

echo "--- Running Python timestamp detection script ---"
python3 /scripts/detect_timestomping.py "$IMG"
echo ""

echo "============================================================"
echo "  KEY FINDINGS:"
echo "  - sihosts.exe: mtime set to 2019 via touch"
echo "  - All other files have 2024 timestamps consistent with"
echo "    workstation deployment date"
echo "  - notes.txt deleted from directory — may be recoverable"
echo "    via icat on unallocated inode"
echo "  Action: Document timestamp discrepancy; attempt icat recovery."
echo ""
echo "  Real artifact: the timestomp EVTX sample fetched by"
echo "  'make fetch-data' (Sysmon EID 2, file-creation-time modified)"
echo "  shows the same technique (T1070.006) in a real Windows log."
echo "============================================================"
