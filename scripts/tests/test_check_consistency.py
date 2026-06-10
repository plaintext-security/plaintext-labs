"""Tests for check_consistency.py — prose <-> labs lockstep.

Uses synthetic tmp trees (a tiny fake plaintext/tracks + plaintext-labs) so the test is
hermetic and doesn't depend on a sibling clone. Drives main() via argv.
"""
from __future__ import annotations

import check_consistency as cc


def _make_module(tracks_root, track, module):
    d = tracks_root / track / "modules" / module
    d.mkdir(parents=True)
    (d / "README.md").write_text("# module")
    return d


def _make_lab(labs_root, track_nodigits, module, with_makefile=True):
    d = labs_root / track_nodigits / module
    d.mkdir(parents=True)
    if with_makefile:
        (d / "Makefile").write_text("up:\n\techo up\n")
    return d


def _run(monkeypatch, tracks, labs):
    monkeypatch.setattr("sys.argv",
                        ["check_consistency.py", "--tracks", str(tracks), "--labs", str(labs)])
    return cc.main()


def test_in_sync_passes(tmp_path, monkeypatch, capsys):
    tracks = tmp_path / "tracks"
    labs = tmp_path / "labs"
    _make_module(tracks, "00-foundations", "01-networking")
    _make_lab(labs, "foundations", "01-networking")
    assert _run(monkeypatch, tracks, labs) == 0
    assert "passed" in capsys.readouterr().out


def test_module_without_lab_fails(tmp_path, monkeypatch, capsys):
    tracks = tmp_path / "tracks"
    labs = tmp_path / "labs"
    _make_module(tracks, "00-foundations", "01-networking")
    (labs / "foundations").mkdir(parents=True)  # exists but no module dir
    assert _run(monkeypatch, tracks, labs) == 1
    out = capsys.readouterr().out
    assert "has no lab dir" in out


def test_lab_without_module_fails(tmp_path, monkeypatch, capsys):
    tracks = tmp_path / "tracks"
    labs = tmp_path / "labs"
    # define the track in prose so its lab-track name is recognized, but no matching module
    _make_module(tracks, "00-foundations", "01-networking")
    _make_lab(labs, "foundations", "01-networking")          # the matched pair
    _make_lab(labs, "foundations", "99-orphan")              # orphan lab, has a Makefile
    assert _run(monkeypatch, tracks, labs) == 1
    out = capsys.readouterr().out
    assert "has no module" in out
    assert "99-orphan" in out


def test_track_strip_prefix():
    assert cc.track_to_lab_dir("05-cloud") == "cloud"
    assert cc.track_to_lab_dir("00-foundations") == "foundations"


def test_missing_tracks_path_errors(tmp_path, monkeypatch):
    assert _run(monkeypatch, tmp_path / "does-not-exist", tmp_path) == 2


def test_real_tree_passes_if_present(monkeypatch, capsys):
    """If a sibling ../plaintext/tracks clone exists, the real tree must be consistent."""
    from pathlib import Path
    tracks = Path(cc.__file__).resolve().parent.parent.parent / "plaintext" / "tracks"
    labs = Path(cc.__file__).resolve().parent.parent
    if not tracks.is_dir():
        import pytest
        pytest.skip("sibling ../plaintext/tracks not present in this environment")
    assert _run(monkeypatch, tracks, labs) == 0
