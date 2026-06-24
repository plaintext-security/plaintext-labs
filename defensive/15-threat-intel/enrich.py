#!/usr/bin/env python3
"""Indicator enrichment against a real abuse.ch ThreatFox feed.

Real threat intel is only as good as the analyst applying it. This script
loads a ThreatFox CSV feed, looks up an indicator, and returns verdict +
context. The Pyramid of Pain tells you which indicator types are actually
painful for the adversary to rotate — and which are trivial.

The feed this enriches is meant to be a LIVE pull: run `make fetch-data`
first (see the lab) to download today's ThreatFox recent-IOC export to
`data/threatfox_recent.csv`. If that live snapshot is absent, the script
falls back to the small committed snapshot `data/threatfox_sample.csv`
so the demo still runs offline.

Both files use the real ThreatFox bulk-export CSV schema, so the same
parser works against either:
    https://threatfox.abuse.ch/export/csv/recent/

Usage:
    python enrich.py <indicator>          # look up a single IOC
    python enrich.py --demo               # run the full demo scenario
"""
import csv
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
LIVE_FEED = DATA_DIR / "threatfox_recent.csv"      # written by `make fetch-data`
SEED_FEED = DATA_DIR / "threatfox_sample.csv"      # committed offline snapshot

PYRAMID_COST = {
    "sha256_hash": "High — file hashes change with any recompile; not trivial to swap",
    "domain":      "Medium — domains take minutes to replace but require infrastructure work",
    "ip:port":     "Low-Medium — IPs rotate quickly; C2 infra is cheap to pivot",
    "url":         "Low — URLs change trivially; useful for immediate blocking only",
}


def feed_path() -> Path:
    """Prefer the live ThreatFox pull; fall back to the committed snapshot."""
    return LIVE_FEED if LIVE_FEED.exists() else SEED_FEED


def load_feed(path: Path) -> list[dict]:
    # ThreatFox prefixes its export with comment lines beginning with '#'.
    with open(path, newline="") as fh:
        rows = [ln for ln in fh if not ln.lstrip().startswith("#")]
    return list(csv.DictReader(rows))


def lookup(feed: list[dict], indicator: str) -> list[dict]:
    needle = indicator.strip().lower()
    return [r for r in feed if r.get("ioc_value", "").strip().lower() == needle]


def verdict(hits: list[dict]) -> None:
    if not hits:
        print("  VERDICT: CLEAN — not found in feed (absence != certainty; feed is a sample)")
        return
    for h in hits:
        ioc_type = h.get("ioc_type", "")
        pain = PYRAMID_COST.get(ioc_type, "Unknown type")
        print(f"  VERDICT: MALICIOUS")
        print(f"    IOC type:   {ioc_type}")
        print(f"    Malware:    {h.get('malware_printable') or h.get('fk_malware', '?')}")
        print(f"    Confidence: {h.get('confidence_level', '?')}%")
        print(f"    Threat:     {h.get('threat_type', '?')}")
        print(f"    First seen: {h.get('first_seen_utc', '?')}")
        print(f"    Last seen:  {h.get('last_seen_utc', '?')}")
        print(f"    Reference:  {h.get('reference') or '(none)'}")
        print(f"    Pyramid of Pain: {pain}")


def demo(feed: list[dict], source: Path) -> None:
    """Walk through a realistic triage scenario."""
    print("=" * 60)
    print("Threat Intel Enrichment Demo")
    is_live = source.name == LIVE_FEED.name
    tag = "LIVE ThreatFox pull" if is_live else "committed offline snapshot"
    print(f"Feed: {source.name}  ({tag}, {len(feed)} IOCs)")
    print("=" * 60)
    if not is_live:
        print("  Note: enriching against the committed snapshot. Run `make")
        print("  fetch-data` first to enrich against TODAY's live ThreatFox feed.")

    scenarios = [
        ("185.220.101.47:4444",
         "Outbound beacon seen in firewall logs — is this C2?"),
        ("cdn-update-sync.example.invalid",
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
    print("  + Confident blocks: confidence >= 80, threat_type = botnet_cc/payload_delivery")
    print("  ~ Watch-list: confidence < 70 or stale (last_seen > 30 days ago)")
    print("  - Do not block 8.8.8.8 — not in feed; legitimate infra; causes broad breakage")
    print("=" * 60)


def main() -> int:
    source = feed_path()
    feed = load_feed(source)
    if "--demo" in sys.argv or len(sys.argv) == 1:
        demo(feed, source)
        return 0
    indicator = sys.argv[1]
    print(f"Enriching: {indicator}  (feed: {source.name})")
    verdict(lookup(feed, indicator))
    return 0


if __name__ == "__main__":
    sys.exit(main())
