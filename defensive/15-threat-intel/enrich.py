#!/usr/bin/env python3
"""Indicator enrichment against a bundled ThreatFox-format feed.

Real threat intel is only as good as the analyst applying it. This script
loads a local feed (ThreatFox CSV format), looks up an indicator, and
returns verdict + context. The Pyramid of Pain tells you which indicator
types are actually painful for the adversary to rotate — and which are trivial.

Usage:
    python enrich.py <indicator>          # look up a single IOC
    python enrich.py --demo               # run the full demo scenario
"""
import csv
import sys
from pathlib import Path

FEED_PATH = Path(__file__).parent / "data" / "threatfox_sample.csv"

PYRAMID_COST = {
    "sha256_hash": "High — file hashes change with any recompile; not trivial to swap",
    "domain":      "Medium — domains take minutes to replace but require infrastructure work",
    "ip:port":     "Low-Medium — IPs rotate quickly; C2 infra is cheap to pivot",
    "url":         "Low — URLs change trivially; useful for immediate blocking only",
}


def load_feed(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def lookup(feed: list[dict], indicator: str) -> list[dict]:
    needle = indicator.strip().lower()
    return [r for r in feed if r["ioc"].strip().lower() == needle]


def verdict(hits: list[dict]) -> None:
    if not hits:
        print("  VERDICT: CLEAN — not found in feed (absence ≠ certainty; feed is a sample)")
        return
    for h in hits:
        ioc_type = h["ioc_type"]
        pain = PYRAMID_COST.get(ioc_type, "Unknown type")
        print(f"  VERDICT: MALICIOUS")
        print(f"    IOC type:   {ioc_type}")
        print(f"    Malware:    {h['malware']}")
        print(f"    Confidence: {h['confidence_level']}%")
        print(f"    Threat:     {h['threat_type']}")
        print(f"    First seen: {h['first_seen']}")
        print(f"    Last seen:  {h['last_seen']}")
        print(f"    Reference:  {h['reference'] or '(none)'}")
        print(f"    Pyramid of Pain: {pain}")


def demo(feed: list[dict]) -> None:
    """Walk through a realistic triage scenario."""
    print("=" * 60)
    print("Meridian Financial — Threat Intel Enrichment Demo")
    print("=" * 60)

    scenarios = [
        ("185.220.101.47:4444",
         "Outbound beacon seen in firewall logs — is this C2?"),
        ("evil-c2.meridiantest.invalid",
         "DNS query to unknown domain from a workstation"),
        ("44a9a9a9a9a9a9a9a9a9a9a9a9a9a9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8",
         "Hash of a file quarantined by AV — known malware?"),
        ("8.8.8.8:53",
         "DNS traffic to Google resolver — should we block it?"),
    ]

    for ioc, context in scenarios:
        print(f"\n[?] Context: {context}")
        print(f"    Indicator: {ioc}")
        hits = lookup(feed, ioc)
        verdict(hits)

    print("\n" + "=" * 60)
    print("Actionability assessment:")
    print("  ✓ Confident blocks: confidence >= 80, threat_type = botnet_cc/payload_delivery")
    print("  ~ Watch-list: confidence < 70 or stale (last_seen > 30 days ago)")
    print("  ✗ Do not block 8.8.8.8 — not in feed; legitimate infra; causes broad breakage")
    print("=" * 60)


def main() -> int:
    feed = load_feed(FEED_PATH)
    if "--demo" in sys.argv or len(sys.argv) == 1:
        demo(feed)
        return 0
    indicator = sys.argv[1]
    print(f"Enriching: {indicator}")
    verdict(lookup(feed, indicator))
    return 0


if __name__ == "__main__":
    sys.exit(main())
