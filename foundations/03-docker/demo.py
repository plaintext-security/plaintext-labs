#!/usr/bin/env python3
"""
Docker Lab — container lifecycle demo.

Demonstrates:
  1. Run + inspect a throwaway container
  2. Publish a port and reach the service
  3. Build an image from a Dockerfile
  4. Inspect the running user — root-by-default
  5. Show the fixed Dockerfile (non-root)

Usage: python3 demo.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

DATA_DIR = Path("/lab/data") if Path("/lab/data").exists() else Path("data")
DIVIDER = "─" * 64


def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"[Step] {title}")
    print(DIVIDER)


def run(cmd: str, capture: bool = True, input: bytes | None = None) -> tuple[int, str]:
    r = subprocess.run(cmd, shell=True, capture_output=capture, text=True,
                       input=input.decode() if input else None)
    return r.returncode, (r.stdout + r.stderr).strip()


def demo_interactive() -> None:
    section("1 — Throwaway container: run, look around, exit")
    print()
    print("  $ docker run --rm alpine sh -c 'cat /etc/os-release | head -3'")
    rc, out = run("docker run --rm alpine sh -c 'cat /etc/os-release | head -3'")
    if rc == 0:
        for line in out.splitlines():
            print(f"    {line}")
        print()
        print("  ✓ Container ran and exited. --rm removes it automatically.")
    else:
        print(f"  Error: {out}")
    print()
    print("  After the container exits, it's gone:")
    print("  $ docker ps -a    # should not show the alpine container")


def demo_service() -> None:
    section("2 — Service container: build, publish port, reach from host")
    print()
    print("  Building the demo web server from app/Dockerfile…")
    rc, out = run("docker build -t plaintext/docker-demo-server app/ 2>&1")
    if rc != 0:
        print(f"  Build failed: {out[:200]}")
        return
    print("  ✓ Built image: plaintext/docker-demo-server")

    print("  Starting container on port 18000…")
    run("docker rm -f docker-lab-demo 2>/dev/null")
    rc, _ = run("docker run -d --rm --name docker-lab-demo -p 18000:8000 plaintext/docker-demo-server")
    if rc != 0:
        print("  Could not start container")
        return
    time.sleep(1)

    # Reach it
    rc, out = run("curl -s http://localhost:18000/")
    if rc == 0:
        print(f"  $ curl http://localhost:18000/")
        print(f"  {out.strip()}")
        print("  ✓ Service is reachable from the host on port 18000")
    else:
        print(f"  Could not reach service: {out}")

    run("docker rm -f docker-lab-demo 2>/dev/null")
    print()
    print("  Container cleaned up.")


def demo_inspect_user() -> None:
    section("3 — Inspect running user — root-by-default")
    print()
    print("  $ docker run --rm plaintext/docker-demo-server whoami")
    rc, out = run("docker run --rm plaintext/docker-demo-server whoami 2>&1")
    print(f"  {out}")
    print()
    if "root" in out:
        print("  ⚠ The container runs as root (uid=0).")
        print("  If this container is compromised, the attacker gets root inside it.")
        print("  With a container escape CVE, that can become root on the host.")
    print()
    print("  $ docker inspect plaintext/docker-demo-server | grep User")
    rc, out = run("docker inspect plaintext/docker-demo-server 2>/dev/null | python3 -c \""
                  "import json,sys; cfg=json.load(sys.stdin)[0]; "
                  "print('User:', cfg.get('Config',{}).get('User','(not set — defaults to root)'))\"")
    print(f"  {out or '(not set — defaults to root)'}")


def demo_fixed_dockerfile() -> None:
    section("4 — The fix: non-root user in Dockerfile.fixed")
    print()
    fixed = DATA_DIR / "Dockerfile.fixed"
    if fixed.exists():
        for line in fixed.read_text().splitlines():
            print(f"  {line}")
    print()
    print("  Key lines:")
    print("    RUN adduser --disabled-password appuser   # create a non-root user")
    print("    USER appuser                              # drop privileges before CMD")
    print()
    print("  Build and verify:")
    print("    docker build -f data/Dockerfile.fixed -t demo-server-fixed app/")
    print("    docker run --rm demo-server-fixed whoami   # should print 'appuser'")


def main() -> None:
    print("=" * 64)
    print("Meridian Financial — Docker Lab Demo")
    print("=" * 64)
    print()
    print("Covers the container lifecycle and the root-by-default security issue.")

    demo_interactive()
    demo_service()
    demo_inspect_user()
    demo_fixed_dockerfile()

    print(f"\n{'=' * 64}")
    print("Deliverable: docker-notes.md — your Dockerfile, the docker run lines,")
    print("and one note on the security-relevant default you found.")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
