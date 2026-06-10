"""Tests for validate_grade_yaml.py — the grade.yaml schema linter."""
from __future__ import annotations

from pathlib import Path

import validate_grade_yaml as vg


def _write(tmp_path, content):
    p = tmp_path / "grade.yaml"
    p.write_text(content)
    return p


def test_valid_manifest_each_type(tmp_path):
    p = _write(tmp_path, """
lab: test/lab
checks:
  - name: flag-check
    type: flag
    expects_sha256: "abc"
  - name: struct-check
    type: structural
    file: out.md
  - name: func-check
    type: artifact_functional
    run: "python3 x.py"
  - name: state-check
    type: target_state
    run: "true"
  - name: adv-check
    type: advisory
    note: "fyi"
  - name: rubric-check
    type: ai_rubric
    file: sub.md
""")
    assert vg.validate_file(p) == []


def test_missing_lab(tmp_path):
    p = _write(tmp_path, "checks:\n  - name: c\n    type: advisory\n")
    errs = vg.validate_file(p)
    assert any("lab" in e for e in errs)


def test_missing_checks(tmp_path):
    p = _write(tmp_path, "lab: test/lab\n")
    errs = vg.validate_file(p)
    assert any("checks" in e for e in errs)


def test_empty_checks_list(tmp_path):
    p = _write(tmp_path, "lab: test/lab\nchecks: []\n")
    assert any("checks" in e for e in vg.validate_file(p))


def test_unknown_type(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: bogus\n")
    assert any("unknown type" in e for e in vg.validate_file(p))


def test_flag_missing_expects_sha256(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: flag\n")
    assert any("expects_sha256" in e for e in vg.validate_file(p))


def test_structural_missing_file(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: structural\n")
    assert any("`file`" in e for e in vg.validate_file(p))


def test_artifact_functional_missing_run(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: artifact_functional\n")
    assert any("`run`" in e for e in vg.validate_file(p))


def test_target_state_missing_run(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: target_state\n")
    assert any("`run`" in e for e in vg.validate_file(p))


def test_ai_rubric_missing_file(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: ai_rubric\n")
    assert any("`file`" in e for e in vg.validate_file(p))


def test_check_missing_name(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - type: advisory\n")
    assert any("name" in e for e in vg.validate_file(p))


def test_check_missing_type(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n")
    assert any("type" in e for e in vg.validate_file(p))


def test_required_must_be_bool(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: advisory\n    required: maybe\n")
    assert any("required" in e for e in vg.validate_file(p))


def test_wrong_field_type(tmp_path):
    # file should be a string, not a list
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: structural\n    file: [a, b]\n")
    assert any("`file` must be str" in e for e in vg.validate_file(p))


def test_invalid_yaml(tmp_path):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n   bad indent: x\n")
    assert any("invalid YAML" in e for e in vg.validate_file(p))


def test_empty_file(tmp_path):
    p = _write(tmp_path, "")
    assert any("empty" in e for e in vg.validate_file(p))


def test_top_level_not_mapping(tmp_path):
    p = _write(tmp_path, "- just\n- a\n- list\n")
    assert any("mapping" in e for e in vg.validate_file(p))


def test_main_on_clean_file_returns_0(tmp_path, monkeypatch):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: advisory\n")
    monkeypatch.setattr("sys.argv", ["validate_grade_yaml.py", str(p)])
    assert vg.main() == 0


def test_main_on_bad_file_returns_1(tmp_path, monkeypatch):
    p = _write(tmp_path, "lab: l\nchecks:\n  - name: c\n    type: flag\n")
    monkeypatch.setattr("sys.argv", ["validate_grade_yaml.py", str(p)])
    assert vg.main() == 1


def test_main_scans_real_repo(monkeypatch, capsys):
    """The real repo's grade.yaml manifests must all validate."""
    repo_root = Path(vg.__file__).resolve().parent.parent
    monkeypatch.setattr("sys.argv", ["validate_grade_yaml.py", "--root", str(repo_root)])
    rc = vg.main()
    out = capsys.readouterr().out
    assert "Validation passed" in out
    assert rc == 0
