#!/usr/bin/env python3
"""nmap scan runner and report parser.

Runs a structured three-phase nmap scan against the lab target and
prints a formatted report — the same output you'd hand to module 03
(vulnerability identification).

The lab target is the Vulhub nginx CVE-2017-7529 environment (a real,
named CVE: integer overflow in the nginx range filter, nginx <= 1.13.2).
`make target-up` stands it up on host :8080; version detection here
reveals an nginx in the vulnerable range — the finding module 03 acts on.

Phase 1: Host discovery + port scan (TCP connect, all major ports)
Phase 2: Service and version detection (-sV)
Phase 3: Default NSE scripts (-sC) against discovered services

> AUTHORIZATION REQUIRED — only scan systems you own or have explicit
> written permission to test. In this lab the target is the Vulhub
> container you stood up yourself.

Usage:
    python3 scan.py [host] [port]   # default: host.docker.internal 8080
    python3 scan.py --help
"""
from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_args   = [a for a in sys.argv[1:] if not a.startswith("--")]
TARGET  = _args[0] if len(_args) > 0 else "host.docker.internal"
_port   = _args[1] if len(_args) > 1 else "8080"
PORTS   = f"22,80,443,{_port},8443,3306,5432"
DIVIDER = "─" * 64


def run_nmap(args: list[str]) -> str:
    cmd = ["nmap"] + args
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout


def parse_xml(xml_str: str) -> dict:
    """Parse nmap -oX output into a structured dict."""
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return {"error": "XML parse failed", "raw": xml_str}

    report: dict = {"hosts": []}
    for host_el in root.findall("host"):
        status = host_el.find("status")
        if status is None or status.get("state") != "up":
            continue

        addr_el = host_el.find("address[@addrtype='ipv4']")
        hostname_el = host_el.find("hostnames/hostname")
        host: dict = {
            "ip": addr_el.get("addr") if addr_el is not None else "?",
            "hostname": hostname_el.get("name") if hostname_el is not None else "",
            "ports": [],
        }

        for port_el in host_el.findall("ports/port"):
            state_el = port_el.find("state")
            if state_el is None or state_el.get("state") != "open":
                continue
            service_el = port_el.find("service")
            port_info: dict = {
                "port":     port_el.get("portid"),
                "proto":    port_el.get("protocol"),
                "service":  service_el.get("name", "unknown") if service_el is not None else "unknown",
                "product":  service_el.get("product", "") if service_el is not None else "",
                "version":  service_el.get("version", "") if service_el is not None else "",
                "scripts":  {},
            }
            for script_el in port_el.findall("script"):
                port_info["scripts"][script_el.get("id", "")] = script_el.get("output", "")
            host["ports"].append(port_info)

        report["hosts"].append(host)
    return report


def print_report(report: dict) -> None:
    if "error" in report:
        print(f"  Parse error: {report['error']}")
        return
    for host in report["hosts"]:
        addr = host["ip"]
        if host["hostname"]:
            addr += f" ({host['hostname']})"
        print(f"\n  Host: {addr}")
        if not host["ports"]:
            print("  No open ports found.")
            return
        print(f"  {'PORT':>6}  {'SERVICE':15s}  {'VERSION'}")
        print(f"  {'─'*6}  {'─'*15}  {'─'*35}")
        for p in host["ports"]:
            ver = f"{p['product']} {p['version']}".strip()
            print(f"  {p['port']:>6}/tcp  {p['service']:15s}  {ver or '(no version detected)'}")
        print()
        for p in host["ports"]:
            if p["scripts"]:
                print(f"  NSE results — port {p['port']}/tcp:")
                for sid, output in p["scripts"].items():
                    first_line = output.strip().split("\n")[0][:80]
                    print(f"    [{sid}] {first_line}")
                print()


def demo() -> int:
    print("=" * 64)
    print(f"Port Scan: {TARGET}")
    print(f"Authorization: lab only (target is the Vulhub nginx CVE-2017-7529 container you stood up)")
    print("=" * 64)

    # Phase 1 — Host discovery + port discovery
    print(f"\n[Phase 1] Host discovery + TCP port scan")
    phase1_xml = run_nmap(["-n", "-Pn", f"-p{PORTS}", "-oX", "-", TARGET])
    report1 = parse_xml(phase1_xml)
    open_ports = [p["port"] for h in report1.get("hosts", []) for p in h["ports"]]
    print_report(report1)

    if not open_ports:
        print("  No open ports found — check that the victim container is running.")
        return 1

    print(DIVIDER)

    # Phase 2 — Service and version detection
    print(f"\n[Phase 2] Service and version detection (-sV)")
    ports_str = ",".join(open_ports)
    phase2_xml = run_nmap(["-n", "-Pn", "-sV", f"-p{ports_str}", "-oX", "-", TARGET])
    report2 = parse_xml(phase2_xml)
    print_report(report2)

    print(DIVIDER)

    # Phase 3 — Default NSE scripts
    print(f"\n[Phase 3] NSE default scripts (-sC) — service enumeration")
    phase3_xml = run_nmap([
        "-n", "-Pn", "-sV", "-sC",
        f"-p{ports_str}", "-oX", "-", TARGET
    ])
    report3 = parse_xml(phase3_xml)
    print_report(report3)

    print("=" * 64)
    print("Scan summary")
    print("=" * 64)
    all_ports = []
    for host in report3.get("hosts", []):
        for p in host["ports"]:
            ver = f"{p['product']} {p['version']}".strip()
            all_ports.append(f"  {p['port']:>6}/tcp  {p['service']:15s}  {ver}")
    print(f"\n  Target: {TARGET}")
    print(f"  Open ports: {len(all_ports)}")
    for line in all_ports:
        print(line)
    print(f"""
  Next steps (→ module 03 — vulnerability identification):
    • Run `searchsploit nginx` against the discovered version.
    • The detected nginx version is in the CVE-2017-7529 range
      (<= 1.13.2) — confirm it on NVD: integer overflow in the range
      filter, leaks cache file headers/memory.
    • Server/version banners hint at the application stack.
""")
    return 0


if __name__ == "__main__":
    sys.exit(demo())
