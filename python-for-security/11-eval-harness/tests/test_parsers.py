"""Tests for the parsers under test: correctness on the corpus + robustness.

These verify the GOOD parser catches every labelled attack, the REGRESSED parser
under-detects the slow-and-low spray, and NEITHER crashes on malformed input.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import parser_good  # noqa: E402
import parser_regressed  # noqa: E402

CORPUS = ROOT / "data" / "auth-corpus.jsonl"
LABELS = ROOT / "data" / "auth-labels.json"


def expected_attack_ips():
    labels = json.loads(LABELS.read_text())["verdicts"]
    return {ip for ip, e in labels.items() if e["label"] == "attack"}


def test_good_parser_catches_all_attacks():
    verdicts = parser_good.classify(str(CORPUS))
    for ip in expected_attack_ips():
        assert verdicts.get(ip) == "attack", f"good parser missed {ip}"


def test_good_parser_no_false_positive_on_cron_nearmiss():
    verdicts = parser_good.classify(str(CORPUS))
    assert verdicts.get("10.0.5.20", "benign") == "benign"


def test_regressed_parser_misses_slow_and_low():
    # The planted regression: the slow-and-low spray is silently marked benign.
    verdicts = parser_regressed.classify(str(CORPUS))
    assert verdicts.get("198.51.100.7", "benign") == "benign", \
        "regression should UNDER-detect 198.51.100.7"
    # ...but it still catches the fast burst, which is why unit tests/demo pass.
    assert verdicts.get("203.0.113.10") == "attack"


def test_neither_parser_crashes_on_malformed_input(tmp_path):
    junk = tmp_path / "junk.jsonl"
    junk.write_text(
        '\n'
        '{"id": "x", "line": "Nov 15 10:00:00 host sshd[1]: Failed password for root from 192.0.2"}\n'
        '{"id": "y", "line": "<<< binary noise >>>"}\n'
        'not even json\n'
        '{"id": "z", "line": ""}\n',
        encoding="utf-8",
    )
    # Must return cleanly (no exception) on every malformed shape.
    assert parser_good.classify(str(junk)) == {}
    assert parser_regressed.classify(str(junk)) == {}
