#!/usr/bin/env python3
"""Review gate for AI-drafted Sigma rules — fire them at a LABELLED corpus.

A clean read (and even `sigma convert`) passes a rule that is subtly wrong: a
field that doesn't exist in your telemetry, a modifier that's too broad, a
logsource that points at the wrong event class, or a hallucinated ATT&CK ID.
None of those raise an error. The only thing that never lies is *firing the rule
at ground truth* and *resolving every tag against the primary source*. This
harness does both, per rule:

  * MATCH the rule against the labelled corpus (each event has `_label` =
    malicious|benign and malicious events carry `_technique`).
  * MISS  — the rule's tagged technique has a known-bad sample in the corpus that
            the rule fails to catch  -> false negative (dangerous).
  * FALSE POSITIVE — the rule fires on a benign event.
  * TAG   — resolve every `attack.tNNNN[.NNN]` tag against the local ATT&CK ID
            list; an unresolvable tag is a fabricated/hallucinated technique.

Exit code is non-zero if ANY rule misfires, so this doubles as a CI review gate
(see `make review` / the lab's `review-gate.py` build step).

  usage:
    review.py --corpus corpus/corpus.jsonl --attack attack/attack_ids.txt \\
              ai-drafts/*.yml
"""
import argparse
import glob
import json
import sys

import yaml

# --- Sigma matching subset (shared semantics with module 08's detect.py) ----


def as_list(value):
    return value if isinstance(value, list) else [value]


def match_field(event_value, modifier, expected):
    if event_value is None:
        return False
    haystack = str(event_value).lower()
    for exp in as_list(expected):
        needle = str(exp).lower()
        if modifier is None and haystack == needle:
            return True
        if modifier == "contains" and needle in haystack:
            return True
        if modifier == "startswith" and haystack.startswith(needle):
            return True
        if modifier == "endswith" and haystack.endswith(needle):
            return True
    return False


def match_selection(event, selection):
    for key, expected in selection.items():
        field, _, modifier = key.partition("|")
        if not match_field(event.get(field), modifier or None, expected):
            return False
    return True


def rule_matches(event, detection):
    condition = str(detection.get("condition", "selection")).strip()
    hit = match_selection(event, detection.get("selection", {}))
    if condition == "selection":
        return hit
    if condition == "selection and not filter":
        return hit and not match_selection(event, detection.get("filter", {}))
    sys.exit(f"unsupported condition: {condition!r}")


# --- helpers -----------------------------------------------------------------


def load_corpus(path):
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_attack_ids(path):
    ids = set()
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                ids.add(line.upper())
    return ids


def rule_technique_ids(rule):
    """Extract T#### / T####.### from attack.* tags."""
    techniques = []
    for tag in rule.get("tags", []):
        t = str(tag)
        if t.lower().startswith("attack.t"):
            techniques.append(t.split(".", 1)[1].upper())  # tNNNN[.NNN] -> TNNNN
    return techniques


def review_rule(rule, corpus, attack_ids):
    detection = rule["detection"]
    techs = rule_technique_ids(rule)

    # 1. fire at corpus
    benign_fps = 0
    malicious_total = 0
    malicious_caught = 0
    missed_targets = []
    for e in corpus:
        label = e.get("_label")
        ev = {k: v for k, v in e.items() if not k.startswith("_")}
        hit = rule_matches(ev, detection)
        if label == "benign":
            if hit:
                benign_fps += 1
        elif label == "malicious":
            # Count malicious events for this rule's tagged technique(s). Match on
            # the BASE technique (strip the sub-technique) so a rule tagged with a
            # fabricated sub-ID (e.g. T1047.002) still maps to its real-technique
            # known-bad sample — the fabricated tag then surfaces as its own
            # finding rather than masquerading as "no target sample".
            ev_tech = str(e.get("_technique", "")).upper()
            ev_base = ev_tech.split(".")[0]
            rule_bases = {t.split(".")[0] for t in techs}
            if ev_tech in techs or ev_base in rule_bases:
                malicious_total += 1
                if hit:
                    malicious_caught += 1
                else:
                    missed_targets.append(ev_tech)

    # 2. resolve tags
    bad_tags = [t for t in techs if t not in attack_ids]

    findings = []
    if malicious_total and malicious_caught < malicious_total:
        findings.append(
            f"MISS: caught {malicious_caught}/{malicious_total} of its tagged "
            f"malicious samples ({', '.join(sorted(set(missed_targets)))})"
        )
    if not techs:
        findings.append("NO ATT&CK TAG: cannot verify coverage against ground truth")
    elif malicious_total == 0:
        findings.append(
            "NO TARGET SAMPLE: tagged technique(s) have no labelled known-bad in "
            "the corpus — coverage unprovable"
        )
    if benign_fps:
        findings.append(f"FALSE POSITIVE: fires on {benign_fps} benign event(s)")
    if bad_tags:
        findings.append(
            f"FABRICATED ATT&CK ID: {', '.join(bad_tags)} not in the ATT&CK list"
        )
    return findings, malicious_caught, malicious_total, benign_fps


def main():
    ap = argparse.ArgumentParser(description="Fire AI-drafted Sigma rules at a labelled corpus.")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--attack", required=True)
    ap.add_argument("rules", nargs="+", help="rule files or globs")
    args = ap.parse_args()

    corpus = load_corpus(args.corpus)
    attack_ids = load_attack_ids(args.attack)

    rule_paths = []
    for r in args.rules:
        rule_paths.extend(sorted(glob.glob(r)) if any(c in r for c in "*?[") else [r])

    print("=" * 72)
    print("AI-DRAFTED DETECTION REVIEW — fire-test + tag resolution")
    print(f"  corpus : {args.corpus}  ({len(corpus)} labelled events)")
    print(f"  attack : {args.attack}  ({len(attack_ids)} valid IDs)")
    print("=" * 72)

    any_bad = False
    for path in rule_paths:
        with open(path) as fh:
            rule = yaml.safe_load(fh)
        findings, caught, total, fps = review_rule(rule, corpus, attack_ids)
        verdict = "PASS" if not findings else "REVIEW FAIL"
        any_bad = any_bad or bool(findings)
        print(f"\n[{verdict}] {path}")
        print(f"         title: {rule.get('title', '<untitled>')}")
        print(f"         logsource: {rule.get('logsource', {}).get('category', '?')}")
        if findings:
            for f in findings:
                print(f"         - {f}")
        else:
            print(f"         - fires on {caught}/{total} malicious, 0 FPs, tags resolve")

    print("\n" + "=" * 72)
    if any_bad:
        print("GATE: BLOCKED — one or more AI drafts misfired. Do not ship as-is.")
    else:
        print("GATE: CLEAR — every draft fired correctly and resolved its tags.")
    print("=" * 72)
    sys.exit(1 if any_bad else 0)


if __name__ == "__main__":
    main()
