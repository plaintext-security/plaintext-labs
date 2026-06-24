"""Atomic T1059.001 — PowerShell Encoded Command.

This is a synthetic *emulator* that mirrors a real Atomic Red Team test:
  Atomic Red Team T1059.001 — "Command and Scripting Interpreter: PowerShell"
  https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1059.001 (MIT)
The genuine ART tests run `powershell -EncodedCommand <base64>` on Windows. On Linux
we base64-decode through bash to stand in, but the event record below carries the
Windows-style fields (powershell.exe, `-enc <base64>`) so the Sigma rule matches
exactly as it would on a real Sysmon EventID 1. To validate against the real
technique, run the ART atomic on your own Windows lab host (see lab.md).
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
        "User": "CORP\\auser",
        "technique": "T1059.001",
        "stdout": result.stdout.strip(),
        "returncode": result.returncode,
    }
