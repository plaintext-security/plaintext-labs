"""Unit tests for the eval harness scoring + gate (pytest, stdlib only).

These prove the SCORER is correct — distinct from grading the parser. Run with:
    python -m pytest tests/ -v
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import eval as harness  # noqa: E402


def test_perfect_score():
    labels = {"a": "attack", "b": "benign"}
    verdicts = {"a": "attack", "b": "benign"}
    r = harness.score(verdicts, labels)
    assert r["confusion"] == {"TP": 1, "FP": 0, "FN": 0, "TN": 1}
    assert r["recall"] == 1.0
    assert r["precision"] == 1.0
    assert r["accuracy"] == 1.0


def test_missing_verdict_counts_as_under_detection():
    # An IP the tool never scored must default to benign -> a missed attack (FN),
    # never a skipped row. This is the fail-closed behaviour of the scorer.
    labels = {"a": "attack"}
    verdicts = {}  # tool produced nothing for "a"
    r = harness.score(verdicts, labels)
    assert r["confusion"]["FN"] == 1
    assert r["recall"] == 0.0


def test_recall_drops_when_attack_missed():
    labels = {"a": "attack", "b": "attack", "c": "benign"}
    verdicts = {"a": "attack", "b": "benign", "c": "benign"}  # missed one attack
    r = harness.score(verdicts, labels)
    assert r["recall"] == pytest.approx(0.5)
    assert r["confusion"]["FN"] == 1


def test_do_nothing_baseline_high_accuracy_zero_recall():
    # The lab's key lesson: a do-nothing parser scores high accuracy on an
    # imbalanced corpus while catching zero attacks.
    labels = {**{f"atk{i}": "attack" for i in range(2)},
              **{f"ben{i}": "benign" for i in range(11)}}
    verdicts = {ip: "benign" for ip in labels}  # flags nothing
    r = harness.score(verdicts, labels)
    assert r["recall"] == 0.0
    assert r["accuracy"] > 0.80  # looks great, catches nothing


def test_gate_parse_rejects_unknown_metric():
    with pytest.raises(SystemExit):
        harness.parse_gate("recal=0.9")  # typo'd metric -> fail closed


def test_gate_parse_rejects_non_numeric_floor():
    with pytest.raises(SystemExit):
        harness.parse_gate("recall=high")


def test_gate_parse_valid():
    assert harness.parse_gate("recall=0.85") == ("recall", 0.85)


def test_invalid_predicted_label_is_fatal():
    with pytest.raises(SystemExit):
        harness.score({"a": "maybe"}, {"a": "attack"})
