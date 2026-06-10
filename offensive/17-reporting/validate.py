#!/usr/bin/env python3
"""
Reporting lab — report validator and reference checker.

Validates a completed engagement report against required structural elements,
and checks that public report references are reachable.

Usage:
    python3 validate.py                          # demo: validate the template
    python3 validate.py engagement-report.md     # validate your report

A valid report must have:
  - Executive Summary
  - ≥1 Technical Finding with Severity, CVSS, Reproduction Steps, and Remediation
  - Findings Summary table
  - Remediation Roadmap
"""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DIVIDER = "─" * 64


def check_section(text: str, pattern: str, label: str) -> bool:
    found = bool(re.search(pattern, text, re.IGNORECASE))
    status = "✓" if found else "✗"
    print(f"  {status}  {label}")
    return found


def validate_report(path: Path) -> int:
    text = path.read_text(errors="replace")
    print(f"\n[Report] Validating: {path.name}")
    print()

    checks = [
        (r"executive summary",                "Executive Summary section"),
        (r"scope.*methodology|methodology",   "Scope and Methodology"),
        (r"findings summary",                  "Findings Summary table"),
        (r"\|\s*(critical|high|medium|low)",  "Severity in findings table"),
        (r"cvss",                              "CVSS score referenced"),
        (r"cwe",                               "CWE referenced"),
        (r"reproduction|steps to reproduce",   "Reproduction steps"),
        (r"remediation",                       "Remediation section"),
        (r"impact",                            "Impact section per finding"),
        (r"authorization|authoris",            "Authorization statement"),
        (r"appendix|reference",               "Appendix / References"),
    ]

    passed = sum(check_section(text, pat, label) for pat, label in checks)
    total = len(checks)

    print(f"\n  Score: {passed}/{total}")
    if passed == total:
        print("  ✓ Report passes all structural checks")
        return 0
    else:
        missing = total - passed
        print(f"  ✗ {missing} section(s) missing — see ✗ marks above")
        return 1


def demo() -> int:
    print("=" * 64)
    print("Penetration Test Reporting — Lab Validator")
    print("=" * 64)

    # ── 1: Validate the template ──────────────────────────────────────────
    template = DATA_DIR / "report-template.md"
    validate_report(template)

    # ── 2: Public report references ───────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("[References] Public penetration test reports to model")
    print()
    print("  The public reports collection is at:")
    print("  https://github.com/juliocesarfort/public-pentesting-reports")
    print()
    print("  Recommended reading (3 well-regarded public reports):")
    refs = [
        ("Bitwarden — Password Manager Security Audit (Cure53)",   "https://cure53.de/pentest-report_bitwarden.pdf"),
        ("Public pentest reports collection (GitHub index)",       "https://github.com/juliocesarfort/public-pentesting-reports"),
        ("Cure53 publications index (all public audits)",          "https://cure53.de/#publications"),
    ]
    for label, url in refs:
        try:
            with urllib.request.urlopen(url, timeout=6) as r:
                status = r.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as e:
            status = f"ERR: {e}"
        print(f"  {'✓' if status == 200 else '⚠'} [{status}] {label}")
        print(f"           {url}")
        print()

    # ── 3: Report writing tips ────────────────────────────────────────────
    print(DIVIDER)
    print("[Tips] Common report writing mistakes")
    print()
    mistakes = [
        ("Jargon in exec summary", "Replace 'SSRF via the /api/fetch endpoint' with 'An attacker could make our server fetch any internal URL, including AWS credentials'"),
        ("CVSS without context",   "Add: 'This is rated 9.8 but requires no prior access — an external attacker can exploit it directly'"),
        ("Vague remediation",      "Replace 'patch the system' with 'upgrade to Flask 3.0.3 or later; add URL allow-list to /api/fetch'"),
        ("Missing evidence",       "Every exploited finding needs a screenshot or terminal dump showing the impact (redact credentials)"),
        ("Raw CVSS prioritization","Justify the order: 'We prioritise F-001 over F-002 despite equal CVSS because F-001 is in CISA KEV with active exploitation'"),
    ]
    for mistake, fix in mistakes:
        print(f"  ✗ {mistake}")
        print(f"    → {fix}")
        print()

    print(f"{'=' * 64}")
    print("Report template in: data/report-template.md")
    print("Validate your report: python3 validate.py engagement-report.md")
    print(f"{'=' * 64}\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(validate_report(Path(sys.argv[1])))
    sys.exit(demo())
