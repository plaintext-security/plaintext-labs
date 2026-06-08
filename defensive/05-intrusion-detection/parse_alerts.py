#!/usr/bin/env python3
"""Parse Suricata eve.json: summarise alerts, extract indicators, triage severity.

Suricata produces a stream of JSON events (eve.json). The alerts in it are only
useful if you can answer: which signatures fired the most, what hosts are
involved, and which alerts are worth acting on versus noise. This script does
that summary — the same logic you'd write once and run after every PCAP analysis.

Usage:
    python3 parse_alerts.py [eve.json]    # default: data/eve.json
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

EVE_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data" / "eve.json"

SEVERITY_LABEL = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}


def load_alerts(path: Path) -> list[dict]:
    alerts = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            if ev.get("event_type") == "alert":
                alerts.append(ev)
        except json.JSONDecodeError:
            pass
    return alerts


def main() -> int:
    alerts = load_alerts(EVE_PATH)
    print("=" * 62)
    print(f"Suricata Alert Summary — {EVE_PATH.name}")
    print(f"{len(alerts)} alert events")
    print("=" * 62)

    # By severity
    by_sev: Counter = Counter(
        SEVERITY_LABEL.get(a["alert"]["severity"], "UNKNOWN") for a in alerts
    )
    print("\n[Severity breakdown]")
    for sev in ("HIGH", "MEDIUM", "LOW"):
        print(f"  {sev:<8}  {by_sev.get(sev, 0)}")

    # By signature
    print("\n[Top signatures]")
    sig_counts: Counter = Counter(a["alert"]["signature"] for a in alerts)
    for sig, n in sig_counts.most_common(10):
        sev = next((SEVERITY_LABEL.get(a["alert"]["severity"], "?")
                    for a in alerts if a["alert"]["signature"] == sig), "?")
        print(f"  [{sev:<6}]  {n}×  {sig}")

    # Involved hosts
    print("\n[Internal hosts generating/receiving alerts]")
    internal_hosts: set = set()
    for a in alerts:
        for field in ("src_ip", "dest_ip"):
            ip = a.get(field, "")
            if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172."):
                internal_hosts.add(ip)
    for h in sorted(internal_hosts):
        outbound = sum(1 for a in alerts if a.get("src_ip") == h)
        inbound  = sum(1 for a in alerts if a.get("dest_ip") == h)
        print(f"  {h:<18}  outbound alerts: {outbound}  inbound alerts: {inbound}")

    # External IPs involved
    ext_ips: Counter = Counter()
    for a in alerts:
        for field in ("src_ip", "dest_ip"):
            ip = a.get(field, "")
            if ip and not (ip.startswith("10.") or ip.startswith("192.168.")
                          or ip.startswith("172.") or ip == "8.8.8.8"):
                ext_ips[ip] += 1
    if ext_ips:
        print("\n[External IPs in alerts]")
        for ip, n in ext_ips.most_common():
            print(f"  {ip:<20}  {n} alert(s)")

    # High-severity alerts with context
    high = [a for a in alerts if a["alert"]["severity"] == 1]
    if high:
        print(f"\n[HIGH severity alert detail ({len(high)} events)]")
        seen_sigs: set = set()
        for a in high:
            sig = a["alert"]["signature"]
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)
            ts = a["timestamp"][:19]
            src = f"{a.get('src_ip','?')}:{a.get('src_port','?')}"
            dst = f"{a.get('dest_ip','?')}:{a.get('dest_port','?')}"
            count = sum(1 for x in high if x["alert"]["signature"] == sig)
            print(f"\n  [{ts}] {sig}")
            print(f"    {src} → {dst}  ({count}× total)")
            cat = a["alert"].get("category", "")
            if cat:
                print(f"    Category: {cat}")

    # Download events
    downloads = [a for a in alerts if a.get("http", {}).get("url", "").endswith(
        (".ps1", ".exe", ".bat", ".vbs"))]
    if downloads:
        print(f"\n[Suspicious file downloads in alerts]")
        for a in downloads:
            h = a.get("http", {})
            print(f"  {h.get('http_method','?')} {h.get('hostname','?')}{h.get('url','?')}"
                  f"  [{h.get('length',0)} bytes]")

    # Custom rule template
    print("\n── Custom rule template ────────────────────────────────────")
    # Find the C2 host from HTTP alerts
    c2_hosts = {a["http"]["hostname"] for a in alerts if "http" in a and "hostname" in a.get("http", {})}
    if c2_hosts:
        host = sorted(c2_hosts)[0]
        print(f"""  # Block all traffic to the C2 host observed in this session:
  alert http any any -> any any (\\
      msg:"LOCAL C2 Domain {host}"; \\
      http.host; content:"{host}"; \\
      classtype:trojan-activity; sid:9000001; rev:1;)""")
    print()
    print("Validate your rule: suricata -r capture.pcap -S local.rules -l .")
    return 0


if __name__ == "__main__":
    sys.exit(main())
