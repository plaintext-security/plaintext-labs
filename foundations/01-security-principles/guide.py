#!/usr/bin/env python3
"""
Security Principles lab — Equifax principle-autopsy guide + CISA KEV sampler.

Prints the principle-autopsy template and fetches recent high-profile CVEs
from the CISA Known Exploited Vulnerabilities catalog as breach candidates
(for the Stretch: re-run the autopsy on a different breach).

Usage:
    python3 guide.py          # print guide + sample KEV entries
    python3 guide.py --check  # smoke-check a completed principle-autopsy.md
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
DIVIDER = "─" * 64


def fetch_kev(n: int = 5) -> list[dict]:
    try:
        with urllib.request.urlopen(KEV_URL, timeout=8) as r:
            data = json.loads(r.read())
        vulns = data.get("vulnerabilities", [])
        # Return the n most recently added, highest-profile ones
        return vulns[-n:][::-1]
    except Exception as e:
        return [{"error": str(e)}]


def print_guide() -> None:
    print("=" * 64)
    print("Security Principles — Equifax Principle-Autopsy Guide")
    print("=" * 64)

    print("""
Module 01: The Equifax Autopsy — Map Every Failure to a First Principle

This lab has no tooling — only a documented breach and your judgment.
Your deliverable is principle-autopsy.md. The blanks below are scaffolding,
not answers: you fill every cell from the GAO report (gao.gov/products/gao-18-559).

──────────────────────────────────────────────────────────────
PRINCIPLE AUTOPSY TEMPLATE  (copy into principle-autopsy.md)
──────────────────────────────────────────────────────────────

## Equifax (2017) — Principle Autopsy
Source: GAO-18-559 + CISA KEV / NVD for CVE-2017-5638

### Prediction (write this BEFORE you read — grade it at the end)
The one thing I think failed:

### The chain — one row per hop
| Hop | The failure (what happened) | Principle that failed | The one change that breaks the chain here |
|-----|-----------------------------|-----------------------|-------------------------------------------|
| 1. The entry (unpatched Struts) |  |  |  |
| 2. The spread (flat network)    |  |  |  |
| 3. The blind spot (expired cert)|  |  |  |

### Bottom line (2 sentences)
Was there one thing that failed? →
Why "they didn't patch" is an incomplete answer →

### Prediction scorecard
What my step-1 guess got right / missed:

──────────────────────────────────────────────────────────────
NEXT: build cert_check.py (your exercise) — see lab.md → "Automate & own it",
then `make cert-demo`. Stretch: re-run this autopsy on another breach using a
CISA KEV entry below.
""")


def print_kev_samples(entries: list[dict]) -> None:
    print(DIVIDER)
    print("Recent CISA KEV entries — good breach starting points")
    print(DIVIDER)
    print()
    if any("error" in e for e in entries):
        print("  (Could not reach CISA KEV — work offline or check connectivity)")
        print("  Alternatively: https://www.cisa.gov/known-exploited-vulnerabilities-catalog")
        print()
        return
    for e in entries:
        print(f"  CVE:     {e.get('cveID', '—')}")
        print(f"  Vendor:  {e.get('vendorProject', '—')}")
        print(f"  Product: {e.get('product', '—')}")
        print(f"  Name:    {e.get('vulnerabilityName', '—')}")
        print(f"  Added:   {e.get('dateAdded', '—')}")
        desc = e.get('shortDescription', '')
        if desc:
            print(f"  Desc:    {desc[:120]}{'…' if len(desc) > 120 else ''}")
        print()


def check_analysis(path: Path) -> int:
    text = path.read_text(errors="replace")
    print(f"\n[Check] Validating: {path.name}\n")

    checks = [
        (r"cia|confidential|integrity|availab|aaa|account",  "CIA / AAA addressed"),
        (r"least.priv|defense.in.depth|segment|princip",     "Security principle named"),
        (r"patch|segment|monitor|cert|control|breaking",     "Breaking-change control identified"),
        (r"struts|cve-2017-5638|equifax|expired",            "Grounded in the Equifax specifics"),
        (r"predict|chain|bottom.line|no single",             "Prediction scored + chain bottom line"),
    ]

    passed = 0
    for pattern, label in checks:
        found = bool(re.search(pattern, text, re.IGNORECASE))
        print(f"  {'✓' if found else '✗'}  {label}")
        if found:
            passed += 1

    print(f"\n  Score: {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 1


def main() -> None:
    if "--check" in sys.argv:
        candidates = [Path("principle-autopsy.md")] + list(Path(".").glob("*.md"))
        for p in candidates:
            if p.exists() and ("autopsy" in p.name.lower() or "principle" in p.name.lower()):
                sys.exit(check_analysis(p))
        print("No principle-autopsy.md found in current directory.")
        sys.exit(1)

    print_guide()
    entries = fetch_kev(5)
    print_kev_samples(entries)

    print(DIVIDER)
    print("When done:")
    print("  python3 guide.py --check   # smoke-check your principle-autopsy.md")
    print("  (a keyword smell test — not a grade; your committed autopsy is the proof)")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()
