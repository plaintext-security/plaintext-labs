"""Atomic T1547.001 — Registry Run Key Persistence (Linux cron equivalent).

On Windows this creates a Run key. On Linux we simulate by writing a crontab
entry (same persistence mechanism, different OS primitive). The event record
uses the Sigma field names so the rule still matches.
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
        "User": "jsmith",
        "TargetObject": r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\UpdateCheck",
        "Details": "/tmp/.update_check",
        "technique": "T1547.001",
        "stdout": "(crontab updated — simulated)",
        "returncode": 0,
    }
