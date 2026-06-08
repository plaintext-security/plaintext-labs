#!/usr/bin/env python3
"""
Networking Lab — live capture + annotated analysis.

Performs the capture-and-parse workflow the learner should replicate:
  1. Generates one DNS lookup + one HTTP request to the server
  2. Reads the bundled annotated capture to explain what was seen
  3. Shows the tcpdump and Wireshark commands to use interactively

Usage: python3 demo.py   (run inside the lab container)
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

DATA_DIR = Path("/lab/data") if Path("/lab/data").exists() else Path("data")
DIVIDER = "─" * 64
SERVER = "server"


def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"[Step] {title}")
    print(DIVIDER)


def run(cmd: str, timeout: int = 10) -> tuple[int, str]:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def demo_dns() -> None:
    section("DNS lookup — 'dig server A'")
    print()

    if shutil.which("dig"):
        rc, out = run(f"dig +short {SERVER} A 2>&1 || host {SERVER}")
        if rc == 0 and out:
            print(f"  $ dig +short {SERVER} A")
            print(f"  {out}")
        else:
            print(f"  (dig returned: {out[:100]})")
    elif shutil.which("getent"):
        rc, out = run(f"getent hosts {SERVER}")
        print(f"  $ getent hosts {SERVER}")
        print(f"  {out or '(not found)'}")
    else:
        print(f"  DNS tools not available — try inside the lab container")

    print()
    print("  In a real capture, dig produces:")
    print("    Packet 1: UDP query  → DNS server port 53   (A? server)")
    print("    Packet 2: UDP reply  ← DNS server           (A 172.20.0.x)")


def demo_http() -> None:
    section("HTTP request — 'curl -v http://server/'")
    print()

    if shutil.which("curl"):
        rc, out = run(f"curl -v http://{SERVER}/ 2>&1", timeout=10)
        lines = out.splitlines()
        # Show headers only
        for line in lines:
            if line.startswith(">") or line.startswith("<") or line.startswith("*"):
                print(f"  {line}")
        if rc == 0:
            print(f"\n  ✓ HTTP 200 received from {SERVER}")
        else:
            print(f"\n  (server not available — run 'make up' first)")
    else:
        print("  curl not available — run inside the lab container")


def demo_annotated_capture() -> None:
    section("Annotated capture walk-through")
    print()
    cap = DATA_DIR / "capture_annotated.txt"
    if cap.exists():
        for line in cap.read_text().splitlines():
            print(f"  {line}")
    else:
        print(f"  (Annotated capture not found at {cap})")


def demo_commands() -> None:
    section("Commands to run yourself inside the container")
    print()
    print("""
  # 1. Start a capture on all interfaces, writing to a file
  tcpdump -i any -w /tmp/cap.pcap &
  BGPID=$!

  # 2. Generate DNS + HTTP traffic
  dig +short server A
  curl -s http://server/ > /dev/null

  # 3. Stop the capture
  sleep 1 && kill $BGPID

  # 4. Read it back — DNS only
  tcpdump -r /tmp/cap.pcap 'udp port 53'

  # 5. TCP handshake — SYN, SYN-ACK, ACK
  tcpdump -r /tmp/cap.pcap 'tcp[tcpflags] & (tcp-syn|tcp-ack) != 0'

  # 6. Open in Wireshark (on your host after copying out)
  docker cp <container_id>:/tmp/cap.pcap ./cap.pcap
  wireshark cap.pcap   # Filter: 'tcp.flags.syn==1' or 'http'

  NOTE: cap.pcap should NOT be committed — it's in .gitignore.
  Document findings in networking.md instead.
""")


def main() -> None:
    print("=" * 64)
    print("Meridian Financial — Networking Lab Demo")
    print("=" * 64)
    print()
    print("Goal: capture a DNS query + TCP handshake and read each packet.")

    demo_dns()
    demo_http()
    demo_annotated_capture()
    demo_commands()

    print(f"{'=' * 64}")
    print("Deliverable: networking.md with the resolved IP, annotated")
    print("handshake, and packet count before any data flowed.")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
