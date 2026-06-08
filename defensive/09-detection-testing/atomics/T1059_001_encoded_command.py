"""Atomic T1059.001 — PowerShell Encoded Command.

Simulates an attacker running a base64-encoded shell command to evade
command-line inspection. On Linux this uses bash with base64-decoded args
rather than PowerShell, but produces the same detection signal.
"""
import base64
import os
import subprocess
import time


def run():
    # Encode a benign payload: 'id; hostname' (attacker would use malware here)
    payload = "id; hostname"
    encoded = base64.b64encode(payload.encode()).decode()
    cmdline = f"bash -enc {encoded}"

    # Execute (container-safe, harmless output)
    result = subprocess.run(
        ["bash", "-c", f"echo {encoded} | base64 -d | bash"],
        capture_output=True, text=True, timeout=5
    )

    # Event record mirrors what Windows Sysmon EventID 1 would produce for this technique.
    # Image and CommandLine use Windows paths/syntax so the Sigma rule matches.
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "EventID": 1,
        "Image": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        "CommandLine": f"powershell.exe -enc {encoded}",
        "ParentImage": r"C:\Windows\System32\cmd.exe",
        "User": "MERIDIAN\\jsmith",
        "technique": "T1059.001",
        "stdout": result.stdout.strip(),
        "returncode": result.returncode,
    }
