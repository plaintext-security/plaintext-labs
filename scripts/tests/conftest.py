"""Shared pytest fixtures for the scripts test suite.

The scripts live in `scripts/` (one level up) and import each other by bare module
name (`track_certificate.py` does `from verify_receipt import ...`), so we put that
directory on sys.path. Tests run fully offline — no Docker, no network: the only
`run(...)` shelled out is a trivial local command the test itself supplies.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(autouse=True)
def _clean_grader_env(monkeypatch):
    """Ensure grader env knobs are unset unless a test opts in.

    GRADER_HMAC_KEY / AI_GRADER_CMD / FLAG leak across tests otherwise (and from the
    developer's own shell). Clear them by default; tests set what they need explicitly.
    """
    for var in ("GRADER_HMAC_KEY", "AI_GRADER_CMD", "FLAG"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def _clean_argv(monkeypatch):
    """Reset sys.argv so scripts' argparse-based main() don't see pytest's args.

    grade.py / validate_grade_yaml.py call main() that parse sys.argv directly; under
    pytest, argv carries the test-runner flags. Tests that need args set argv themselves.
    """
    monkeypatch.setattr("sys.argv", ["prog"])


@pytest.fixture
def in_tmp(tmp_path, monkeypatch):
    """chdir into a fresh tmp dir (the grader writes receipt.json to cwd)."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
