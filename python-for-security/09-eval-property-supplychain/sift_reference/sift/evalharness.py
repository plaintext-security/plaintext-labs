"""Eval-as-code — a HELD-OUT corpus, a metric, a scorecard, a regression gate.

This is the durable pattern `pydantic-evals` formalizes: you can't improve what you
don't measure. The corpus is held out from tuning; the gate fails the build when a
change drops the score below baseline.
"""
from __future__ import annotations

from collections.abc import Callable

# Held-out labelled corpus (indicator, true_label). NEVER tuned against.
HELD_OUT: list[tuple[str, str]] = [
    ("45.83.192.44", "malicious"),
    ("45.83.192.99", "malicious"),
    ("203.0.113.9", "malicious"),
    ("198.51.100.7", "malicious"),   # classifier MISSES this one → recall < 1.0 (honest)
    ("8.8.8.8", "benign"),
    ("1.1.1.1", "benign"),
    ("10.0.0.5", "benign"),
    ("172.16.0.9", "benign"),
]

RECALL_BASELINE = 0.70


def score(classifier: Callable[[str], str]) -> dict[str, float]:
    """Confusion matrix + precision/recall for the 'malicious' class."""
    tp = fp = fn = tn = 0
    for indicator, label in HELD_OUT:
        pred = classifier(indicator)
        if label == "malicious" and pred == "malicious":
            tp += 1
        elif label == "benign" and pred == "malicious":
            fp += 1
        elif label == "malicious" and pred == "benign":
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall}
