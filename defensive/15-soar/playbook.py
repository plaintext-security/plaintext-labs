#!/usr/bin/env python3
"""Meridian Financial — SOAR response playbook.

This harness implements the four-stage SOAR pattern:
  1. Trigger    — an alert arrives from the SIEM/IDS
  2. Enrich     — look up IPs in threat intel; add context
  3. Triage     — AI-style scoring: score → route (escalate/suppress)
  4. Act        — open a case; gate containment on human approval

In production this pipeline runs in Shuffle, Tines, or a SOAR of your
choice. The Python implementation teaches the same pattern — and makes
the human-gate requirement explicit in code, not just in docs.

The triage step is rule-based here, but the *interface* matches what
you'd wire to an LLM: it receives context (alert + intel + metadata),
returns a score and reasoning, and the pipeline gates on the score.
The guardrail that matters is not the model — it is the human-approval
step before any containment action fires.

Usage:
    python3 playbook.py            # demo mode — run all 3 test alerts
    python3 playbook.py --auto     # skip the human-gate pause (CI/testing)
    python3 playbook.py --export   # print the playbook as YAML workflow-as-code
"""
from __future__ import annotations

import json
import sys
import textwrap
import time
from pathlib import Path

DATA_DIR   = Path(__file__).parent / "data"
ALERTS_FILE = DATA_DIR / "alerts.json"
INTEL_FILE  = DATA_DIR / "intel.json"

DIVIDER  = "─" * 64
WIDTH    = 72
AUTO_MODE = "--auto" in sys.argv


def wrap(text: str, indent: int = 2) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=WIDTH, initial_indent=prefix,
                         subsequent_indent=prefix)


# ── Step 1: Trigger ───────────────────────────────────────────────────────────

def step_trigger(alert: dict) -> dict:
    return alert


# ── Step 2: Enrich ────────────────────────────────────────────────────────────

def step_enrich(alert: dict, intel: dict) -> dict:
    enriched = dict(alert)
    enriched["intel"] = {}
    for ip_field in ("src_ip", "dst_ip"):
        ip = alert.get(ip_field)
        if ip and ip in intel:
            enriched["intel"][ip] = intel[ip]
    # Mark internal IPs as clean if no intel entry
    enriched["intel"].setdefault(alert["src_ip"], {"verdict": "unknown"})
    enriched["intel"].setdefault(alert["dst_ip"], {"verdict": "unknown"})
    return enriched


# ── Step 3: Triage (AI-style scoring) ────────────────────────────────────────

def step_triage(enriched: dict) -> dict:
    """Score the alert 0–100; return score, reasoning, routing decision.

    This implements the same interface you'd expose to an LLM:
    - Input: structured alert + enrichment context
    - Output: numeric score, reasoning bullets, route (escalate/suppress)

    The difference from calling an LLM: the rules here are explicit and
    auditable. An LLM-based triage step must meet the same bar — every
    scoring factor must be inspectable and testable on ground-truth data.
    """
    score = 0
    reasons: list[str] = []

    # Severity base score
    base = {"critical": 40, "high": 30, "medium": 15, "low": 5}.get(
        enriched.get("severity", "low"), 5)
    score += base
    reasons.append(f"Severity '{enriched['severity']}' → +{base}")

    # Threat-intel: known-bad destination
    dst_intel = enriched["intel"].get(enriched.get("dst_ip", ""), {})
    if dst_intel.get("verdict") == "malicious":
        conf = dst_intel.get("confidence", 50)
        boost = int(conf * 0.4)
        score += boost
        reasons.append(
            f"Dst {enriched['dst_ip']} is known-{dst_intel['malware']} "
            f"(confidence {conf}%) → +{boost}"
        )
    elif dst_intel.get("verdict") == "clean":
        score -= 20
        reasons.append(f"Dst {enriched['dst_ip']} on allowlist → -20")

    # Threat-intel: known-bad source
    src_intel = enriched["intel"].get(enriched.get("src_ip", ""), {})
    if src_intel.get("verdict") == "malicious":
        score += 20
        reasons.append(f"Src {enriched['src_ip']} is known-bad → +20")

    # Lateral movement / brute success amplifier
    if enriched.get("additional", {}).get("success_after_failures"):
        score += 25
        reasons.append("Brute-force success after failures → +25 (lateral movement indicator)")

    # Parent process chain amplifier (endpoint context)
    parent = enriched.get("additional", {}).get("sysmon_parent", "")
    if "WINWORD" in parent or "EXCEL" in parent:
        score += 15
        reasons.append(f"Office app in process chain → +15 (macro delivery indicator)")
    elif "chrome" in parent.lower():
        score -= 5
        reasons.append(f"Browser parent process → -5 (likely user-driven download)")

    score = max(0, min(100, score))
    route = "ESCALATE" if score >= 50 else "SUPPRESS"
    return {"score": score, "reasons": reasons, "route": route}


# ── Step 4: Act ───────────────────────────────────────────────────────────────

def step_open_case(enriched: dict, triage: dict) -> dict:
    case = {
        "title": f"[AUTO] {enriched['signature']} — {enriched['host']}",
        "severity": 3 if enriched["severity"] == "critical" else
                    2 if enriched["severity"] == "high" else 1,
        "tags": ["auto-generated", "soar", enriched["source"].lower()],
        "description": (
            f"Alert {enriched['id']} from {enriched['source']}.\n"
            f"Triage score: {triage['score']}/100 → {triage['route']}\n"
            f"Src: {enriched['src_ip']}  Dst: {enriched['dst_ip']}:{enriched['dst_port']}\n"
        ),
        "observables": [
            {"dataType": "ip", "data": enriched["src_ip"], "tags": ["source"]},
            {"dataType": "ip", "data": enriched["dst_ip"], "tags": ["destination"]},
        ],
    }
    return case


def step_human_gate(alert: dict, triage: dict, auto: bool = False) -> bool:
    """Containment actions MUST be approved by a human.

    This is the non-negotiable guardrail: no automated action isolates
    a host or blocks a network path without a person reviewing the
    evidence and approving. The AI scores; the human decides.
    """
    if triage["score"] < 70:
        return False  # Below threshold — don't even prompt
    if auto:
        print("  [AUTO MODE] Human gate bypassed (--auto flag). "
              "In production this gate must require explicit approval.")
        return True
    print(f"\n  ⚠ HUMAN APPROVAL REQUIRED — containment action pending")
    print(f"  Host: {alert['host']}  Score: {triage['score']}/100")
    print(f"  Action: isolate {alert['src_ip']} from network + block {alert['dst_ip']}")
    resp = input("  Approve containment? [y/N] ").strip().lower()
    return resp == "y"


def step_contain(alert: dict, approved: bool) -> list[str]:
    """Simulate containment actions (no live network/host calls)."""
    if not approved:
        return []
    actions = [
        f"FIREWALL BLOCK: deny src any dst {alert['dst_ip']}/32 port {alert['dst_port']}",
        f"EDR ISOLATE: network-isolate {alert['src_ip']} (host {alert['host']})",
        f"AD DISABLE: disable account {alert['user'].split(',')[0]}",
    ]
    return actions


# ── YAML export ───────────────────────────────────────────────────────────────

PLAYBOOK_YAML = """\
# Meridian Financial — SOAR Alert Response Playbook
# Workflow-as-code: commit this alongside your detection rules.
# Import into Shuffle, Tines, or any SOAR that supports YAML workflows.

name: "Alert → Enrich → Triage → Human Gate → Contain"
version: "1.0.0"
trigger:
  type: webhook
  source: [SIEM, IDS]
  filter:
    severity: [high, critical]

steps:
  - id: enrich
    name: "Enrich — threat intel lookup"
    action: http.get
    params:
      url: "https://threatfox-api.abuse.ch/api/v1/"
      body: {query: "search_ioc", search_term: "{{alert.dst_ip}}"}
    output: intel_result

  - id: triage
    name: "Triage — AI scoring (rule-based + optional LLM)"
    action: script.python
    params:
      code: |
        score = base_score(alert.severity)
        if intel_result.verdict == "malicious":
            score += int(intel_result.confidence * 0.4)
        if alert.additional.get("success_after_failures"):
            score += 25
        route = "ESCALATE" if score >= 50 else "SUPPRESS"
    output: triage_result

  - id: open_case
    name: "Open TheHive case"
    condition: "triage_result.route == ESCALATE"
    action: thehive.create_case
    params:
      title: "{{alert.signature}} — {{alert.host}}"
      severity: "{{alert.severity}}"
      observables:
        - {type: ip, value: "{{alert.src_ip}}"}
        - {type: ip, value: "{{alert.dst_ip}}"}

  - id: human_gate
    name: "Human approval — REQUIRED before any containment"
    condition: "triage_result.score >= 70"
    action: approval.request
    params:
      message: |
        Alert {{alert.id}} scored {{triage_result.score}}/100.
        Proposed actions:
          - Block {{alert.dst_ip}}/32 at perimeter
          - Network-isolate {{alert.host}} ({{alert.src_ip}})
        Approve?
      timeout_minutes: 30
      on_timeout: escalate_to_on_call

  - id: contain
    name: "Containment — gated on human approval"
    condition: "human_gate.approved == true"
    action: sequence
    steps:
      - action: firewall.block
        params: {dst_ip: "{{alert.dst_ip}}", dst_port: "{{alert.dst_port}}"}
      - action: edr.isolate
        params: {host: "{{alert.host}}", ip: "{{alert.src_ip}}"}
      - action: ad.disable_account
        params: {user: "{{alert.user}}"}
"""


# ── Demo ──────────────────────────────────────────────────────────────────────

def run_alert(alert: dict, intel: dict) -> None:
    print(f"\n{'=' * 64}")
    print(f"  Processing {alert['id']} — {alert['signature'][:55]}")
    print(f"{'=' * 64}")

    # Step 1 — Trigger
    print(f"\n[1] TRIGGER  {alert['ts']}")
    print(f"    Source: {alert['source']}  Severity: {alert['severity'].upper()}")
    print(f"    {alert['src_ip']} → {alert['dst_ip']}:{alert['dst_port']}  host: {alert['host']}")

    # Step 2 — Enrich
    enriched = step_enrich(step_trigger(alert), intel)
    print(f"\n[2] ENRICH   threat-intel lookup")
    for ip, data in enriched["intel"].items():
        verdict = data.get("verdict", "unknown")
        malware = data.get("malware") or ""
        conf    = data.get("confidence", "?")
        symbol  = {"malicious": "✗", "clean": "✓", "unknown": "?"}.get(verdict, "?")
        print(f"    {symbol} {ip:18s}  {verdict.upper():10s}  {malware}  {conf}%"
              if malware else f"    {symbol} {ip:18s}  {verdict.upper()}")

    # Step 3 — Triage
    triage = step_triage(enriched)
    print(f"\n[3] TRIAGE   score: {triage['score']}/100  →  {triage['route']}")
    for r in triage["reasons"]:
        print(f"    • {r}")

    # Step 4a — Open case if escalating
    if triage["route"] == "ESCALATE":
        case = step_open_case(enriched, triage)
        print(f"\n[4] CASE     TheHive case opened → severity {case['severity']}")
        print(f"    Title: {case['title'][:60]}")

        # Step 4b — Human gate before containment
        approved = step_human_gate(alert, triage, auto=AUTO_MODE)
        if approved:
            actions = step_contain(alert, approved=True)
            print(f"\n[4] CONTAIN  Approved — {len(actions)} action(s) dispatched:")
            for a in actions:
                print(f"    ✓ {a}")
        else:
            print(f"\n[4] CONTAIN  Gate not approved — no automated containment taken.")
            print(f"    Case remains open for analyst review.")
    else:
        print(f"\n[4] SUPPRESS  Alert suppressed (score < 50). Case not opened.")
        print(f"    This alert is auto-closed; analyst review optional.")


def demo() -> int:
    alerts = json.loads(ALERTS_FILE.read_text())
    intel  = json.loads(INTEL_FILE.read_text())

    print("=" * 64)
    print("Meridian Financial SOAR Playbook")
    print(f"Processing {len(alerts)} incoming alerts")
    print("=" * 64)
    print(f"\nPlaybook: Trigger → Enrich → Triage → [Human Gate] → Contain")
    print(f"Human-gate threshold: score ≥ 70/100")
    print(wrap(
        "\nKey principle: the AI scores and routes; a human must approve "
        "before any host is isolated or any network path is blocked. "
        "This is not an optional guardrail — it is the contract.", indent=0
    ))

    for alert in alerts:
        run_alert(alert, intel)

    print(f"\n{'=' * 64}")
    print("Run summary")
    print(f"{'=' * 64}")
    print("""
  ALERT-001 (C2 download + macro chain):  ESCALATE  score=85  case opened
  ALERT-002 (Chrome download, CDN dst):   SUPPRESS  score=10  no case
  ALERT-003 (SSH brute + success):        ESCALATE  score=90  case opened

  Note: ALERT-001 and ALERT-003 both score ≥ 70 but containment is
  only dispatched with human approval. In demo mode (--auto) the gate
  is bypassed; in production, approval must come from a real human.
""")
    return 0


if __name__ == "__main__":
    if "--export" in sys.argv:
        print(PLAYBOOK_YAML)
        sys.exit(0)
    sys.exit(demo())
