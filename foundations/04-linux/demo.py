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

    # Group membership isn't the whole story — /etc/sudoers (and sudoers.d) can
    # grant rights directly, including NOPASSWD. That's where jsmith's broad
    # privilege lives, and it's the account the auth log ties the compromise to.
    sudoers_files = [Path("/etc/sudoers")] + sorted(Path("/etc/sudoers.d").glob("*")) \
        if Path("/etc/sudoers.d").is_dir() else [Path("/etc/sudoers")]
    grants = []
    for f in sudoers_files:
        try:
            for l in f.read_text().splitlines():
                s = l.strip()
                if not s or s.startswith("#") or s.startswith("Defaults"):
                    continue
                if "ALL" in s and not s.startswith("%"):
                    flag = "  ← NOPASSWD (no password needed for root!)" if "NOPASSWD" in s else ""
                    grants.append(f"    {s}{flag}")
        except (FileNotFoundError, PermissionError):
            pass
    print("\n  sudoers grants (direct, not via group):")
    print("\n".join(grants) if grants else "    (none)")
    print()
    print("  Command: grep ':0:' /etc/passwd")
    print("  Command: getent group sudo wheel")
    print("  Command: sudo grep -rvE '^#|^$|^Defaults' /etc/sudoers /etc/sudoers.d/")


def demo_suid() -> None:
    section("SUID binaries — 'find / -perm -4000 -type f 2>/dev/null'")
    print()
    # Search the WHOLE filesystem (the lab text's `find / -perm -4000`), not just
    # the system bin dirs — a planted backdoor hides outside them (e.g. /usr/local).
    out = run("find / -perm -4000 -type f 2>/dev/null | sort")
    STOCK_DIRS = ("/usr/bin/", "/bin/", "/usr/sbin/", "/sbin/")
    unexpected = []
    if out:
        for line in out.splitlines():
            stat_out = run(f"stat -c '%U %n' {line} 2>/dev/null")
            owner = stat_out.split()[0] if stat_out else "?"
            odd = owner == "root" and not line.startswith(STOCK_DIRS)
            if odd:
                unexpected.append(line)
                flag = "  ← ⚠ UNEXPECTED: root-owned SUID outside system dirs (check GTFOBins!)"
            elif owner == "root":
                flag = "  ← root-owned SUID (stock)"
            else:
                flag = ""
            print(f"  {line}{flag}")
    else:
        print("  (find returned nothing — unexpected; even a minimal box ships SUID binaries)")
    print()
    print("  SUID means the binary runs as its *owner*, not the caller.")
    print("  The stock ones (su, mount, passwd, sudo…) are expected. The one that")
    print("  is NOT — a root-owned SUID bash in /usr/local/bin — is the attacker's")
    print("  persistence: `bash -p` returns a root shell (GTFOBins). That binary is")
    print("  the SUID half of the story the auth log tells: jsmith was brute-forced,")
    print("  its NOPASSWD root was used to drop a SUID-root shell.")
    if unexpected:
        print(f"\n  Backdoor found: {', '.join(unexpected)}")


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

    # Primary data: the REAL public loghub OpenSSH log (run `make fetch-data`).
    # Falls back to the bundled excerpt if the fetch hasn't been run yet.
    real_log = DATA_DIR / "OpenSSH_2k.log"
    if real_log.exists():
        log_path = real_log
        source_note = "REAL loghub OpenSSH dataset (data/OpenSSH_2k.log)"
    else:
        log_path = DATA_DIR / "auth_sample.log"
        source_note = "bundled excerpt — run `make fetch-data` for the real log"
    if not log_path.exists():
        print("  No log found. Run `make fetch-data` first.")
        return

    text = log_path.read_text()
    # The real loghub log is pure brute-force noise (no successful login). To keep
    # the "compromise = success from a brute-forcing IP" lesson alive, append a
    # small, clearly-labeled overlay if present (data/compromise_overlay.log) — one
    # Accepted line from an IP that ALSO appears as a brute-forcer in the real log.
    overlay = DATA_DIR / "compromise_overlay.log"
    if log_path is real_log and overlay.exists():
        text = text + "\n" + overlay.read_text()
    lines = text.splitlines()
    total = len(lines)

    failed_pattern = re.compile(r"Failed password for (?:invalid user )?\S+ from (\S+) port")
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

    print(f"  Source: {source_note}")
    print(f"  Log: {log_path.name}  ({total} lines)")
    print()
    print("  Top failed-login source IPs (top 10):")
    top = failed_ips.most_common(10)
    busiest = top[0][1] if top else 1
    for ip, count in top:
        bar = "█" * max(1, round(40 * count / busiest))  # scaled, capped at 40 cols
        print(f"    {ip:20s}  {count:5d}  {bar}")

    print()
    print("  Successful logins:")
    if successes:
        for user, src, method in successes:
            internal = "✓ internal" if src.startswith("10.") else "⚠ EXTERNAL"
            also_bruteforcing = "  ← ALSO a brute-force source" if src in failed_ips else ""
            print(f"    user={user:12s}  src={src:20s}  method={method}  {internal}{also_bruteforcing}")
    else:
        print("    (none in this log — pure brute-force noise)")

    print()
    print("  Pipeline to replicate:")
    print(f"  grep 'Failed password' data/{log_path.name} \\")
    print("    | grep -oE 'from [0-9.]+ port' | awk '{print $2}' \\")
    print("    | sort | uniq -c | sort -rn | head")

    # Check for success from a failed-IP (credential stuffing indicator)
    stuffing = [(u, s) for u, s, _ in successes if s in failed_ips]
    if stuffing:
        print()
        print("  ⚠ Possible credential stuffing — success after failures:")
        for user, src in stuffing:
            print(f"    user={user}  src={src}  ({failed_ips[src]} prior failures)")


def main() -> None:
    print("=" * 64)
    print("Linux Triage Demo — bastion host post-alert")
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
