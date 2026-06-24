"""Atomic T1547.001 — Registry Run Key Persistence (Linux cron equivalent).

This is a synthetic *emulator* that mirrors a real Atomic Red Team test:
  Atomic Red Team T1547.001 — "Boot or Logon Autostart Execution: Registry Run Keys"
  https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1547.001 (MIT)
The genuine ART tests write a CurrentVersion\\Run value on Windows. On Linux we
stand in with a crontab entry (same persistence intent, different OS primitive), but
the event record below carries the Windows-style Run-key fields (TargetObject,
Details) so the Sigma rule matches. To validate against the real technique, run the
ART atomic on your own Windows lab host (see lab.md).
"""
import subprocess
import time


def run():
    # Add a crontab entry (benign: just echo a message)
    cron_entry = "@reboot /tmp/.update_check >/dev/null 2>&1"

    # Simulate the event without actually creating persistence in the container
    # (the event record is what matters for detection testing)
    cmdline = f"crontab -l | (cat; echo '{cron_entry}') | crontab -"

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "EventID": 1,
        "Image": "/usr/bin/crontab",
        "CommandLine": cmdline,
        "ParentImage": "/bin/bash",
        "User": "auser",
        "TargetObject": r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\UpdateCheck",
        "Details": "/tmp/.update_check",
        "technique": "T1547.001",
        "stdout": "(crontab updated — simulated)",
        "returncode": 0,
    }
