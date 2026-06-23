#!/usr/bin/env python3
"""
eval.py — Score a CloudTrail Sigma rule against a HELD-OUT, labelled corpus and print a scorecard.
Doubles as a CI regression gate: pass --gate <metric>=<min/max> and the process exits non-zero
when the rule scores worse than the declared threshold.

The system under test is a DETECTION (the IAM CreateUser -> AttachUserPolicy privesc Sigma rule),
not a model. A detection is still a non-deterministic-in-practice classifier over a 99.99%-benign
event stream: it has a recall (does it catch the attacks?) and a false-positive rate (does it fire
on benign near-misses?). This harness measures both against events the rule was NEVER tuned on.

How it works:
  * It reads an actual Sigma rule (the same data/sigma_rule.yml the lab ships) and INTERPRETS the
    `create_user` / `attach_policy` selections, the `condition` (create_user followed by
    attach_policy), and the `timeframe`. That means a regressed rule (e.g. one that drops the
    admin-policy filter) genuinely matches differently — the eval grades the rule, not a hard-code.
  * It runs the interpreted rule over each labelled case in heldout.json and records whether the
    rule FIRED, then scores fire-vs-label as a binary classifier ('attack' = positive class).

CRUCIAL — this runs OFFLINE with NO AWS, NO network: it grades a committed Sigma rule against a
committed corpus, so `make eval` / `make demo` are deterministic in CI.

Examples:
  python3 eval_corpus/eval.py --rule data/sigma_rule.yml
  python3 eval_corpus/eval.py --rule data/sigma_rule.yml --gate recall=1.0
  python3 eval_corpus/eval.py --rule data/sigma_rule.yml --gate fp_rate=0.0
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required (it is installed in the lab container; `pip install pyyaml` locally).")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS = os.path.join(HERE, "heldout.json")


def _parse_time(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _parse_timeframe(tf) -> float:
    """Sigma timeframe like '5m' / '300s' / '1h' -> seconds. Defaults to 300s."""
    if not tf:
        return 300.0
    tf = str(tf).strip()
    unit = tf[-1]
    n = float(tf[:-1]) if tf[:-1] else 0.0
    return n * {"s": 1, "m": 60, "h": 3600}.get(unit, 60)


# --------------------------------------------------------------------------- Sigma interpreter


def _selection_matches(event: dict, selection: dict) -> bool:
    """Match one event against a Sigma selection block (supports |contains list modifiers)."""
    for key, want in selection.items():
        contains = key.endswith("|contains")
        field = key[: -len("|contains")] if contains else key
        # dotted field path, e.g. requestParameters.policyArn
        val = event
        for part in field.split("."):
            val = (val or {}).get(part) if isinstance(val, dict) else None
        if val is None:
            return False
        if isinstance(want, list):
            if contains:
                if not any(str(w) in str(val) for w in want):
                    return False
            else:
                if str(val) not in [str(w) for w in want]:
                    return False
        else:
            if contains:
                if str(want) not in str(val):
                    return False
            else:
                if str(val) != str(want):
                    return False
    return True


def rule_fires(records: list, rule: dict) -> bool:
    """Interpret a 'create_user followed by attach_policy' Sigma rule over a case's records.

    Honours: the create_user selection, the attach_policy selection (INCLUDING the policyArn
    filter when present), the timeframe window, and same-userName correlation. If the rule drops
    the policyArn filter (the regression), attach_policy matches a wider set of events -> more fires.
    """
    det = rule.get("detection", {})
    create_sel = det.get("create_user", {})
    attach_sel = det.get("attach_policy", {})
    window = _parse_timeframe(det.get("timeframe"))

    creates = [r for r in records if _selection_matches(r, create_sel)]
    attaches = [r for r in records if _selection_matches(r, attach_sel)]

    for c in creates:
        c_user = (c.get("requestParameters") or {}).get("userName")
        c_t = _parse_time(c["eventTime"])
        for a in attaches:
            a_user = (a.get("requestParameters") or {}).get("userName")
            if a_user != c_user:
                continue  # 'followed by' correlates on the same user
            a_t = _parse_time(a["eventTime"])
            delta = (a_t - c_t).total_seconds()
            if 0 <= delta <= window:
                return True
    return False


# --------------------------------------------------------------------------- scoring


def score(rule: dict, corpus: dict) -> dict:
    cases = corpus["cases"]
    tp = fp = tn = fn = 0
    missed_attacks = []     # false negatives — the rule went silent on a real attack
    false_alarms = []       # false positives — the rule fired on benign
    for case in cases:
        fired = rule_fires(case["records"], rule)
        is_attack = case["label"] == "attack"
        if is_attack and fired:
            tp += 1
        elif is_attack and not fired:
            fn += 1
            missed_attacks.append(case["id"])
        elif not is_attack and fired:
            fp += 1
            false_alarms.append(case["id"])
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fp_rate = fp / (fp + tn) if (fp + tn) else 0.0     # benign cases the rule alerted on
    fn_rate = fn / (tp + fn) if (tp + fn) else 0.0     # attacks the rule missed

    return {
        "evaluated": len(cases),
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "fp_rate": round(fp_rate, 3),
            "fn_rate": round(fn_rate, 3),
        },
        "missed_attacks": missed_attacks,
        "false_alarms": false_alarms,
    }


def print_scorecard(rule_path: str, s: dict):
    m, c = s["metrics"], s["confusion"]
    print("\n=== Sigma rule scorecard (held-out CloudTrail corpus) ===")
    print(f"Rule: {rule_path}")
    print(f"Cases evaluated: {s['evaluated']}   (positive class = ATTACK)\n")
    print("Confusion matrix (rule fired vs. ground truth):")
    print("                  rule FIRED   rule silent")
    print(f"  true attack       {c['tp']:^10} {c['fn']:^11}")
    print(f"  true benign       {c['fp']:^10} {c['tn']:^11}\n")
    print(f"  Recall  (attacks caught / all attacks) : {m['recall']:.1%}   <- a miss = an undetected breach")
    print(f"  FN-rate (attacks the rule went silent on): {m['fn_rate']:.1%}")
    print(f"  Precision (of fires, truly malicious)   : {m['precision']:.1%}")
    print(f"  FP-rate  (benign that fired = alert fatigue): {m['fp_rate']:.1%}   <- the false-positive economics")
    print(f"  F1                                       : {m['f1']:.3f}")
    if s["missed_attacks"]:
        print(f"\n  MISSED ATTACKS (false negatives): {', '.join(s['missed_attacks'])}")
    if s["false_alarms"]:
        print(f"  FALSE ALARMS on benign (false positives): {', '.join(s['false_alarms'])}")
    print()


# --------------------------------------------------------------------------- gate


def apply_gate(scorecard: dict, gate: str) -> bool:
    """gate is 'metric=threshold'. For recall/precision/f1 it's a FLOOR (>=); for fp_rate/fn_rate
    it's a CEILING (<=) since those are costs you want low. Fails CLOSED on a missing metric."""
    try:
        metric, threshold = gate.split("=")
        threshold = float(threshold)
    except ValueError:
        print(f"GATE ERROR: malformed --gate '{gate}' (expected metric=value).", file=sys.stderr)
        return False
    value = scorecard["metrics"].get(metric)
    if value is None:
        print(f"GATE ERROR: metric '{metric}' not in scorecard {list(scorecard['metrics'])}.",
              file=sys.stderr)
        return False  # fail closed: a gate that can't read the score must not pass
    ceiling_metrics = {"fp_rate", "fn_rate"}
    if metric in ceiling_metrics:
        ok = value <= threshold
        rel = f"<= {threshold:.3f}"
    else:
        ok = value >= threshold
        rel = f">= {threshold:.3f}"
    verb = "PASS" if ok else "FAIL"
    print(f"REGRESSION GATE [{verb}]: {metric} = {value:.3f}  (threshold {rel})")
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rule", default="data/sigma_rule.yml",
                   help="the Sigma rule to grade (the regressed fixture lives in eval_corpus/)")
    p.add_argument("--corpus", default=DEFAULT_CORPUS, help="held-out labelled corpus")
    p.add_argument("--gate", action="append", default=[],
                   help="metric=value; repeatable. recall/precision/f1 are floors, "
                        "fp_rate/fn_rate are ceilings. e.g. --gate recall=1.0 --gate fp_rate=0.0")
    args = p.parse_args()

    with open(args.rule) as f:
        rule = yaml.safe_load(f)
    with open(args.corpus) as f:
        corpus = json.load(f)

    scorecard = score(rule, corpus)
    print_scorecard(args.rule, scorecard)

    if args.gate:
        passed = all(apply_gate(scorecard, g) for g in args.gate)
        if not passed:
            sys.exit(1)  # non-zero -> the CI build fails
    return 0


if __name__ == "__main__":
    sys.exit(main())
