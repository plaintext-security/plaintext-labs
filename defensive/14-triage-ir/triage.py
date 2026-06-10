#!/usr/bin/env python3
"""Meridian Financial — Incident triage and IR walkthrough.

This harness presents the Meridian INC-2024-0315-001 incident pack and
walks through the NIST SP 800-61 lifecycle:
  1. Detection & Analysis  — triage to a true/false-positive verdict
  2. Containment           — minimum action to stop active harm
  3. Eradication           — remove every persistence artifact
  4. Recovery              — criteria before returning to production
  5. Post-Incident Review  — root cause and improvement action

In a production SOC this workflow runs in TheHive, Jira, or similar.
Here, the harness prints the structured incident pack so you work
through the same reasoning steps — question, evidence, decision.

Usage:
    python3 triage.py          # demo mode — full guided walkthrough
    python3 triage.py --pack   # dump the raw incident pack as JSON
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "incident_pack.json"
DIVIDER = "─" * 64
WIDTH = 72


def wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=WIDTH, initial_indent=prefix,
                         subsequent_indent=prefix)


def print_section(title: str) -> None:
    print(f"\n{'=' * 64}")
    print(f"  {title}")
    print(f"{'=' * 64}")


def demo(pack: dict) -> int:
    print("=" * 64)
    print("Meridian Financial — Incident Triage")
    print(f"Incident: {pack['incident_id']}  |  {pack['title']}")
    print("=" * 64)

    # ── Initial alert ─────────────────────────────────────────────────────────
    print_section("PHASE 0 — Initial alert")
    alert = pack["initial_alert"]
    print(f"\n  Source:    {alert['source']}  ({alert['ts']})")
    print(f"  Signature: {alert['signature']}")
    print(f"  Traffic:   {alert['src_ip']} → {alert['dst_ip']}")
    print(f"  Severity:  {alert['severity'].upper()}")
    print()
    print(wrap("First question every analyst asks: is this a true positive "
               "or a false positive? An IDS signature for 'PE download HTTP' "
               "fires on any unencrypted executable download — Windows Update, "
               "installers, and malware alike. What additional evidence do you "
               "pull to decide?"))

    # ── Observables ───────────────────────────────────────────────────────────
    print_section("PHASE 1 — Detection & Analysis: observables")
    print()
    for obs in pack["observables"]:
        print(f"  [{obs['type'].upper():7s}]  {obs['value']}")
        print(f"           ↳ {obs['note']}")
    print()

    # ── Threat intel enrichment ───────────────────────────────────────────────
    print(DIVIDER)
    print("  Threat-intel enrichment (ThreatFox / MalwareBazaar):")
    print()
    for ioc, intel in pack["threat_intel"].items():
        verdict_label = "✗ MALICIOUS" if intel["verdict"] == "malicious" else "? UNKNOWN"
        print(f"  {verdict_label}  {ioc[:52]}")
        print(f"             {intel['malware']}  (confidence {intel['confidence']}%)"
              f"  — {intel['source']}")
    print()
    print(wrap("Threat intel confirms 185.220.101.47 is a known Cobalt Strike "
               "C2. Combined with the Sysmon process chain, this is a true "
               "positive. Severity: CRITICAL (active C2 implant with persistence "
               "on a Finance workstation)."))

    # ── Timeline ──────────────────────────────────────────────────────────────
    print_section("PHASE 1 (continued) — Attack timeline")
    print()
    for entry in pack["timeline"]:
        print(f"  {entry['ts'][11:19]}Z  {entry['event']}")

    # ── Triage questions ──────────────────────────────────────────────────────
    print_section("PHASE 1 — Triage decision checklist")
    print()
    for q in pack["questions"]["triage"]:
        print(f"  □  {q}")

    # ── Containment ───────────────────────────────────────────────────────────
    print_section("PHASE 2 — Containment")
    print()
    print(wrap("NIST SP 800-61 containment: stop the bleeding without "
               "destroying forensics. The C2 implant is beaconing; every "
               "minute it's live is an opportunity for the attacker to "
               "exfiltrate more or pivot."))
    print()
    print("  Immediate actions (in order):")
    print("    1. Isolate WS-JSMITH from the network (VLAN quarantine or")
    print("       endpoint isolation via EDR — do NOT simply pull the cable,")
    print("       which may lose volatile memory state).")
    print("    2. Block 185.220.101.47/32 at the perimeter firewall.")
    print("    3. Preserve: acquire memory image + disk image before")
    print("       remediation (evidence for eradication verification).")
    print("    4. Rotate jsmith's Active Directory credentials immediately.")
    print("    5. Notify: legal, management per the IR policy.")
    print()
    print("  Do NOT:")
    print("    ✗ Reboot the machine — clears volatile memory / running artifacts.")
    print("    ✗ Run antivirus scans immediately — may destroy forensic evidence.")
    print("    ✗ Notify the user before isolation — attacker may be monitoring.")
    print()
    for q in pack["questions"]["contain"]:
        print(f"  □  {q}")

    # ── Eradication ───────────────────────────────────────────────────────────
    print_section("PHASE 3 — Eradication")
    print()
    print("  Persistence artifacts to remove (all must be cleared):")
    persistence = [o for o in pack["observables"]
                   if o["type"] in ("regkey", "task", "file")]
    for p in persistence:
        print(f"    • [{p['type'].upper():6s}]  {p['value']}")
    print()
    print(wrap("Eradication is not just deletion. Confirm each artifact is "
               "gone via an independent query — not by trusting the same "
               "tool that removed it. Check for additional scheduled tasks "
               "or Run keys the attacker may have added that aren't in the "
               "initial evidence (an implant often installs redundant "
               "persistence)."))
    print()
    for q in pack["questions"]["eradicate"]:
        print(f"  □  {q}")

    # ── Recovery ──────────────────────────────────────────────────────────────
    print_section("PHASE 4 — Recovery")
    print()
    print("  Before returning WS-JSMITH to production:")
    print("    □  Full AV/EDR scan clean (post-eradication).")
    print("    □  Verify no scheduled tasks or Run keys remain for updater.exe.")
    print("    □  Confirm 185.220.101.47 blocked and no outbound traffic to it.")
    print("    □  Reset jsmith's credentials and confirm MFA is enrolled.")
    print("    □  Re-image if full forensic confidence is required (cleanest).")
    print()
    for q in pack["questions"]["recover"]:
        print(f"  □  {q}")

    # ── Post-incident review ──────────────────────────────────────────────────
    print_section("PHASE 5 — Post-Incident Review")
    print()
    print(wrap("The post-incident review is where the investment compounds. "
               "Every incident either produces an improvement or it repeats."))
    print()
    print("  Findings:")
    print("    • Initial vector: phishing .docm with embedded macro.")
    print("    • Macro execution not blocked (no GPO to disable Office macros).")
    print("    • certutil used as LOLBin — not alerted on pre-existing rules.")
    print("    • C2 IP was known-bad in ThreatFox since 2023-11-01; no automated")
    print("      block was in place.")
    print()
    print("  Improvement actions (ranked):")
    print("    1. Deploy GPO to disable Office macros from the internet zone.")
    print("    2. Add certutil.exe with -urlcache to the SIEM correlation rules.")
    print("    3. Subscribe to abuse.ch ThreatFox feed and auto-block at firewall.")
    print("    4. Run phishing simulation for Finance team within 30 days.")
    print()
    for q in pack["questions"]["post_incident"]:
        print(f"  □  {q}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print_section("Incident summary")
    print(f"""
  Incident:  {pack['incident_id']}
  Verdict:   TRUE POSITIVE — CRITICAL
  Malware:   Cobalt Strike (CobaltStrike.Beacon via macro dropper)
  C2:        185.220.101.47  (known-bad since 2023-11-01)
  Scope:     1 host isolated (WS-JSMITH); SRV-01 brute force unrelated
  NIST phase reached: Recovery (eradication in progress)

  Deliverable: commit incident.md with the timeline, triage decision,
  all five-phase answers, and the improvement action you'd prioritise.
""")
    return 0


if __name__ == "__main__":
    pack = json.loads(DATA_FILE.read_text())
    if "--pack" in sys.argv:
        print(json.dumps(pack, indent=2))
        sys.exit(0)
    sys.exit(demo(pack))
