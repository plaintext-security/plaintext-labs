#!/usr/bin/env python3
"""
Pivoting demo — network segmentation bypass.

Demonstrates:
  1. Network discovery — attacker maps reachable hosts and routes
  2. Direct connection attempt — attacker CANNOT reach internal-target
  3. Pivot setup — relay.py already running on the pivot host
  4. Tunnelled connection — attacker reaches internal-target via pivot
  5. Lateral movement — reading internal-only data through the tunnel
  6. Network diagram + defences

This script runs in the 'attacker' container (DMZ network only).
The pivot container is on both DMZ and internal; internal-target is internal only.

> Only pivot in networks you own or have explicit written authorisation to test.

Network topology:
  ┌─────────────────┐  DMZ (172.20.0.0/24)  ┌──────────────────────────────┐
  │  attacker        │◄─────────────────────►│  pivot (172.20.0.x)          │
  │  (this container)│                       │  ↕  (also on internal)       │
  └─────────────────┘                        │  (172.21.0.x)                │
                                             └──────────────────────────────┘
                                                        │  internal (172.21.0.0/24)
                                             ┌──────────▼───────────────────┐
                                             │  internal-target (172.21.0.x)│
                                             │  (NOT reachable from attacker)│
                                             └──────────────────────────────┘
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

DIVIDER = "─" * 64
PIVOT_HOST = "pivot"
PIVOT_PORT = 8888       # relay listening port on pivot
INTERNAL_HOST = "internal-target"
INTERNAL_PORT = 80


def try_connect(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_get(url: str, timeout: float = 5.0) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read(4096).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return 0, str(e)


def demo() -> int:
    print("=" * 64)
    print("Network Pivoting Demo")
    print("Technique: TCP relay through dual-homed pivot host")
    print("=" * 64)

    # ── Step 1: Network discovery ─────────────────────────────────────────
    print("\n[Step 1] Network discovery — attacker's position")
    print()
    r = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)
    dmz_ip = None
    for line in r.stdout.splitlines():
        if "inet " in line and "127." not in line:
            dmz_ip = line.strip().split()[1]
            print(f"  Attacker IP: {dmz_ip}")
    print()

    r = subprocess.run(["ip", "route"], capture_output=True, text=True)
    print("  Routes (attacker can only reach the DMZ subnet):")
    for line in r.stdout.splitlines():
        if line.strip():
            print(f"    {line}")

    # ── Step 2: Attempt to reach internal-target directly ─────────────────
    print(f"\n{DIVIDER}")
    print(f"[Step 2] Direct connection attempt to {INTERNAL_HOST}:{INTERNAL_PORT}")
    print()
    print(f"  Trying socket.connect('{INTERNAL_HOST}', {INTERNAL_PORT}) ...")
    reachable = try_connect(INTERNAL_HOST, INTERNAL_PORT, timeout=2.0)
    if reachable:
        print(f"  Connection succeeded (unexpected — check network config)")
    else:
        print(f"  Connection FAILED — internal-target is not reachable from the DMZ")
        print(f"  (This is the segmentation working correctly — attacker cannot reach internal)")

    # ── Step 3: Check the pivot host is reachable ─────────────────────────
    print(f"\n{DIVIDER}")
    print(f"[Step 3] Identify pivot host on DMZ")
    print()
    print(f"  Checking {PIVOT_HOST}:{PIVOT_PORT} (relay listening port) ...")
    pivot_ok = try_connect(PIVOT_HOST, PIVOT_PORT, timeout=3.0)
    if pivot_ok:
        print(f"  ✓ Pivot host reachable — relay is running on {PIVOT_HOST}:{PIVOT_PORT}")
    else:
        print(f"  ✗ Cannot reach pivot relay — is 'make up' running?")
        return 1

    # ── Step 4: Tunnel through pivot ─────────────────────────────────────
    print(f"\n{DIVIDER}")
    print(f"[Step 4] Tunnelled connection — reach internal-target via pivot")
    print()
    print(f"  Pivot relay is forwarding: {PIVOT_HOST}:{PIVOT_PORT} → {INTERNAL_HOST}:{INTERNAL_PORT}")
    print(f"  Sending HTTP GET to http://{PIVOT_HOST}:{PIVOT_PORT}/ ...")
    print()
    status, body = http_get(f"http://{PIVOT_HOST}:{PIVOT_PORT}/", timeout=5)
    if status == 200:
        print(f"  HTTP {status} — internal-target reached through pivot!")
        print()
        # Extract key lines from the response
        for line in body.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("<!") and not stripped.startswith("<html") and not stripped.startswith("<head"):
                print(f"    {stripped}")
        print()
        print("  ✓ Pivot confirmed — attacker read internal-only data through the relay")
    else:
        print(f"  HTTP {status}: {body[:200]}")
        return 1

    # ── Step 5: Explain the technique ─────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 5] Network diagram")
    print()
    print("  ┌─────────────┐   DMZ (172.20.x.x)    ┌──────────────────┐")
    print("  │  attacker   │◄──────────────────────►│  pivot           │")
    print("  │  (us)       │   port 8888 open       │  DMZ + internal  │")
    print("  └─────────────┘                        │  relay: 8888→80  │")
    print("                                         └────────┬─────────┘")
    print("                                          internal │(172.21.x.x)")
    print("                                         ┌─────────▼──────────┐")
    print("                                         │  internal-target   │")
    print("                                         │  NOT from DMZ      │")
    print("                                         └────────────────────┘")
    print()
    print("  Traffic path:")
    print("    attacker → pivot:8888 → [relay] → internal-target:80 → pivot:8888 → attacker")
    print()
    print("  Real-world tools that do this:")
    print("    chisel:    socks proxy (attacker acts as SOCKS server)")
    print("    ligolo-ng: full tun interface on attacker machine")
    print("    SSH -L:    ssh -L 8888:internal-target:80 user@pivot")
    print("    socat:     socat TCP-LISTEN:8888,fork TCP:internal-target:80")

    # ── Step 6: Defences ──────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 6] Defences — what stops each step")
    print()
    rows = [
        ("Network segmentation", "Prevents direct attacker→internal — already working here"),
        ("Firewall egress rules", "Block outbound on pivot to 172.21.x; no pivot port 8888"),
        ("Host IDS / EDR",        "Detects relay binary / unusual bind on pivot host"),
        ("Zeek/Suricata on pivot", "Detects unusual long-lived connections or byte patterns"),
        ("Beacon hunting (RITA)",  "The relay's keep-alive traffic matches beaconing profile"),
        ("Zero-trust / ZTNA",      "Every internal-target request requires identity, not just IP"),
    ]
    print(f"  {'Defence':<28}  Effect")
    print(f"  {'─'*28}  {'─'*36}")
    for d, e in rows:
        print(f"  {d:<28}  {e}")

    print(f"\n{'=' * 64}")
    print("Demo complete — pivot through DMZ host to internal network confirmed")
    print(f"{'=' * 64}\n")
    return 0


if __name__ == "__main__":
    sys.exit(demo())
