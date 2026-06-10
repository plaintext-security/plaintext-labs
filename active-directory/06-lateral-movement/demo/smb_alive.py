#!/usr/bin/env python3
"""Fallback SMB liveness check (used when nxc is unavailable in the lab image)."""
import subprocess

hosts = ["10.10.0.10", "10.10.0.101", "10.10.0.102"]
for h in hosts:
    r = subprocess.run(
        ["smbclient", "-L", h, "-N", "-g"],
        capture_output=True,
        text=True,
    )
    print(f"{h}: alive={r.returncode == 0}")
