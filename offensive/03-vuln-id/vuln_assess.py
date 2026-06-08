#!/usr/bin/env python3
"""Meridian Financial — vulnerability assessment workflow.

Takes service versions (from module 02 scan output) and walks the
full CVE research chain:
  CVE → CWE (weakness class) → CVSS score → KEV status → PoC availability

This is the research methodology used in professional penetration testing
and vulnerability management. The key insight: CVSS tells you severity;
KEV tells you urgency. A medium-CVSS CVE in KEV outranks a critical-CVSS
CVE that's never been exploited.

Bundled data covers the three CVEs most relevant to the recon output
from module 01:
  - CVE-2021-44228 (Log4Shell) — the canonical teaching example
  - CVE-2023-44487 (HTTP/2 Rapid Reset) — affects nginx on the victim
  - CVE-2024-21762 (FortiGate RCE) — from vpn.meridian-financial.com

Usage:
    python3 vuln_assess.py            # demo mode — full assessment
    python3 vuln_assess.py --report   # also write vuln-assessment.md
    python3 vuln_assess.py --live CVE-2021-44228  # query NVD API live
"""
from __future__ import annotations

import json
import sys
import textwrap
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DIVIDER  = "─" * 64


def wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=72, initial_indent=prefix,
                         subsequent_indent=prefix)


CWE_NAMES = {
    "CWE-502": "Deserialization of Untrusted Data",
    "CWE-400": "Uncontrolled Resource Consumption",
    "CWE-787": "Out-of-bounds Write",
    "CWE-89":  "SQL Injection",
    "CWE-79":  "Cross-site Scripting",
    "CWE-287": "Improper Authentication",
    "CWE-22":  "Path Traversal",
}

SEVERITY_COLORS = {
    "CRITICAL": "⛔",
    "HIGH":     "🔴",
    "MEDIUM":   "🟡",
    "LOW":      "🟢",
}


def load_kev(kev_data: dict) -> set[str]:
    return {v["cveID"] for v in kev_data.get("vulnerabilities", [])}


def get_kev_entry(kev_data: dict, cve_id: str) -> dict | None:
    for v in kev_data.get("vulnerabilities", []):
        if v["cveID"] == cve_id:
            return v
    return None


def assess_cve(cve: dict, kev_ids: set[str], kev_data: dict) -> dict:
    cve_id   = cve["id"]
    desc     = cve["descriptions"][0]["value"]
    metrics  = cve["metrics"]["cvssMetricV31"][0]["cvssData"]
    score    = metrics["baseScore"]
    severity = metrics["baseSeverity"]
    vector   = metrics["vectorString"]
    cwe      = cve["weaknesses"][0]["description"][0]["value"]
    in_kev   = cve_id in kev_ids
    kev_entry = get_kev_entry(kev_data, cve_id) if in_kev else None

    # Risk priority: KEV + CRITICAL = P0; KEV alone = P1; CRITICAL alone = P2; rest = P3
    if in_kev and score >= 9.0:
        priority = "P0 — EXPLOIT NOW"
    elif in_kev:
        priority = "P1 — EXPLOIT SOON (KEV)"
    elif score >= 9.0:
        priority = "P2 — HIGH (no KEV confirmation)"
    elif score >= 7.0:
        priority = "P3 — MEDIUM-HIGH"
    else:
        priority = "P4 — LOWER"

    return {
        "cve_id": cve_id,
        "desc": desc,
        "score": score,
        "severity": severity,
        "vector": vector,
        "cwe": cwe,
        "cwe_name": CWE_NAMES.get(cwe, "Unknown weakness"),
        "in_kev": in_kev,
        "kev_entry": kev_entry,
        "priority": priority,
        "patch": cve.get("patch_available", False),
        "fix": cve.get("fix_version", "Unknown"),
        "products": cve.get("affected_products", []),
    }


def print_cve_assessment(a: dict) -> None:
    sev_icon = SEVERITY_COLORS.get(a["severity"], "•")
    kev_flag = "★ IN CISA KEV" if a["in_kev"] else "  not in KEV"
    print(f"\n  {sev_icon} {a['cve_id']}  CVSS {a['score']} ({a['severity']})  {kev_flag}")
    print(f"     Priority: {a['priority']}")
    print(f"     CWE:      {a['cwe']} — {a['cwe_name']}")
    print(f"     Vector:   {a['vector']}")
    print()
    print(wrap(a["desc"], indent=5))
    print()
    if a["products"]:
        print(f"     Affected: {'; '.join(a['products'][:2])}")
    print(f"     Fix:      {a['fix']}")
    if a["in_kev"] and a["kev_entry"]:
        ke = a["kev_entry"]
        print(f"     KEV due:  {ke.get('dueDate','?')}  ({ke.get('notes','')})")


def demo(write_report: bool = False) -> int:
    nvd_cves = json.loads((DATA_DIR / "nvd_cves.json").read_text())
    kev_data = json.loads((DATA_DIR / "kev.json").read_text())
    scan_in  = json.loads((DATA_DIR / "scan_input.json").read_text())
    kev_ids  = load_kev(kev_data)

    print("=" * 64)
    print("Meridian Financial — Vulnerability Assessment")
    print(f"CVE sources: NVD (bundled) | KEV catalog v{kev_data['catalogVersion']}")
    print("=" * 64)

    # Step 1: Service inventory from scan
    print(f"\n[Step 1] Service inventory (from module 02 scan output)")
    print()
    print(f"  {'PORT':>6}  {'SERVICE':8s}  {'PRODUCT + VERSION'}")
    print(f"  {'─'*6}  {'─'*8}  {'─'*35}")
    for s in scan_in:
        print(f"  {s['port']:>6}  {s['service']:8s}  {s['product']} {s['version']}")

    # Step 2: CVE research chain
    print(f"\n{DIVIDER}")
    print(f"[Step 2] CVE research — NVD lookup + KEV check")

    assessments = []
    for cve in nvd_cves:
        a = assess_cve(cve, kev_ids, kev_data)
        assessments.append(a)
        print_cve_assessment(a)

    # Step 3: Risk prioritization
    print(f"\n{DIVIDER}")
    print(f"[Step 3] Risk prioritization — KEV over CVSS")
    print()
    sorted_a = sorted(assessments, key=lambda x: (
        0 if x["in_kev"] and x["score"] >= 9.0 else
        1 if x["in_kev"] else
        2 if x["score"] >= 9.0 else 3
    ))
    print(f"  {'Priority':25s}  {'CVE':18s}  CVSS  KEV")
    print(f"  {'─'*25}  {'─'*18}  {'─'*4}  {'─'*3}")
    for a in sorted_a:
        kev_mark = "yes" if a["in_kev"] else "no"
        print(f"  {a['priority'][:25]:25s}  {a['cve_id']:18s}  {a['score']:4.1f}  {kev_mark}")

    # Step 4: Searchsploit / PoC availability
    print(f"\n{DIVIDER}")
    print(f"[Step 4] PoC / Exploit-DB availability")
    print(f"""
  searchsploit "log4j":
    Apache Log4j 2 - Remote Code Execution (Apache Solr)  | exploits/java/webapps/50592.py
    Apache Log4j 2.14.1 - Information Disclosure          | exploits/java/webapps/50461.txt
    → PoC available, weaponized exploits exist in Metasploit (exploit/multi/misc/log4shell_header_injection)

  searchsploit "nginx 1.24":
    No results found.
    → CVE-2023-44487 is a DoS; tooling exists but Metasploit module not yet merged.

  searchsploit "FortiGate 7.4":
    Fortinet FortiOS 7.4.x - CVE-2024-21762 RCE           | exploits/python/remote/54916.py
    → PoC published; nation-state actors used it before patch release.
""")

    # Step 5: Verdict
    print("=" * 64)
    print("Risk verdict (one line per CVE)")
    print("=" * 64)
    print(f"""
  CVE-2021-44228 (Log4Shell): CVSS 10.0 CRITICAL, IN KEV, weaponized
    Metasploit module exists. Exploit if Log4j 2.0-2.14.x is present —
    confirm by querying /api/ endpoint that logs user input.
    Priority: P0.

  CVE-2024-21762 (FortiGate): CVSS 9.8 CRITICAL, IN KEV, nation-state
    exploitation confirmed. vpn.meridian-financial.com runs FortiGate
    SSL-VPN — confirm version, then patch or disable VPN immediately.
    Priority: P0.

  CVE-2023-44487 (Rapid Reset): CVSS 7.5 HIGH, IN KEV, DoS only.
    Affects nginx 1.24.0 (victim). Patch to 1.25.3. Lower urgency
    vs. RCE above but still requires patching.
    Priority: P1.

  Key insight: two P0 CVEs rank ahead because they're in CISA KEV
  (actively exploited in the wild). A CVSS 7.5 in KEV ranks
  above a CVSS 9.8 with no KEV entry — because exploitation is
  confirmed, not theoretical.
""")

    if write_report:
        _write_report(assessments)

    return 0


def _write_report(assessments: list[dict]) -> None:
    out = Path("vuln-assessment.md")
    lines = [
        "# Vulnerability Assessment — Meridian Financial",
        f"Date: {date.today().isoformat()}",
        "",
        "## Scope",
        "Target: meridian-financial.com (module 01 recon output).",
        "Services assessed: nginx 1.24.0, FortiGate SSL-VPN, Log4j2.",
        "",
        "## CVE → CWE → CVSS → KEV → PoC chain",
        "",
    ]
    for a in assessments:
        lines += [
            f"### {a['cve_id']}  (CVSS {a['score']} {a['severity']})",
            f"- **CWE:** {a['cwe']} — {a['cwe_name']}",
            f"- **CVSS vector:** `{a['vector']}`",
            f"- **KEV:** {'YES — ' + a['kev_entry']['dateAdded'] if a['in_kev'] and a['kev_entry'] else 'No'}",
            f"- **Priority:** {a['priority']}",
            f"- **Fix:** {a['fix']}",
            "",
            f"  {a['desc'][:200]}",
            "",
        ]
    lines += [
        "## One-line risk verdict",
        "",
        "Patch CVE-2024-21762 (FortiGate) and CVE-2021-44228 (Log4Shell) immediately — "
        "both are in CISA KEV with confirmed exploitation. The DoS-only CVE-2023-44487 "
        "ranks third. CVSS alone is not a prioritisation signal; KEV is.",
    ]
    out.write_text("\n".join(lines))
    print(f"\n  [Report written to {out}]")


def live_query(cve_id: str) -> None:
    """Query the NVD API live — requires internet."""
    try:
        import urllib.request
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        vuln = data["vulnerabilities"][0]["cve"]
        desc = vuln["descriptions"][0]["value"]
        score = vuln["metrics"]["cvssMetricV31"][0]["cvssData"]["baseScore"]
        sev   = vuln["metrics"]["cvssMetricV31"][0]["cvssData"]["baseSeverity"]
        print(f"\n{cve_id}  CVSS {score} {sev}")
        print(wrap(desc, indent=2))
    except Exception as e:
        print(f"NVD API error: {e}")


if __name__ == "__main__":
    if "--live" in sys.argv:
        idx = sys.argv.index("--live")
        cve = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "CVE-2021-44228"
        live_query(cve)
        sys.exit(0)
    write_report = "--report" in sys.argv
    sys.exit(demo(write_report))
