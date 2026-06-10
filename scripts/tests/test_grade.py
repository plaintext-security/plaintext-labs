"""Tests for grade.py — the lab grader.

Covers every check type, the all-pass receipt write, the required-fail gate (no
receipt), --no-receipt, HMAC-when-keyed, and the advisory/ai_rubric never-gate rule.
All offline: the only shelled command is a trivial `python3 -c` / `true` / `false`.
"""
from __future__ import annotations

import hashlib
import json

import pytest

import grade


# --- individual check functions ------------------------------------------------
def test_check_flag_match(monkeypatch):
    monkeypatch.setenv("FLAG", "hunter2")
    c = {"type": "flag", "expects_sha256": hashlib.sha256(b"hunter2").hexdigest()}
    ok, _ = grade.check_flag(c)
    assert ok


def test_check_flag_trims_whitespace(monkeypatch):
    monkeypatch.setenv("FLAG", "  hunter2\n")
    c = {"type": "flag", "expects_sha256": hashlib.sha256(b"hunter2").hexdigest()}
    assert grade.check_flag(c)[0]


def test_check_flag_mismatch(monkeypatch):
    monkeypatch.setenv("FLAG", "wrong")
    c = {"type": "flag", "expects_sha256": hashlib.sha256(b"hunter2").hexdigest()}
    assert grade.check_flag(c)[0] is False


def test_check_flag_unset_env():
    c = {"type": "flag", "expects_sha256": "x"}
    ok, detail = grade.check_flag(c)
    assert ok is False and "FLAG" in detail


def test_check_flag_custom_env(monkeypatch):
    monkeypatch.setenv("SECRET", "abc")
    c = {"type": "flag", "env": "SECRET", "expects_sha256": hashlib.sha256(b"abc").hexdigest()}
    assert grade.check_flag(c)[0]


def test_check_structural_match(in_tmp):
    (in_tmp / "a.md").write_text("uses UNION and parameterized queries")
    c = {"type": "structural", "file": "a.md", "must_match": ["union", "parameteri"]}
    assert grade.check_structural(c)[0]


def test_check_structural_missing_file():
    c = {"type": "structural", "file": "nope.md"}
    ok, detail = grade.check_structural(c)
    assert ok is False and "missing" in detail


def test_check_structural_must_match_fail(in_tmp):
    (in_tmp / "a.md").write_text("nothing here")
    c = {"type": "structural", "file": "a.md", "must_match": ["UNION"]}
    assert grade.check_structural(c)[0] is False


def test_check_structural_must_not_match_fail(in_tmp):
    (in_tmp / "a.md").write_text("secret S3cr3t leaked")
    c = {"type": "structural", "file": "a.md", "must_not_match": ["S3cr3t"]}
    assert grade.check_structural(c)[0] is False


def test_check_structural_json_valid(in_tmp):
    (in_tmp / "a.json").write_text('{"ok": true}')
    assert grade.check_structural({"type": "structural", "file": "a.json", "json_valid": True})[0]
    (in_tmp / "bad.json").write_text("{not json}")
    assert grade.check_structural({"type": "structural", "file": "bad.json", "json_valid": True})[0] is False


def test_check_artifact_functional_pass(in_tmp):
    (in_tmp / "tool.py").write_text("print('admin found')")
    c = {
        "type": "artifact_functional",
        "artifact": "tool.py",
        "run": "python3 {artifact}",
        "expect_exit": 0,
        "expect_stdout_contains": "admin",
    }
    assert grade.check_artifact_functional(c)[0]


def test_check_artifact_functional_missing_artifact():
    c = {"type": "artifact_functional", "artifact": "gone.py", "run": "python3 {artifact}"}
    ok, detail = grade.check_artifact_functional(c)
    assert ok is False and "missing" in detail


def test_check_artifact_functional_wrong_exit():
    c = {"type": "artifact_functional", "run": "python3 -c 'import sys; sys.exit(3)'", "expect_exit": 0}
    ok, detail = grade.check_artifact_functional(c)
    assert ok is False and "exit 3" in detail


def test_check_artifact_functional_stdout_missing():
    c = {"type": "artifact_functional", "run": "python3 -c 'print(1)'", "expect_stdout_contains": "admin"}
    assert grade.check_artifact_functional(c)[0] is False


def test_check_target_state_pass():
    assert grade.check_target_state({"type": "target_state", "run": "true"})[0]


def test_check_target_state_fail():
    assert grade.check_target_state({"type": "target_state", "run": "false"})[0] is False


def test_check_advisory_always_passes():
    ok, detail = grade.check_advisory({"type": "advisory", "note": "just info"})
    assert ok and "just info" in detail


def test_check_ai_rubric_no_artifact():
    # Advisory: passes even with no artifact present.
    assert grade.check_ai_rubric({"type": "ai_rubric", "file": "missing.md"})[0]


def test_check_ai_rubric_runs_judge_when_configured(in_tmp, monkeypatch, capsys):
    (in_tmp / "sub.md").write_text("my writeup")
    monkeypatch.setenv("AI_GRADER_CMD", "echo judge-feedback-for {file}")
    ok, _ = grade.check_ai_rubric({"type": "ai_rubric", "file": "sub.md", "rubric": "r.md"})
    assert ok
    assert "judge-feedback-for" in capsys.readouterr().out


# --- full grade() flow via main() ----------------------------------------------
def _write_manifest(d, checks, lab="test/lab"):
    path = d / "grade.yaml"
    path.write_text(json.dumps({"lab": lab, "checks": checks}))  # JSON is valid YAML
    return path


def test_main_all_pass_writes_receipt(in_tmp, capsys):
    (in_tmp / "a.md").write_text("hello world")
    _write_manifest(in_tmp, [{"name": "art", "type": "structural", "file": "a.md", "must_match": ["hello"]}])
    rc = grade.main()
    assert rc == 0
    receipt = in_tmp / "receipt.json"
    assert receipt.is_file()
    data = json.loads(receipt.read_text())
    assert data["lab"] == "test/lab"
    assert all(c["passed"] for c in data["checks"])
    # structural artifact hash recorded
    assert "a.md" in data["artifacts"]
    assert "digest" in data and "hmac" not in data
    assert "PASS" in capsys.readouterr().out


def test_main_required_fail_blocks_no_receipt(in_tmp):
    _write_manifest(in_tmp, [{"name": "art", "type": "structural", "file": "missing.md"}])
    rc = grade.main()
    assert rc == 1
    assert not (in_tmp / "receipt.json").exists()


def test_main_no_receipt_flag(in_tmp, monkeypatch):
    (in_tmp / "a.md").write_text("hello")
    _write_manifest(in_tmp, [{"name": "art", "type": "structural", "file": "a.md"}])
    # grade.main() parses sys.argv (no argv param), so drive it through argv.
    monkeypatch.setattr("sys.argv", ["grade.py", "grade.yaml", "--no-receipt"])
    assert grade.main() == 0
    assert not (in_tmp / "receipt.json").exists()


def test_main_hmac_added_when_keyed(in_tmp, monkeypatch):
    monkeypatch.setenv("GRADER_HMAC_KEY", "topsecret")
    (in_tmp / "a.md").write_text("hello")
    _write_manifest(in_tmp, [{"name": "art", "type": "structural", "file": "a.md"}])
    assert grade.main() == 0
    data = json.loads((in_tmp / "receipt.json").read_text())
    assert "hmac" in data and len(data["hmac"]) == 64


def test_main_advisory_does_not_gate(in_tmp):
    # An advisory + ai_rubric only manifest passes and writes a receipt even though
    # nothing "succeeded" in a hard sense.
    (in_tmp / "sub.md").write_text("x")
    _write_manifest(in_tmp, [
        {"name": "adv", "type": "advisory", "note": "fyi"},
        {"name": "rub", "type": "ai_rubric", "file": "sub.md"},
    ])
    assert grade.main() == 0
    assert (in_tmp / "receipt.json").exists()


def test_main_unknown_type_hard_fails(in_tmp):
    _write_manifest(in_tmp, [{"name": "bad", "type": "nonsense"}])
    assert grade.main() == 1
    assert not (in_tmp / "receipt.json").exists()


def test_main_failing_advisory_impl_never_blocks(in_tmp, monkeypatch):
    # Even if an ai_rubric's judge is configured and the artifact exists, it is advisory:
    # required defaults to False for ai_rubric, so the grade still passes.
    monkeypatch.setenv("AI_GRADER_CMD", "false")  # judge exits non-zero
    (in_tmp / "sub.md").write_text("x")
    _write_manifest(in_tmp, [{"name": "rub", "type": "ai_rubric", "file": "sub.md"}])
    assert grade.main() == 0
