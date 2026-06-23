#!/usr/bin/env python3
"""
eval.py — Score a detection ruleset against a HELD-OUT, labelled corpus and print a scorecard.
Doubles as a CI regression gate: pass --gate <metric>=<bound> and the process exits non-zero
when the ruleset scores worse than the declared threshold.

The held-out corpus (heldout/corpus.jsonl) is DISTINCT from the demo/tuning atomics in atomics/:
every record is a Sysmon-shaped event labelled malicious (a technique the rules MUST catch) or
benign (activity the rules must NOT fire on, including near-miss lookalikes). You tune your rules
against the atomics; you grade them — honestly — against this held-out set the rules never saw.

The positive class is MALICIOUS. We report the confusion matrix and:
  recall   — caught attacks / all real attacks   (the metric that matters; a miss can be a breach)
  fp_rate  — benign events that fired             (the analyst-time cost of that recall)
  precision, f1, accuracy                          (accuracy is shown to be misleading on imbalance)

CRUCIAL — this runs OFFLINE with no SIEM and no network. It replays recorded events through the
same in-process Sigma matcher the demo uses (test_detections.rule_fires), so `make eval` / `make
demo` are deterministic in CI. In real use you point --corpus at events exported from your own SIEM.

Gate direction is per-metric: recall/precision/f1 are floors (>=); fp_rate is a ceiling (<=).

Examples:
  python3 eval.py                                          # scorecard on the good rules
  python3 eval.py --gate recall=0.90                       # fail the build if recall < 0.90
  python3 eval.py --gate fp_rate=0.05                      # fail the build if FP-rate > 0.05
  python3 eval.py --rules heldout/rules-regressed --gate recall=0.90   # the planted regression
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

# Reuse the EXACT matcher the demo uses — one detection engine, scored two ways.
from test_detections import rule_fires

HERE = Path(__file__).parent
CEILING_METRICS = {"fp_rate"}  # lower is better; --gate is an upper bound for these


def load_rules(rules_dir: Path) -> list[dict]:
    rules = []
    for path in sorted(rules_dir.glob("*.yml")):
        data = yaml.safe_load(path.read_text())
        if data:
            data["_path"] = path.name
            rules.append(data)
    return rules


def load_corpus(path: Path) -> list[dict]:
    events = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events


def score(rules: list[dict], corpus: list[dict]) -> dict:
    tp = fp = tn = fn = 0
    false_negatives = []  # missed attacks — the dangerous failures
    false_positives = []
    for event in corpus:
        is_malicious = event.get("label") == "malicious"
        fired = any(rule_fires(r, event) for r in rules)
        if is_malicious and fired:
            tp += 1
        elif is_malicious and not fired:
            fn += 1
            false_negatives.append(event["id"])
        elif not is_malicious and fired:
            fp += 1
            false_positives.append(event["id"])
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fp_rate = fp / (fp + tn) if (fp + tn) else 0.0
    accuracy = (tp + tn) / len(corpus) if corpus else 0.0

    return {
        "evaluated": len(corpus),
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "fp_rate": round(fp_rate, 3),
            "accuracy": round(accuracy, 3),
        },
        "false_negatives": false_negatives,
        "false_positives": false_positives,
    }


def print_scorecard(s: dict, rules_dir: str):
    m, c = s["metrics"], s["confusion"]
    print("\n=== Detection scorecard (held-out corpus) ===")
    print(f"Ruleset: {rules_dir}   Events: {s['evaluated']}   (positive class = MALICIOUS)\n")
    print("Confusion matrix:")
    print("                 fired          did not fire")
    print(f"  true malicious   {c['tp']:^12} {c['fn']:^14}")
    print(f"  true benign      {c['fp']:^12} {c['tn']:^14}\n")
    print(f"  Recall  (caught attacks / all attacks) : {m['recall']:.1%}   <- the metric that matters")
    print(f"  FP-rate (benign fired = analyst cost)  : {m['fp_rate']:.1%}")
    print(f"  Precision (of fired, truly malicious)  : {m['precision']:.1%}")
    print(f"  F1                                     : {m['f1']:.3f}")
    print(f"  Accuracy (DECEPTIVE on imbalance alone): {m['accuracy']:.1%}")
    if s["false_negatives"]:
        print(f"\n  MISSED ATTACKS (false negatives): {', '.join(s['false_negatives'])}")
    if s["false_positives"]:
        print(f"  Benign that fired (false positives): {', '.join(s['false_positives'])}")
    print()


def apply_gate(scorecard: dict, gate: str) -> bool:
    """gate is 'metric=bound'. Floors for recall/precision/f1, ceiling for fp_rate.
    Fails CLOSED on a missing/garbled metric — a gate that can't read the score must not pass."""
    try:
        metric, bound = gate.split("=")
        bound = float(bound)
    except ValueError:
        print(f"GATE ERROR: malformed --gate '{gate}' (expected metric=bound).", file=sys.stderr)
        return False
    value = scorecard["metrics"].get(metric)
    if value is None:
        print(f"GATE ERROR: metric '{metric}' not in scorecard {list(scorecard['metrics'])}.",
              file=sys.stderr)
        return False
    if metric in CEILING_METRICS:
        ok = value <= bound
        rel = f"<= {bound:.3f}"
    else:
        ok = value >= bound
        rel = f">= {bound:.3f}"
    verb = "PASS" if ok else "FAIL"
    print(f"REGRESSION GATE [{verb}]: {metric} = {value:.3f}  (require {rel})")
    return ok


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rules", default=str(HERE / "rules"),
                   help="rules dir to grade (default: rules; use heldout/rules-regressed for the planted regression)")
    p.add_argument("--corpus", default=str(HERE / "heldout" / "corpus.jsonl"),
                   help="held-out labelled event corpus")
    p.add_argument("--gate", action="append", default=[],
                   help="metric=bound; repeatable. Floors for recall/precision/f1, ceiling for fp_rate")
    args = p.parse_args()

    rules = load_rules(Path(args.rules))
    corpus = load_corpus(Path(args.corpus))
    scorecard = score(rules, corpus)
    print_scorecard(scorecard, args.rules)

    if args.gate:
        passed = all(apply_gate(scorecard, g) for g in args.gate)
        if not passed:
            sys.exit(1)  # non-zero -> the CI build fails
    return 0


if __name__ == "__main__":
    sys.exit(main())
