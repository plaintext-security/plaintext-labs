#!/usr/bin/env python3
"""Passive recon attack-surface map.

Passive recon collects public data without directly probing the target:
  - Certificate Transparency logs (crt.sh) reveal subdomains
  - DNS enumeration maps hostnames to IPs and ASNs
  - HTTP banner/header grabbing fingerprints the tech stack
  - SPF/MX records reveal email infrastructure and cloud providers

This harness loads pre-captured recon output for example.com (the
RFC-2606 reserved domain) so the demo is deterministic and offline.
The same code works against live targets (see --live flag instructions
at the bottom).

> AUTHORIZATION REQUIRED — only run live recon against targets you own
> or have explicit written permission to test. Passive recon stays
> within scope but still creates logs on the target's DNS servers.

Usage:
    python3 recon.py          # demo mode — bundled example.com data
    python3 recon.py --report  # also write recon-report.md
"""
from __future__ import annotations

import json
import sys
import textwrap
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DIVIDER  = "─" * 64


def wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=72, initial_indent=prefix,
                         subsequent_indent=prefix)


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_json(filename: str) -> dict | list:
    return json.loads((DATA_DIR / filename).read_text())


# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze_crt(crt_entries: list[dict]) -> set[str]:
    """Extract unique subdomains from certificate transparency entries."""
    subdomains: set[str] = set()
    for entry in crt_entries:
        for name in entry["name_value"].split("\n"):
            name = name.strip().lstrip("*.")
            if name:
                subdomains.add(name)
    return subdomains


def group_by_ip(subdomains: list[dict]) -> dict[str, list[str]]:
    """Group hostnames by IP — useful for finding shared-hosting clusters."""
    groups: dict[str, list[str]] = {}
    for sd in subdomains:
        ip = sd["ip"]
        groups.setdefault(ip, []).append(sd["hostname"])
    return groups


def score_interest(host: str, tech: dict) -> int:
    """Priority score for a discovered asset (higher = more interesting)."""
    score = 0
    status = tech.get("status", 200)
    notes  = tech.get("notes", "").lower()
    techs  = " ".join(tech.get("technologies", [])).lower()

    if status == 200:
        score += 20
    if tech.get("interesting"):
        score += 30
    if "cve" in notes:
        score += 25
    if "dev" in host or "staging" in host:
        score += 10
    if "backup" in host or "s3" in host.lower() or "s3" in techs:
        score += 20
    if "jira" in host or "confluence" in host:
        score += 15
    if "api" in host and "swagger" in techs:
        score += 20
    if "vpn" in host or "gateway" in host:
        score += 15
    return score


# ── Demo ──────────────────────────────────────────────────────────────────────

def demo(write_report: bool = False) -> int:
    crt_entries = load_json("crt_sh.json")
    dns_data    = load_json("dns_enum.json")
    tech_data   = load_json("tech_stack.json")

    domain = dns_data["domain"]

    print("=" * 64)
    print(f"Passive Recon — {domain}")
    print(f"Methodology: crt.sh → DNS enumeration → tech fingerprinting")
    print(f"Target scope: {domain} and all subdomains")
    print(f"Authorization: example.com (RFC-2606 reserved) demo estate / your own authorized domain in --live mode")
    print("=" * 64)

    # ── Step 1: Certificate Transparency ─────────────────────────────────────
    print(f"\n[1] Certificate Transparency — crt.sh")
    print(f"    Source: https://crt.sh/?q=%.{domain}")
    print()
    ct_subdomains = analyze_crt(crt_entries)
    print(f"  Found {len(crt_entries)} CT log entries → {len(ct_subdomains)} unique subdomains:")
    for sd in sorted(ct_subdomains):
        print(f"    • {sd}")
    print()
    print(wrap("Certificate transparency is often the richest passive source. "
               "Wildcard certs expose all subdomains at once; expired certs "
               "reveal assets that were once active. The expired S3 cert "
               "(backups.example.com, expired 2023-08) is a flag — "
               "a forgotten bucket may still be public."))

    # ── Step 2: DNS enumeration ───────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print(f"[2] DNS enumeration — NS, MX, SPF, subdomains")
    print()
    print(f"  Nameservers: {', '.join(dns_data['ns_records'])}")
    print(f"  MX records:")
    for mx in dns_data["mx_records"]:
        print(f"    priority {mx['priority']}: {mx['host']}  {mx['ip']}")
    print(f"  SPF: {next((t for t in dns_data['txt_records'] if t.startswith('v=spf')), 'none')}")
    print()

    # IP grouping
    ip_groups = group_by_ip(dns_data["subdomains"])
    print(f"  Subdomains ({len(dns_data['subdomains'])} resolved), grouped by IP:")
    for ip, hosts in sorted(ip_groups.items()):
        asn = next(sd["asn"] for sd in dns_data["subdomains"] if sd["ip"] == ip)
        print(f"    {ip:18s}  {asn:30s}  {', '.join(h.split('.')[0] for h in hosts)}")

    print()
    print(wrap("SPF includes sendgrid.net — email may use a third-party relay "
               "(phishing simulation could abuse this). Two subdomains on "
               "198.51.100.55 (HE ASN): dev and staging share infrastructure — "
               "a vuln in one may be present in both."))

    # ── Step 3: Tech stack fingerprinting ─────────────────────────────────────
    print(f"\n{DIVIDER}")
    print(f"[3] Technology fingerprinting — HTTP banners & headers")
    print()
    scored = []
    for host, tech in tech_data.items():
        score = score_interest(host, tech)
        scored.append((score, host, tech))
    scored.sort(reverse=True)

    print(f"  {'Host':40s}  {'Status':>6}  {'Score':>5}  Stack")
    print(f"  {'-'*40}  {'-'*6}  {'-'*5}  {'-'*30}")
    for score, host, tech in scored:
        stack = ", ".join(tech["technologies"][:2])
        flag  = "⚠" if score >= 50 else " "
        print(f"  {flag} {host:39s}  {tech.get('status',200):>6}  {score:>5}  {stack}")

    # ── Step 4: Priority targets ───────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print(f"[4] Priority targets (score ≥ 50)")
    print()
    for score, host, tech in scored:
        if score < 50:
            continue
        print(f"  [{score:>3}/100] {host}")
        if tech.get("notes"):
            print(f"          {tech['notes']}")
        print()

    # ── Step 5: Attack-surface summary ────────────────────────────────────────
    print(f"{'=' * 64}")
    print(f"Attack-surface summary — {domain}")
    print(f"{'=' * 64}")
    top_host, top_tech = scored[0][1], scored[0][2]
    print(f"""
  Total subdomains discovered:  {len(ct_subdomains)} (CT) + {len(dns_data['subdomains'])} (DNS resolved)
  IP ranges touched:            Cloudflare CDN, AWS, Atlassian, HE
  Email provider:               Google + Sendgrid relay

  Top target: {top_host}
  Reason: {top_tech.get('notes', 'high-interest stack')}

  Recommended next phase (module 02 — Scanning):
    1. Active scan {top_host} (authorized only).
    2. Check vpn.example.com for FortiGate CVE-2024-21762.
    3. Enumerate the S3 bucket at backups.example.com for
       public read/ListObject (test with: aws s3 ls s3://backups.example.com --no-sign-request).
    4. Verify Jira/Confluence (CVE-2023-22515) on jira.example.com.
""")

    if write_report:
        _write_report(domain, ct_subdomains, dns_data, scored)

    return 0


def _write_report(domain: str, subdomains: set[str], dns: dict,
                  scored: list[tuple]) -> None:
    out = Path("recon-report.md")
    lines = [
        f"# Recon Report — {domain}",
        f"Date: {date.today().isoformat()}",
        "",
        "## Scope",
        f"Target: `{domain}` and all subdomains. Passive recon only.",
        "Authorization: lab exercise against example.com (RFC-2606 reserved) "
        "or your own authorized domain in --live mode.",
        "",
        "## Asset inventory",
        "",
        "| Hostname | IP | ASN | Stack | Score | Notes |",
        "|----------|-----|-----|-------|-------|-------|",
    ]
    for score, host, tech in scored:
        ip  = next((sd["ip"] for sd in dns["subdomains"]
                    if sd["hostname"] == host), "—")
        asn = next((sd["asn"].split()[0] for sd in dns["subdomains"]
                    if sd["hostname"] == host), "—")
        stack = ", ".join(tech["technologies"][:2])
        notes = tech.get("notes", "")
        lines.append(f"| {host} | {ip} | {asn} | {stack} | {score} | {notes} |")

    lines += [
        "",
        "## Top priority targets",
        "",
    ]
    for score, host, tech in scored:
        if score < 50:
            continue
        lines.append(f"### {host}  (score {score}/100)")
        lines.append(tech.get("notes", ""))
        lines.append("")

    lines += [
        "## Sources",
        f"- Certificate Transparency: https://crt.sh/?q=%.{domain}",
        "- DNS: passive enumeration (no zone transfer attempted)",
        "- Tech stack: HTTP banner/header analysis",
        "",
        "## Next steps",
        "- Active scan of top-priority targets (authorization confirmed).",
        "- Verify S3 bucket public access policy.",
        "- Check FortiGate VPN and Jira for identified CVEs.",
    ]
    out.write_text("\n".join(lines))
    print(f"  [Report written to {out}]")


if __name__ == "__main__":
    write_report = "--report" in sys.argv
    sys.exit(demo(write_report))
