#!/usr/bin/env python3
"""
eval_detections.py — Score AD Sigma-style detections against a HELD-OUT, labelled corpus
and print a per-rule scorecard (precision / recall / FP-rate). Doubles as a CI regression
gate: with --gate, the process exits non-zero if ANY rule misses an attack (recall < 1.0)
or fires on a benign near-miss (any false positive).

WHY a held-out corpus. The `make demo` set is the data the rules were WRITTEN against — of
course they fire on it. AD telemetry drowns the signal in benign noise: thousands of 4769s,
legitimate 4662 replication, normal NTLM service logons. "The rule fires on the attack EVTX"
is coverage, not effectiveness. Effectiveness is: does it still catch the attack AND stay
quiet on the benign near-misses it has never been tuned on? This corpus is exactly those
near-misses — the AES ticket for the same SPN, the DC$ machine replicating, the Kerberos
file-share logon — the events that turn a coverage-green rule into an alert-fatigue generator.

OFFLINE / DETERMINISTIC. There is no live DC and no binary EVTX parsing here; the corpus is
JSON-shaped events and the detection logic is the same Sigma semantics evtx_demo.py applies,
expressed as a RULESET so we can score the GOOD ruleset against a deliberately TOO-BROAD
(regressed) one. There is NO grading machinery / receipt — Plaintext is an honor system.

Usage:
  python3 scripts/eval_detections.py --ruleset good
  python3 scripts/eval_detections.py --ruleset good --gate
  python3 scripts/eval_detections.py --ruleset regressed --gate   # demonstrates a RED gate
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "data", "heldout", "events.json")


def _is_machine(name: str) -> bool:
    return name.endswith("$")


# Replication extended-right GUIDs (DS-Replication-Get-Changes / -All / -In-Filtered-Set).
REPL_GUIDS = (
    "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2",
    "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2",
    "1131f6ae-9c07-11d1-f79f-00c04fc2dcd2",
    "89e95b76-444d-4c62-991a-0facbeda640c",
)


def _repl_right(props: str) -> bool:
    return any(g in props for g in REPL_GUIDS)


# --- GOOD detection logic: tight rules that key on the real discriminator + exclusions. -----
def good(e: dict, rule: str) -> bool:
    s, d = e.get("System", {}), e.get("EventData", {})
    if rule == "kerberoast":
        return (
            s.get("EventID") == 4769
            and d.get("TicketEncryptionType") == "0x17"        # RC4 is the discriminator
            and not _is_machine(d.get("ServiceName", ""))      # exclude machine-account tickets
        )
    if rule == "dcsync":
        return (
            s.get("EventID") == 4662
            and _repl_right(d.get("Properties", ""))           # the replication right, not any 4662
            and not _is_machine(d.get("SubjectUserName", ""))  # exclude DC-to-DC replication
        )
    if rule == "asrep":
        return (
            s.get("EventID") == 4768
            and d.get("PreAuthType") == "0"
            and d.get("Status") == "0x0"
            and not _is_machine(d.get("TargetUserName", ""))   # exclude machine accounts
        )
    if rule == "pth":
        return (
            s.get("EventID") == 4624
            and d.get("LogonType") == "3"
            and d.get("AuthenticationPackageName") == "NTLM"   # NTLM, not Kerberos
            and not _is_machine(d.get("TargetUserName", ""))   # exclude machine accounts
            and d.get("TargetUserName") != "ANONYMOUS LOGON"
            and d.get("IpAddress") not in ("127.0.0.1", "::1", "-")
        )
    return False


# --- REGRESSED detection logic: a plausible "broaden it / I dropped the exclusion" edit. -----
# Each rule still CATCHES every attack (recall stays 1.0) but loses its benign exclusion and
# so FIRES on the near-miss benign events -> false positives. This is how a detection rots into
# noise: coverage looks fine, effectiveness collapses. The gate must catch it.
def regressed(e: dict, rule: str) -> bool:
    s, d = e.get("System", {}), e.get("EventData", {})
    if rule == "kerberoast":
        # Dropped the machine-account exclusion: now any RC4 4769 fires (incl. machine$ tickets).
        return s.get("EventID") == 4769 and d.get("TicketEncryptionType") == "0x17"
    if rule == "dcsync":
        # Dropped the DC-account exclusion: now legitimate DC-to-DC replication fires.
        return s.get("EventID") == 4662 and _repl_right(d.get("Properties", ""))
    if rule == "asrep":
        # Dropped the machine-account exclusion: now PreAuthType=0 for any principal fires.
        return s.get("EventID") == 4768 and d.get("PreAuthType") == "0" and d.get("Status") == "0x0"
    if rule == "pth":
        # Dropped the machine-account exclusion: now NTLM Type 3 to machine$ accounts fires.
        return (
            s.get("EventID") == 4624
            and d.get("LogonType") == "3"
            and d.get("AuthenticationPackageName") == "NTLM"
        )
    return False


RULESETS = {"good": good, "regressed": regressed}
RULES = ["kerberoast", "dcsync", "asrep", "pth"]


def score(events, fire) -> dict:
    by_rule = {}
    for r in RULES:
        items = [e for e in events if e["rule"] == r]
        tp = fp = tn = fn = 0
        missed, falsefire = [], []
        for e in items:
            fired = fire(e, r)
            attack = e["label"] == "attack"
            if attack and fired:
                tp += 1
            elif attack and not fired:
                fn += 1
                missed.append(e["id"])
            elif not attack and fired:
                fp += 1
                falsefire.append(e["id"])
            else:
                tn += 1
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 1.0
        fp_rate = fp / (fp + tn) if (fp + tn) else 0.0
        by_rule[r] = {
            "attacks": tp + fn, "benign": fp + tn,
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": precision, "recall": recall, "fp_rate": fp_rate,
            "missed": missed, "false_fires": falsefire,
        }
    return by_rule


def print_scorecard(ruleset, by_rule):
    print(f"\n=== AD detection scorecard — ruleset '{ruleset}' (HELD-OUT corpus) ===")
    print(f"{'rule':<12} {'attacks':>7} {'benign':>6} {'recall':>7} {'precision':>10} {'FP-rate':>8}   notes")
    for r in RULES:
        m = by_rule[r]
        note = ""
        if m["missed"]:
            note = f"MISSED ATTACK: {', '.join(m['missed'])}"
        elif m["false_fires"]:
            note = f"FALSE POSITIVE on benign: {', '.join(m['false_fires'])}"
        print(f"{r:<12} {m['attacks']:>7} {m['benign']:>6} "
              f"{m['recall']:>6.0%} {m['precision']:>10.0%} {m['fp_rate']:>8.0%}   {note}")
    print()


def gate(by_rule) -> bool:
    """Pass only if EVERY rule catches all attacks (recall == 1.0) and fires on NO benign event.
    Fails CLOSED. This is the regression gate: a rule that regressed into noise turns it red."""
    ok = True
    for r in RULES:
        m = by_rule[r]
        if m["recall"] < 1.0:
            print(f"GATE FAIL [{r}]: missed attack(s) {m['missed']} (recall {m['recall']:.0%} < 100%).",
                  file=sys.stderr)
            ok = False
        if m["fp"] > 0:
            print(f"GATE FAIL [{r}]: fired on benign event(s) {m['false_fires']} (FP-rate {m['fp_rate']:.0%}).",
                  file=sys.stderr)
            ok = False
    print("REGRESSION GATE [PASS]: every rule caught all attacks and stayed quiet on every benign near-miss."
          if ok else "REGRESSION GATE [FAIL]: a rule regressed — see failures above.")
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ruleset", choices=list(RULESETS), default="good",
                   help="which detection logic to score (good = tight rules, regressed = too-broad)")
    p.add_argument("--corpus", default=CORPUS, help="held-out labelled events")
    p.add_argument("--gate", action="store_true",
                   help="exit non-zero on any missed attack or any benign false positive")
    args = p.parse_args()

    with open(args.corpus) as f:
        events = json.load(f)

    by_rule = score(events, RULESETS[args.ruleset])
    print_scorecard(args.ruleset, by_rule)

    if args.gate and not gate(by_rule):
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
