#!/usr/bin/env python3
"""eval.py — a precision/recall scorecard + CI regression gate for a detection tool.

The eval-as-code IS the artifact: a held-out labelled corpus + a scorecard + a gate
that fails the build when detection quality regresses. Standard library only — the
whole eval is offline and deterministic.

What it does:
  1. Gets per-IP verdicts for the tool under test, either by running it
     (--tool scripts/parser_good.py) or by reading recorded verdicts (--verdicts f.json).
  2. Compares them to the held-out answer key (--labels data/auth-labels.json),
     treating "attack" as the positive class.
  3. Prints a confusion matrix (TP/FP/FN/TN) and precision / recall / F1 / FP-rate /
     accuracy.
  4. If --gate METRIC=FLOOR is given, exits 0 when metric >= floor, else exits 1.
     FAILS CLOSED: an unknown metric name, an erroring tool, or a missing verdict is a
     non-zero exit, never a silent pass.

Examples:
    python3 eval.py --tool scripts/parser_good.py --corpus data/auth-corpus.jsonl \\
                    --labels data/auth-labels.json --gate recall=0.85
    python3 eval.py --verdicts results/verdicts-good.json \\
                    --labels data/auth-labels.json
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

POSITIVE = "attack"
NEGATIVE = "benign"
METRICS = ("precision", "recall", "f1", "fp_rate", "accuracy")


def die(msg: str, code: int = 2) -> None:
    """Fail closed: print to stderr and exit non-zero."""
    print(f"eval.py: ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def run_tool(tool: str, corpus: str) -> dict[str, str]:
    """Run the parser under test and parse its JSON {ip: verdict} stdout."""
    try:
        proc = subprocess.run(
            [sys.executable, tool, corpus],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        die(f"could not run tool {tool!r}: {exc}")
    if proc.returncode != 0:
        die(f"tool {tool!r} exited {proc.returncode}: {proc.stderr.strip()}")
    try:
        verdicts = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        die(f"tool {tool!r} did not emit valid JSON verdicts: {exc}")
    if not isinstance(verdicts, dict):
        die(f"tool {tool!r} verdicts must be a JSON object {{ip: verdict}}")
    return verdicts


def load_verdicts(path: str) -> dict[str, str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        die(f"{path}: verdicts must be a JSON object {{ip: verdict}}")
    return data


def load_labels(path: str) -> dict[str, str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    verdicts = data.get("verdicts", {})
    labels = {ip: entry["label"] for ip, entry in verdicts.items()}
    if not labels:
        die(f"{path}: no labels found under 'verdicts'")
    return labels


def score(verdicts: dict[str, str], labels: dict[str, str]) -> dict:
    """Confusion matrix + metrics over the LABELLED IPs only (held-out answer key)."""
    tp = fp = fn = tn = 0
    rows = []
    for ip, truth in sorted(labels.items()):
        # Fail closed: a labelled IP the tool never produced a verdict for is a miss,
        # not an excuse to skip. Default a missing verdict to NEGATIVE (under-detection).
        predicted = verdicts.get(ip, NEGATIVE)
        if predicted not in (POSITIVE, NEGATIVE):
            die(f"verdict for {ip!r} is {predicted!r}, expected {POSITIVE!r}/{NEGATIVE!r}")
        if truth == POSITIVE and predicted == POSITIVE:
            tp += 1; outcome = "TP"
        elif truth == NEGATIVE and predicted == POSITIVE:
            fp += 1; outcome = "FP"
        elif truth == POSITIVE and predicted == NEGATIVE:
            fn += 1; outcome = "FN"
        else:
            tn += 1; outcome = "TN"
        rows.append((ip, truth, predicted, outcome))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fp_rate = fp / (fp + tn) if (fp + tn) else 0.0
    accuracy = (tp + tn) / (tp + fp + fn + tn) if (tp + fp + fn + tn) else 0.0

    return {
        "rows": rows,
        "confusion": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
        "precision": precision, "recall": recall, "f1": f1,
        "fp_rate": fp_rate, "accuracy": accuracy,
    }


def print_scorecard(result: dict) -> None:
    print("=== Per-IP verdicts (truth vs. predicted) ===")
    for ip, truth, predicted, outcome in result["rows"]:
        flag = "  " if outcome in ("TP", "TN") else "<<"
        print(f"  {ip:<16} truth={truth:<7} pred={predicted:<7} -> {outcome} {flag}")
    c = result["confusion"]
    print("\n=== Confusion matrix (positive class = 'attack') ===")
    print(f"  TP={c['TP']}  FP={c['FP']}  FN={c['FN']}  TN={c['TN']}")
    print("\n=== Scorecard ===")
    print(f"  precision : {result['precision']:.3f}")
    print(f"  recall    : {result['recall']:.3f}   <- load-bearing: a missed attack is the costly error")
    print(f"  f1        : {result['f1']:.3f}")
    print(f"  fp_rate   : {result['fp_rate']:.3f}")
    print(f"  accuracy  : {result['accuracy']:.3f}   <- misleading on this imbalanced corpus")


def parse_gate(spec: str) -> tuple[str, float]:
    if "=" not in spec:
        die(f"--gate must be METRIC=FLOOR (e.g. recall=0.85), got {spec!r}")
    metric, _, floor = spec.partition("=")
    metric = metric.strip().lower()
    if metric not in METRICS:
        die(f"unknown gate metric {metric!r}; choose from {', '.join(METRICS)}")
    try:
        return metric, float(floor)
    except ValueError:
        die(f"gate floor {floor!r} is not a number")


def main() -> None:
    ap = argparse.ArgumentParser(description="Scorecard + regression gate for a detection tool.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--tool", help="path to a parser to run (emits {ip: verdict} JSON)")
    src.add_argument("--verdicts", help="path to a recorded {ip: verdict} JSON file")
    ap.add_argument("--corpus", help="corpus JSONL (required with --tool)")
    ap.add_argument("--labels", required=True, help="held-out answer key (auth-labels.json)")
    ap.add_argument("--gate", help="enforce METRIC=FLOOR, e.g. recall=0.85; exit 1 if below")
    args = ap.parse_args()

    if args.tool:
        if not args.corpus:
            die("--corpus is required with --tool")
        verdicts = run_tool(args.tool, args.corpus)
    else:
        verdicts = load_verdicts(args.verdicts)

    labels = load_labels(args.labels)
    result = score(verdicts, labels)
    print_scorecard(result)

    if not args.gate:
        sys.exit(0)

    metric, floor = parse_gate(args.gate)
    value = result[metric]
    print(f"\n=== Gate: {metric} >= {floor:.3f} ===")
    if value >= floor:
        print(f"PASS: {metric}={value:.3f} >= {floor:.3f}  (gate GREEN)")
        sys.exit(0)
    print(f"FAIL: {metric}={value:.3f} <  {floor:.3f}  (gate RED — detection regressed)")
    sys.exit(1)


if __name__ == "__main__":
    main()
