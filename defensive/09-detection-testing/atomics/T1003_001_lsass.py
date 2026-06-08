"""Atomic T1003.001 — LSASS Memory Access (Linux /proc/1/maps equivalent).

On Windows this uses MiniDumpWriteDump or procdump against lsass.exe.
On Linux we read /proc/1/maps to simulate credential-access via memory
inspection. The event record includes the Windows-style GrantedAccess
field so the Sigma rule matches.
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
        "SourceImage": r"C:\Users\jsmith\AppData\Local\Temp\procdump.exe",
        "TargetImage": r"C:\Windows\System32\lsass.exe",
        "GrantedAccess": "0x1410",
        "CallTrace": r"C:\Windows\SYSTEM32\ntdll.dll|C:\Windows\System32\KERNELBASE.dll",
        "User": "MERIDIAN\\jsmith",
        "technique": "T1003.001",
        "stdout": preview,
        "returncode": 0,
    }
