#!/usr/bin/env python3
"""
create_ext2_img.py — creates a minimal ext2 disk image for the anti-forensics lab.

Builds a 2MB ext2 image with a timestomped file (sihosts.exe with mtime=2019)
and a deleted file (notes.txt). Runs inside the Docker container which has
mkfs.ext2 and debugfs available.

Usage: python3 create_ext2_img.py [output_path]
"""

import subprocess
import os
import sys
import tempfile

IMG = sys.argv[1] if len(sys.argv) > 1 else "/data/disk.img"


def run(cmd, check=True):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout[:500])
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[:300]}")
        if check:
            raise RuntimeError(f"Command failed: {cmd}")
    return result


print(f"Creating ext2 disk image: {IMG}")

# Create a 2MB zero-filled image
run(f"dd if=/dev/zero of={IMG} bs=1M count=2 status=none")
print(f"Created {IMG}")

# Format as ext2
run(f"mkfs.ext2 -F -L BEACHHEAD-WS01 -m 0 {IMG}")
print("Formatted as ext2")

# Populate using debugfs (no mount needed — works without root)
mktdir = tempfile.mkdtemp()

# Create file contents
files = {
    "readme.txt": ("202401150900", "Workstation configuration\n"),
    "config.ini": ("202402200830", "[network]\ndns=10.0.0.1\nproxy=none\n"),
    "app.log": ("202403101430", "2024-03-10 14:30:01 INFO Application started\n"),
    "sihosts.exe": ("201906150000", "\x7fELF\x02\x01" + "\x00" * 58),  # ELF magic
    "notes.txt": ("202403151422", "attacker_c2=workspacin.cloud\n"),
}

# Write temp files
for name, (ts, content) in files.items():
    path = os.path.join(mktdir, name)
    mode = "w" if isinstance(content, str) else "wb"
    with open(path, mode) as f:
        f.write(content if isinstance(content, str) else content.encode())

# Use debugfs to write files into the image
debugfs_cmds = []
for name, (ts, _) in files.items():
    src = os.path.join(mktdir, name)
    debugfs_cmds.append(f"write {src} {name}")
    # Set timestamps: format is YYYYMMDDHHMMSS
    ts_formatted = f"{ts[:8]}{ts[8:]}00"  # add seconds
    debugfs_cmds.append(f"set_inode_field {name} mtime {ts[:4]}-{ts[4:6]}-{ts[6:8]}T{ts[8:10]}:{ts[10:12]}:00")

# Write and remove notes.txt to simulate deletion
debugfs_cmds.append(f"rm notes.txt")

cmd_str = "\n".join(debugfs_cmds)
cmd_file = os.path.join(mktdir, "debugfs_cmds.txt")
with open(cmd_file, "w") as f:
    f.write(cmd_str + "\n")

result = subprocess.run(
    f"debugfs -w {IMG} < {cmd_file}",
    shell=True, capture_output=True, text=True
)
if result.returncode not in (0, 1):  # debugfs exits 1 on some warnings
    print(f"debugfs output: {result.stdout[:500]}")
    print(f"debugfs stderr: {result.stderr[:300]}")

# Clean up temp files
import shutil
shutil.rmtree(mktdir)

# Verify
print("\nFile listing (fls):")
result = subprocess.run(f"fls -r {IMG}", shell=True, capture_output=True, text=True)
print(result.stdout or "(empty — fls may need to be run inside container)")
print(f"\nImage size: {os.path.getsize(IMG):,} bytes ({os.path.getsize(IMG)/1024/1024:.1f} MB)")
print("Done.")
