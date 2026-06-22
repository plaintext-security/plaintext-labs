#!/usr/bin/env python3
"""
eval.py — Score an AI security system against a HELD-OUT, labelled corpus and print a scorecard.
Doubles as a CI regression gate: pass --gate <metric>=<min> and the process exits non-zero
when the system scores below the declared threshold.

Two modes:

  triage  — binary classification (malicious vs benign). Reports a confusion matrix plus
            precision / recall / F1 / false-negative-rate / false-positive-rate on the MALICIOUS
            class (the class whose miss costs a breach). Accuracy is reported too, and shown to be
            misleading on its own.
  rag     — retrieval quality. Reports retrieval@k: for each question, did a genuinely-relevant
            document land in the system's top-k retrieved chunks?

CRUCIAL — this runs OFFLINE with NO live model. It scores RECORDED system outputs (the
predictions-*.json / retrieval-*.json fixtures), so `make eval` / `make demo` are deterministic in
CI. In real use you replace the fixture with your actual model's output and run the identical eval.

Examples:
  python3 scripts/eval.py triage --predictions data/predictions-good.json
  python3 scripts/eval.py triage --predictions data/predictions-good.json --gate recall=0.80
  python3 scripts/eval.py rag    --retrieval   data/retrieval-good.json   --gate recall_at_k=0.75
"""

import argparse
import json
import sys


def _load(path):
    with open(path) as f:
        data = json.load(f)
    # Allow a leading "_comment" key in fixtures for documentation.
    if isinstance(data, dict):
        data.pop("_comment", None)
    return data


# --------------------------------------------------------------------------- triage

def score_triage(predictions: dict, labels: dict) -> dict:
    """Binary malicious/benign. 'malicious' is the positive class."""
    ids = [i for i in labels if i in predictions]
    tp = fp = tn = fn = 0
    false_negatives = []  # missed attacks — the dangerous failures
    false_positives = []
    for i in ids:
        truth = labels[i]["label"]
        pred = predictions[i]
        if truth == "malicious" and pred == "malicious":
            tp += 1
        elif truth == "benign" and pred == "malicious":
            fp += 1
            false_positives.append(i)
        elif truth == "benign" and pred == "benign":
            tn += 1
        elif truth == "malicious" and pred == "benign":
            fn += 1
            false_negatives.append(i)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0          # caught attacks / all real attacks
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fn_rate = fn / (tp + fn) if (tp + fn) else 0.0          # the false "all clear" rate
    fp_rate = fp / (fp + tn) if (fp + tn) else 0.0          # analyst-time cost
    accuracy = (tp + tn) / len(ids) if ids else 0.0

    return {
        "mode": "triage",
        "evaluated": len(ids),
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "fn_rate": round(fn_rate, 3),
            "fp_rate": round(fp_rate, 3),
            "accuracy": round(accuracy, 3),
        },
        "false_negatives": false_negatives,
        "false_positives": false_positives,
    }


def print_triage(s: dict):
    m = s["metrics"]
    c = s["confusion"]
    print("\n=== Triage scorecard (held-out corpus) ===")
    print(f"Items evaluated: {s['evaluated']}   (positive class = MALICIOUS)\n")
    print("Confusion matrix:")
    print(f"                 pred malicious   pred benign")
    print(f"  true malicious   {c['tp']:^14} {c['fn']:^12}")
    print(f"  true benign      {c['fp']:^14} {c['tn']:^12}\n")
    print(f"  Recall  (caught attacks / all attacks) : {m['recall']:.1%}   <- the metric that matters")
    print(f"  FN-rate (missed attacks, false 'clear'): {m['fn_rate']:.1%}")
    print(f"  Precision (of flagged, truly malicious): {m['precision']:.1%}")
    print(f"  FP-rate  (benign flagged = analyst cost): {m['fp_rate']:.1%}")
    print(f"  F1                                       : {m['f1']:.3f}")
    print(f"  Accuracy (DECEPTIVE on imbalance alone)  : {m['accuracy']:.1%}")
    if s["false_negatives"]:
        print(f"\n  MISSED ATTACKS (false negatives): {', '.join(s['false_negatives'])}")
    if s["false_positives"]:
        print(f"  Benign over-flagged (false positives): {', '.join(s['false_positives'])}")
    print()


# --------------------------------------------------------------------------- rag

def score_rag(retrieval: dict, heldout: dict, k: int) -> dict:
    questions = heldout["questions"]
    hits = 0
    misses = []
    for q in questions:
        qid = q["id"]
        relevant = set(q["relevant_docs"])
        retrieved = retrieval.get(qid, [])[:k]
        if relevant & set(retrieved):
            hits += 1
        else:
            misses.append(qid)
    total = len(questions)
    recall_at_k = hits / total if total else 0.0
    return {
        "mode": "rag",
        "k": k,
        "evaluated": total,
        "metrics": {"recall_at_k": round(recall_at_k, 3)},
        "hits": hits,
        "misses": misses,
    }


def print_rag(s: dict):
    print("\n=== RAG retrieval scorecard (held-out Q&A) ===")
    print(f"Questions evaluated: {s['evaluated']}   k = {s['k']}\n")
    print(f"  retrieval@{s['k']} (>=1 relevant doc in top-{s['k']}): {s['metrics']['recall_at_k']:.1%}")
    print(f"  hits: {s['hits']}/{s['evaluated']}")
    if s["misses"]:
        print(f"  MISSED (no relevant doc retrieved): {', '.join(s['misses'])}")
    print()


# --------------------------------------------------------------------------- gate

def apply_gate(scorecard: dict, gate: str) -> bool:
    """gate is 'metric=min'. Returns True if pass. Fails CLOSED on a missing/garbled metric."""
    try:
        metric, threshold = gate.split("=")
        threshold = float(threshold)
    except ValueError:
        print(f"GATE ERROR: malformed --gate '{gate}' (expected metric=min).", file=sys.stderr)
        return False
    value = scorecard["metrics"].get(metric)
    if value is None:
        print(f"GATE ERROR: metric '{metric}' not in scorecard {list(scorecard['metrics'])}.",
              file=sys.stderr)
        return False  # fail closed: a gate that can't read the score must not pass
    ok = value >= threshold
    verb = "PASS" if ok else "FAIL"
    print(f"REGRESSION GATE [{verb}]: {metric} = {value:.3f}  (threshold >= {threshold:.3f})")
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="mode", required=True)

    t = sub.add_parser("triage", help="binary malicious/benign classification eval")
    t.add_argument("--predictions", default="data/predictions-good.json",
                   help="recorded system outputs to grade")
    t.add_argument("--labels", default="data/triage-labels.json")
    t.add_argument("--gate", help="metric=min, e.g. recall=0.80 (fails the process below it)")

    r = sub.add_parser("rag", help="retrieval@k eval")
    r.add_argument("--retrieval", default="data/retrieval-good.json",
                   help="recorded top-k retrieval to grade")
    r.add_argument("--heldout", default="data/rag-heldout.json")
    r.add_argument("--k", type=int, default=3)
    r.add_argument("--gate", help="metric=min, e.g. recall_at_k=0.75")

    args = p.parse_args()

    if args.mode == "triage":
        scorecard = score_triage(_load(args.predictions), _load(args.labels))
        print_triage(scorecard)
    else:
        scorecard = score_rag(_load(args.retrieval), _load(args.heldout), args.k)
        print_rag(scorecard)

    if args.gate:
        if not apply_gate(scorecard, args.gate):
            sys.exit(1)  # non-zero -> the CI build fails

    return 0


if __name__ == "__main__":
    sys.exit(main())
