#!/usr/bin/env python3
"""Refresh against the current CISA KEV catalog and pick a runnable target.

The "what's actively exploited right now" list moves every few days. This tool
answers the practitioner's first question — *of everything CISA confirms is being
exploited in the wild, which recent entry can I stand up, attack, and detect today?*
— by cross-referencing the live KEV catalog against a bundled map of CVEs that have
a ready Vulhub environment.

Two modes, on purpose:
  * default (offline, deterministic) reads the bundled snapshot in data/ — this is
    what `make demo` and CI run, so it never depends on the network being up;
  * --live fetches the real, current catalog from CISA so you work against today's
    list. (Source of truth: the CISA KEV catalog JSON feed.)

Usage:
    python kev_refresh.py                 # rank recent KEV entries (bundled snapshot)
    python kev_refresh.py --live          # ...against the live CISA catalog
    python kev_refresh.py --recommend     # print the single best runnable target
    python kev_refresh.py --json          # machine-readable output
    python kev_refresh.py --cve CVE-...   # show one entry + whether it has a target

The recommender is a *lead*, not gospel: KEV tells you it's exploited in the wild,
the Vulhub map tells you it's reproducible here. You still read the advisory and the
Vulhub README before you attack anything. AI drafts, you verify against CISA.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
SNAPSHOT = HERE / "data" / "kev_snapshot.json"
CATALOG = HERE / "data" / "vulhub_catalog.json"

# Canonical CISA KEV feed. The www.cisa.gov host occasionally rejects non-browser
# clients (HTTP 403) from locked-down networks; the cisagov GitHub mirror serves the
# identical catalog and is the documented fallback.
KEV_FEED = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
KEV_MIRROR = "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json"
UA = "plaintext-kev-lab/1.0 (+https://github.com/plaintext-security)"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text())["targets"]


def load_kev(live: bool) -> dict:
    if not live:
        return json.loads(SNAPSHOT.read_text())
    last_err = None
    for url in (KEV_FEED, KEV_MIRROR):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            print(f"[+] Fetched live catalog v{data.get('catalogVersion')} "
                  f"({len(data['vulnerabilities'])} entries) from {url.split('/')[2]}",
                  file=sys.stderr)
            return data
        except Exception as exc:  # network / proxy / 403 — fall through to the mirror
            last_err = exc
            print(f"[!] {url.split('/')[2]} failed: {exc}", file=sys.stderr)
    raise SystemExit(f"error: could not reach the live KEV catalog ({last_err}); "
                     f"run without --live to use the bundled snapshot.")


def days_old(date_added: str) -> int:
    d = datetime.strptime(date_added, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - d).days


def enrich(kev: dict, catalog: dict) -> list[dict]:
    """Attach 'runnable' (has a Vulhub target) + recency to each KEV entry."""
    rows = []
    for v in kev["vulnerabilities"]:
        target = catalog.get(v["cveID"])
        rows.append({
            "cveID": v["cveID"],
            "vendor": v["vendorProject"],
            "product": v["product"],
            "dateAdded": v["dateAdded"],
            "daysOld": days_old(v["dateAdded"]),
            "ransomware": v.get("knownRansomwareCampaignUse", "Unknown"),
            "shortDescription": v.get("shortDescription", ""),
            "runnable": target is not None,
            "target": target,
        })
    # Most recent first; runnable entries float up within the same date.
    rows.sort(key=lambda r: (r["dateAdded"], r["runnable"]), reverse=True)
    return rows


def fmt_table(rows: list[dict], limit: int) -> None:
    print(f"{'CVE':<18} {'Added':<11} {'Age':>4}  {'Ransom':<8} {'Run':<4} Product")
    print("-" * 88)
    for r in rows[:limit]:
        run = "YES" if r["runnable"] else "-"
        ransom = (r["ransomware"] or "Unknown")[:7]
        prod = f"{r['vendor']} {r['product']}"[:34]
        print(f"{r['cveID']:<18} {r['dateAdded']:<11} {r['daysOld']:>3}d  "
              f"{ransom:<8} {run:<4} {prod}")


def recommend(rows: list[dict]) -> dict | None:
    """The most recently-added KEV entry that we can actually stand up here."""
    runnable = [r for r in rows if r["runnable"]]
    return runnable[0] if runnable else None


def reference(rows: list[dict]) -> dict | None:
    """The one target this lab ships a worked exploit + detection for (the demo)."""
    return next((r for r in rows if r["runnable"] and r["target"].get("reference")), None)


def print_recommendation(rec: dict | None) -> int:
    if not rec:
        print("No recent KEV entry maps to a bundled Vulhub target. "
              "Extend data/vulhub_catalog.json, or pick a target from "
              "https://github.com/vulhub/vulhub and add it.")
        return 1
    t = rec["target"]
    print("=" * 60)
    print("RECOMMENDED TARGET — exploit it, then detect it")
    print("=" * 60)
    print(f"  CVE:         {rec['cveID']}")
    print(f"  Product:     {rec['product']}  ({rec['vendor']})")
    print(f"  KEV added:   {rec['dateAdded']}  ({rec['daysOld']} days ago)")
    print(f"  Ransomware:  {rec['ransomware']}")
    print(f"  Class:       {t['exploit_class']}")
    print(f"  Vulhub:      https://github.com/vulhub/vulhub/tree/master/{t['vulhub_path']}")
    print(f"  Service:     port {t['service_port']}")
    print(f"  Detect:      {t['detect_note']}")
    print("=" * 60)
    print("  Next: stand it up (see lab.md), exploit it, then write the detection.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true",
                    help="fetch the live CISA KEV catalog instead of the bundled snapshot")
    ap.add_argument("--recommend", action="store_true",
                    help="print the single most-recent runnable target and exit")
    ap.add_argument("--reference", action="store_true",
                    help="print the lab's shipped reference target (the one the demo exploits)")
    ap.add_argument("--cve", help="show one CVE and whether it has a runnable target")
    ap.add_argument("--limit", type=int, default=20, help="rows to show in the table")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    kev = load_kev(args.live)
    catalog = load_catalog()
    rows = enrich(kev, catalog)

    if args.cve:
        match = next((r for r in rows if r["cveID"].lower() == args.cve.lower()), None)
        if not match:
            print(f"{args.cve} not in the {'live catalog' if args.live else 'snapshot'}.")
            return 1
        print(json.dumps(match, indent=2) if args.json else "")
        if not args.json:
            print_recommendation(match) if match["runnable"] else \
                print(f"{match['cveID']} is in KEV ({match['dateAdded']}) but has no "
                      f"bundled Vulhub target. Add one to data/vulhub_catalog.json.")
        return 0

    if args.reference:
        rec = reference(rows)
        if args.json:
            print(json.dumps(rec, indent=2))
            return 0 if rec else 1
        return print_recommendation(rec)

    if args.recommend:
        rec = recommend(rows)
        if args.json:
            print(json.dumps(rec, indent=2))
            return 0 if rec else 1
        return print_recommendation(rec)

    if args.json:
        print(json.dumps(rows[:args.limit], indent=2))
        return 0

    src = "LIVE CISA catalog" if args.live else f"bundled snapshot ({kev.get('catalogVersion')})"
    print(f"# CISA KEV — {src}: {len(rows)} entries, "
          f"{sum(r['runnable'] for r in rows)} with a runnable target\n")
    fmt_table(rows, args.limit)
    rec = recommend(rows)
    print()
    print_recommendation(rec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
