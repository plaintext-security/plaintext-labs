"""Shared pytest fixtures for the scripts test suite.

The scripts live in `scripts/` (one level up); put that directory on sys.path so tests can import
them by bare module name. Tests run fully offline — no Docker, no network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture(autouse=True)
def _clean_argv(monkeypatch):
    """Reset sys.argv so a script's argparse-based main() doesn't see pytest's args."""
    monkeypatch.setattr("sys.argv", ["prog"])


@pytest.fixture
def in_tmp(tmp_path, monkeypatch):
    """chdir into a fresh tmp dir."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
