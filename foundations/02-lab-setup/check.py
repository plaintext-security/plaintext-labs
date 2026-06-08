#!/usr/bin/env python3
"""
Lab Setup — environment validator and setup guide.

Checks that Docker is available and runs a throwaway container cleanly,
then prints the isolation-and-snapshot guide for building a safe lab.

Usage:
    python3 check.py        # full check + print guide
    python3 check.py --guide  # print guide only (skip Docker check)
"""
from __future__ import annotations

import shutil
import subprocess
import sys

DIVIDER = "─" * 64


def check_docker() -> bool:
    if not shutil.which("docker"):
        print("  ✗  docker not found — install Docker Desktop or Docker Engine")
        return False

    try:
        r = subprocess.run(
            ["docker", "run", "--rm", "hello-world"],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode == 0 and "Hello from Docker" in r.stdout:
            print("  ✓  docker: running — hello-world container passed")
            return True
        print(f"  ✗  docker: hello-world failed (exit {r.returncode})")
        if r.stderr:
            print(f"     {r.stderr.strip()[:200]}")
        return False
    except subprocess.TimeoutExpired:
        print("  ✗  docker: timed out pulling hello-world")
        return False
    except Exception as e:
        print(f"  ✗  docker: {e}")
        return False


def check_git() -> bool:
    if shutil.which("git"):
        r = subprocess.run(["git", "--version"], capture_output=True, text=True)
        print(f"  ✓  git: {r.stdout.strip()}")
        return True
    print("  ✗  git not found")
    return False


def print_guide() -> None:
    print("""
══════════════════════════════════════════════════════════════
Lab 02 — Stand Up a Disposable Lab: Setup Guide
══════════════════════════════════════════════════════════════

GOAL: One isolated Linux VM (snapshot + revert) + Docker confirmed.
      Every later lab runs here.

──────────────────────────────────────────────────────────────
STEP 1 — Create a Linux VM (Ubuntu 22.04 LTS recommended)
──────────────────────────────────────────────────────────────
Hypervisors (free):
  • VirtualBox (Windows/macOS/Linux): https://www.virtualbox.org/
  • UTM (Apple Silicon macOS): https://mac.getutm.app/
  • Hyper-V (Windows 10/11 Pro, built-in)

Recommended settings:
  RAM:   2 GB minimum (4 GB for later labs)
  Disk:  25 GB (dynamically allocated)
  CPU:   2 cores

──────────────────────────────────────────────────────────────
STEP 2 — Isolate the VM network (CRITICAL)
──────────────────────────────────────────────────────────────
Network mode options (choose one):

  HOST-ONLY (most isolated)
    VM ↔ host only. VM cannot reach the internet or your LAN.
    Use for: malware analysis, privilege escalation labs.
    VirtualBox: Settings → Network → Adapter 1 → Host-only.

  NAT (practical default)
    VM reaches the internet via host NAT. LAN devices cannot
    reach the VM. The VM cannot see your LAN.
    Use for: most labs that need package downloads.
    VirtualBox: Settings → Network → Adapter 1 → NAT.

  BRIDGED (avoid for offensive labs)
    VM gets a real LAN IP. Other devices on your network can
    reach it. Only use if you understand the risk.

Verify isolation (run inside VM):
  $ ping 192.168.1.1    # your home router — should fail on host-only
  $ curl -s https://ifconfig.me  # your public IP if NAT works

──────────────────────────────────────────────────────────────
STEP 3 — Take a clean snapshot
──────────────────────────────────────────────────────────────
VirtualBox:
  Machine → Take Snapshot → "Clean baseline"
  To revert: Machine → Restore Snapshot

UTM / Parallels / VMware: equivalent menu in VM settings.

Test the revert cycle:
  1. Create a file inside the VM: touch /tmp/test-change
  2. Revert to snapshot
  3. Confirm /tmp/test-change is gone

──────────────────────────────────────────────────────────────
STEP 4 — Confirm Docker in the VM
──────────────────────────────────────────────────────────────
Inside your VM:
  $ curl -fsSL https://get.docker.com | sh
  $ sudo usermod -aG docker $USER   # log out and back in
  $ docker run --rm hello-world     # should print "Hello from Docker"

──────────────────────────────────────────────────────────────
DELIVERABLE: lab-setup.md
──────────────────────────────────────────────────────────────
Document:
  1. Hypervisor and version you chose
  2. VM specs (OS, RAM, disk, CPU)
  3. Network mode and how you verified isolation
  4. Snapshot workflow (how to take one, how to revert)
  5. Docker smoke-test result
  6. Rebuild steps — enough for a teammate to reproduce from zero

Have a model review lab-setup.md for isolation gaps, then verify
against your actual network settings.
""")


def main() -> None:
    guide_only = "--guide" in sys.argv

    print("=" * 64)
    print("Lab 02 — Lab Setup Validator")
    print("=" * 64)

    if guide_only:
        print_guide()
        return

    print("\n[Checks]\n")
    docker_ok = check_docker()
    git_ok = check_git()

    if docker_ok:
        print("\n  ✓ Core tooling verified — Docker is ready.")
        print("  Next: set up an isolated VM and take a snapshot (see guide below).")
    else:
        print("\n  Install Docker first, then re-run this check.")

    print_guide()


if __name__ == "__main__":
    main()
