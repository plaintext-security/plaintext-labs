"""Atomic T1003.001 — LSASS Memory Access (Linux /proc/1/maps equivalent).

This is a synthetic *emulator* that mirrors a real Atomic Red Team test:
  Atomic Red Team T1003.001 — "OS Credential Dumping: LSASS Memory"
  https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1003.001 (MIT)
On Windows the genuine ART tests use procdump / comsvcs MiniDump against lsass.exe.
On Linux we read /proc/1/maps to stand in for credential-access via memory
inspection, but the event record below carries the Windows-style fields
(EventID 10, TargetImage=lsass.exe, GrantedAccess 0x1410) so the Sigma rule matches
exactly as it would on a real Sysmon ProcessAccess event. To validate against the
real technique, run the ART atomic on your own Windows lab host (see lab.md).
"""
import subprocess
import time


def run():
    # Read process maps (benign, visible in /proc)
    try:
        result = subprocess.run(
            ["cat", "/proc/1/maps"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()
        preview = lines[0] if lines else "(empty)"
    except Exception:
        preview = "(no access)"

    # Event record mirrors Sysmon EventID 10 (ProcessAccess) for a real LSASS dump.
    # GrantedAccess 0x1410 = PROCESS_VM_READ | PROCESS_QUERY_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "EventID": 10,
        "SourceImage": r"C:\Users\auser\AppData\Local\Temp\procdump.exe",
        "TargetImage": r"C:\Windows\System32\lsass.exe",
        "GrantedAccess": "0x1410",
        "CallTrace": r"C:\Windows\SYSTEM32\ntdll.dll|C:\Windows\System32\KERNELBASE.dll",
        "User": "CORP\\auser",
        "technique": "T1003.001",
        "stdout": preview,
        "returncode": 0,
    }
