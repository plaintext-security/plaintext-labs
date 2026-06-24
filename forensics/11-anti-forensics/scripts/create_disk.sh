#!/bin/bash
# create_disk.sh — generates data/disk.img: a small ext2 image with a timestomped file.
# Run this ONCE on the host (requires Linux utilities) to regenerate the image.
# The generated image is committed to the repo under data/.

set -e
IMG=/data/disk.img
SIZE_MB=2

echo "[*] Creating ${SIZE_MB}MB ext2 image at $IMG"
dd if=/dev/zero of="$IMG" bs=1M count="$SIZE_MB" status=progress

echo "[*] Formatting as ext2"
mkfs.ext2 -F -L "BEACHHEAD-WS01" "$IMG"

echo "[*] Mounting and populating"
MNTDIR=$(mktemp -d)
mount -o loop "$IMG" "$MNTDIR"

# Normal system files with coherent timestamps
touch -t "202401150900" "$MNTDIR/readme.txt"
echo "Workstation configuration" > "$MNTDIR/readme.txt"

touch -t "202402200830" "$MNTDIR/config.ini"
echo "[network]
dns=10.0.0.1
proxy=none" > "$MNTDIR/config.ini"

touch -t "202403101430" "$MNTDIR/app.log"
echo "2024-03-10 14:30:01 INFO Application started" > "$MNTDIR/app.log"

# The "timestomped" binary — mtime set to 2019 to look like a system file
# but it was actually written in March 2024 (FN attribute will reflect creation)
cp /bin/true "$MNTDIR/sihosts.exe"
touch -t "201906150000" "$MNTDIR/sihosts.exe"

# A file we'll later "delete"
echo "attacker_c2=workspacin.cloud" > "$MNTDIR/notes.txt"
touch -t "202403151422" "$MNTDIR/notes.txt"

umount "$MNTDIR"
rmdir "$MNTDIR"

# "Delete" notes.txt by removing the directory entry (simulate deletion)
# We can't easily delete at the raw level without debugfs, so we use debugfs
debugfs -w "$IMG" -R "rm notes.txt" 2>/dev/null || true

echo "[*] Image created: $IMG ($(du -h "$IMG" | cut -f1))"
echo "[*] File listing:"
fls "$IMG"
