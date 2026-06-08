#!/usr/bin/env python3
"""
Security Principles lab — breach analysis guide + CISA KEV sampler.

Prints the breach-analysis template and fetches recent high-profile CVEs
from the CISA Known Exploited Vulnerabilities catalog as breach candidates.

Usage:
    python3 guide.py          # print guide + sample KEV entries
    python3 guide.py --check  # validate a completed breach-analysis.md
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
    print("Security Principles — Breach Analysis Guide")
    print("=" * 64)

    print("""
Module 01: Reason About a Breach with First Principles

This lab has no tooling — only a documented breach and your analysis.
Your deliverable is breach-analysis.md.

──────────────────────────────────────────────────────────────
BREACH ANALYSIS TEMPLATE
──────────────────────────────────────────────────────────────

## Breach: [Name / CVE / Incident]
Source: [URL to post-mortem / CISA KEV / NVD]

### 1. Three-sentence summary
What was accessed:
How it happened:
What control failed:

### 2. CIA triad mapping
| Property       | Violated? | How                          |
|----------------|-----------|------------------------------|
| Confidentiality | Yes/No   | [what data was exposed]      |
| Integrity       | Yes/No   | [what was modified/replaced] |
| Availability    | Yes/No   | [what was disrupted]         |

### 3. Failed controls
| Control       | Principle (least-priv / defense-in-depth / etc.) |
|---------------|--------------------------------------------------|
| [Control 1]   | [Principle]                                      |
| [Control 2]   | [Principle]                                      |

### 4. Two controls that would have broken the chain
1. [Control] → protects [CIA property] via [principle]
2. [Control] → protects [CIA property] via [principle]

### 5. AI reconciliation
Ask a model to produce its own CIA/principle mapping of the same breach.
Paste its output here, then annotate where it disagrees with you and
why you kept or changed your answer.
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
        (r"cia|confidential|integrity|availab",  "CIA triad addressed"),
        (r"least.priv|defense.in.depth|princip",  "Security principle named"),
        (r"control|mitigation|patch|fix",          "Controls identified"),
        (r"cve|breach|incident|vulnerabilit",       "Specific breach referenced"),
        (r"ai|model|claude|gpt|gemini",             "AI reconciliation step done"),
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
        candidates = [Path("breach-analysis.md")] + list(Path(".").glob("*.md"))
        for p in candidates:
            if p.exists() and "breach" in p.name.lower():
                sys.exit(check_analysis(p))
        print("No breach-analysis.md found in current directory.")
        sys.exit(1)

    print_guide()
    entries = fetch_kev(5)
    print_kev_samples(entries)

    print(DIVIDER)
    print("When done:")
    print("  python3 guide.py --check   # validate your breach-analysis.md")
    print(DIVIDER + "\n")


if __name__ == "__main__":
    main()
