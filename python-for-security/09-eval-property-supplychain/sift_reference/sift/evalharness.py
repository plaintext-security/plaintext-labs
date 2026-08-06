"""Eval-as-code — a HELD-OUT corpus of REAL Suricata alerts, a metric, a scorecard, a regression gate.

This is the durable pattern `pydantic-evals` formalizes: you can't improve what you don't measure.
The corpus is `evals/holdout.jsonl` — real EVE `alert` events drawn from the anchor capture, each
hand-labelled ``true_positive`` / ``false_positive`` — and it is **held out from tuning**: nothing on
the threshold/rule path reads it. The gate fails the build when a change drops the score below baseline.

Metric choice (decided before the number was read): we optimize **recall** for the malicious
(``true_positive``) class. In triage, a missed true positive is a missed intrusion — far costlier than
an analyst dismissing one extra false alarm — so recall is the number that must not regress. We report
precision too, but recall is what the gate defends.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from sift.classify import EVE_ADAPTER, AlertEvent

# evals/holdout.jsonl lives beside the lab root, two levels up from sift_reference/sift/.
HOLDOUT = Path(__file__).resolve().parents[2] / "evals" / "holdout.jsonl"

# The metric the gate defends, and the threshold, both justified above and pinned BEFORE reading the
# score. Precision is reported for context; recall is the regression gate.
RECALL_BASELINE = 0.90
PRECISION_FLOOR = 0.80
POSITIVE = "true_positive"


def load_holdout() -> list[tuple[AlertEvent, str]]:
    """Parse each held-out line into a typed `AlertEvent` (the M02 boundary) + its ground-truth label.

    Held-out means held out: this is the ONLY reader of `holdout.jsonl`, and nothing here feeds the
    triage rule or its thresholds — it just measures.
    """
    cases: list[tuple[AlertEvent, str]] = []
    with HOLDOUT.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            event = EVE_ADAPTER.validate_python(rec["event"])  # real EVE alert → typed AlertEvent
            cases.append((event, rec["label"]))
    return cases


def score(classifier: Callable[[AlertEvent], str]) -> dict[str, float]:
    """Confusion matrix + precision/recall for the `true_positive` class over the held-out corpus."""
    tp = fp = fn = tn = 0
    for event, label in load_holdout():
        pred = classifier(event)
        if label == POSITIVE and pred == POSITIVE:
            tp += 1
        elif label != POSITIVE and pred == POSITIVE:
            fp += 1
        elif label == POSITIVE and pred != POSITIVE:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "n": tp + fp + fn + tn,
    }
