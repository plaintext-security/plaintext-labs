#!/usr/bin/env python3
"""
Linux Triage Lab — interactive demo.

Shows what the triage commands should find, using:
  - /etc/passwd, /etc/group, /etc/sudoers from the container
  - A bundled auth log (data/auth_sample.log) for the log analysis step
  - subprocess to show live ps and find output

This is the "expected output" reference. The learner's job is to
derive and run each command themselves inside this container.
"""
from __future__ import annotations

import collections
import re
import subprocess
import sys
from pathlib import Path

DATA_DIR = Path("/lab/data") if Path("/lab/data").exists() else Path("data")
DIVIDER = "─" * 64


def run(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (r.stdout + r.stderr).strip()


def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"[Step] {title}")
    print(DIVIDER)


def demo_users() -> None:
    section("Who can become root? (/etc/passwd + /etc/group)")
    print()

    # UID 0 accounts
    uid0 = [l for l in Path("/etc/passwd").read_text().splitlines()
            if l.split(":")[2] == "0" and not l.startswith("#")]
    print("  UID-0 accounts (can become root directly):")
    for line in uid0:
        parts = line.split(":")
        print(f"    {parts[0]:15s}  shell={parts[6]}")

    # sudo group members
    group_text = Path("/etc/group").read_text()
    sudo_line = next((l for l in group_text.splitlines()
                      if l.startswith("sudo:") or l.startswith("wheel:")), "")
    members = sudo_line.split(":")[-1].strip()
    print(f"\n  sudo/wheel group members: {members or '(none in container)'}")
    print()
    print("  Command: grep ':0:' /etc/passwd")
    print("  Command: getent group sudo wheel")


def demo_suid() -> None:
    section("SUID binaries — 'find / -perm -4000 -type f 2>/dev/null'")
    print()
    out = run("find /usr/bin /usr/sbin /bin /sbin -perm -4000 -type f 2>/dev/null | sort")
    if out:
        for line in out.splitlines():
            stat_out = run(f"stat -c '%U %n' {line} 2>/dev/null")
            owner = stat_out.split()[0] if stat_out else "?"
            flag = "  ← root-owned SUID" if owner == "root" else ""
            print(f"  {line}{flag}")
    else:
        print("  (no SUID binaries found — normal in this minimal container)")
    print()
    print("  SUID means the binary runs as its *owner*, not the caller.")
    print("  A root-owned SUID binary can be abused for privilege escalation")
    print("  if it has a GTFOBin entry (see: gtfobins.github.io).")


def demo_processes() -> None:
    section("Running processes — 'ps aux | sort -k3 -rn | head'")
    print()
    out = run("ps aux --sort=-%cpu 2>/dev/null || ps aux 2>/dev/null | head -15")
    if out:
        lines = out.splitlines()[:12]
        for l in lines:
            print(f"  {l}")
    else:
        print("  (ps not available in this container — install procps)")
    print()
    print("  Columns: USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND")
    print("  Sort by %CPU: ps aux | sort -k3 -rn | head -15")
    print("  Sort by %MEM: ps aux | sort -k4 -rn | head -15")


def demo_log_analysis() -> None:
    section("Auth log analysis — failed login ranked by source IP")
    print()

    log_path = DATA_DIR / "auth_sample.log"
    if not log_path.exists():
        print(f"  Log file not found: {log_path}")
        return

    text = log_path.read_text()
    lines = text.splitlines()
    total = len(lines)

    failed_pattern = re.compile(r"Failed password for \S+ from (\S+) port")
    success_pattern = re.compile(r"Accepted (\w+) for (\S+) from (\S+) port")

    failed_ips: collections.Counter = collections.Counter()
    successes = []

    for line in lines:
        m = failed_pattern.search(line)
        if m:
            failed_ips[m.group(1)] += 1
        m = success_pattern.search(line)
        if m:
            successes.append((m.group(2), m.group(3), m.group(1)))

    print(f"  Log: {log_path}  ({total} lines)")
    print()
    print("  Top failed-login source IPs:")
    for ip, count in failed_ips.most_common():
        bar = "█" * count
        print(f"    {ip:20s}  {count:3d}  {bar}")

    print()
    print("  Successful logins:")
    for user, src, method in successes:
        internal = "✓" if src.startswith("10.") else "⚠ EXTERNAL"
        print(f"    user={user:12s}  src={src:20s}  method={method}  {internal}")

    print()
    print("  Pipeline to replicate:")
    print("  grep 'Failed password' data/auth_sample.log \\")
    print("    | awk '{print $11}' | sort | uniq -c | sort -rn")

    # Check for success from a failed-IP (credential stuffing indicator)
    stuffing = [(u, s) for u, s, _ in successes if s in failed_ips]
    if stuffing:
        print()
        print("  ⚠ Possible credential stuffing — success after failures:")
        for user, src in stuffing:
            print(f"    user={user}  src={src}  ({failed_ips[src]} prior failures)")


def main() -> None:
    print("=" * 64)
    print("Meridian Financial — Linux Triage Demo")
    print("=" * 64)
    print()
    print("This demo shows the expected output for each triage step.")
    print("Run each command yourself to verify you get the same result.")

    demo_users()
    demo_suid()
    demo_processes()
    demo_log_analysis()

    print(f"\n{'=' * 64}")
    print("Now it's your turn — run each command inside this container.")
    print("Deliverable: linux-triage.md with privileged accounts,")
    print("  SUID list, and top failed-login IPs.")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
