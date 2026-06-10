"""Tests for track_certificate.py — mint / verify / badge.

Builds a portfolio of real receipts (via grade.write_receipt), mints a certificate over
them, and exercises the happy path plus the refuse-to-mint guards (edited receipt,
failing check).
"""
from __future__ import annotations

import argparse
import json

import grade
import track_certificate as tc


def _portfolio(in_tmp, n=2, *, all_pass=True, key=None, monkeypatch=None):
    """Create n per-lab receipt.json files under a portfolio dir; return that dir."""
    if key is not None:
        monkeypatch.setenv("GRADER_HMAC_KEY", key)
    root = in_tmp / "portfolio"
    for i in range(n):
        lab_dir = root / f"0{i}-module"
        lab_dir.mkdir(parents=True)
        art = lab_dir / "a.md"
        art.write_text(f"artifact {i}")
        manifest = {"lab": f"00-foundations/0{i}-module",
                    "checks": [{"name": "c", "type": "structural", "file": str(art)}]}
        results = [{"name": "c", "type": "structural", "passed": all_pass}]
        grade.write_receipt(manifest, results, lab_dir / "receipt.json")
    return root


def _mint_args(receipts, out, track="00-foundations", name="Ada Lovelace"):
    return argparse.Namespace(track=track, name=name, receipts=str(receipts), out=str(out))


def test_mint_verify_badge_happy_path(in_tmp, capsys):
    root = _portfolio(in_tmp, n=2)
    cert_path = in_tmp / "certificate.json"
    assert tc.mint(_mint_args(root, cert_path)) == 0
    assert cert_path.is_file()
    cert = json.loads(cert_path.read_text())
    assert cert["track"] == "00-foundations"
    assert cert["learner"] == "Ada Lovelace"
    assert cert["labs_completed"] == 2
    assert "digest" in cert

    # verify
    assert tc.verify(argparse.Namespace(certificate=str(cert_path))) == 0
    assert "VALID" in capsys.readouterr().out

    # badge
    svg_path = in_tmp / "badge.svg"
    assert tc.badge(argparse.Namespace(certificate=str(cert_path), out_svg=str(svg_path))) == 0
    svg = svg_path.read_text()
    assert svg.startswith("<svg")
    assert "Foundations" in svg
    assert "#3fb950" in svg  # green == valid


def test_mint_refuses_failing_receipt(in_tmp, capsys):
    root = _portfolio(in_tmp, n=1, all_pass=False)
    cert_path = in_tmp / "certificate.json"
    assert tc.mint(_mint_args(root, cert_path)) == 1
    assert not cert_path.exists()
    assert "not all checks passed" in capsys.readouterr().err


def test_mint_refuses_edited_receipt(in_tmp, capsys):
    root = _portfolio(in_tmp, n=1)
    # tamper with one receipt after minting
    rp = next(root.rglob("receipt.json"))
    data = json.loads(rp.read_text())
    data["lab"] = "edited/lab"
    rp.write_text(json.dumps(data, indent=2))
    cert_path = in_tmp / "certificate.json"
    assert tc.mint(_mint_args(root, cert_path)) == 1
    assert "digest mismatch" in capsys.readouterr().err


def test_mint_no_receipts_errors(in_tmp):
    empty = in_tmp / "empty"
    empty.mkdir()
    assert tc.mint(_mint_args(empty, in_tmp / "c.json")) == 2


def test_verify_tampered_certificate_invalid(in_tmp, capsys):
    root = _portfolio(in_tmp, n=2)
    cert_path = in_tmp / "certificate.json"
    tc.mint(_mint_args(root, cert_path))
    cert = json.loads(cert_path.read_text())
    cert["learner"] = "Mallory"  # edit without recomputing digest
    cert_path.write_text(json.dumps(cert, indent=2))
    assert tc.verify(argparse.Namespace(certificate=str(cert_path))) == 1
    assert "INVALID" in capsys.readouterr().out


def test_badge_muted_on_tampered_cert(in_tmp, capsys):
    root = _portfolio(in_tmp, n=1)
    cert_path = in_tmp / "certificate.json"
    tc.mint(_mint_args(root, cert_path))
    cert = json.loads(cert_path.read_text())
    cert["labs_completed"] = 99
    cert_path.write_text(json.dumps(cert, indent=2))
    svg_path = in_tmp / "badge.svg"
    assert tc.badge(argparse.Namespace(certificate=str(cert_path), out_svg=str(svg_path))) == 1
    assert "#8b949e" in svg_path.read_text()  # muted == invalid


def test_mint_then_verify_with_hmac(in_tmp, monkeypatch, capsys):
    root = _portfolio(in_tmp, n=2, key="k3y", monkeypatch=monkeypatch)
    cert_path = in_tmp / "certificate.json"
    assert tc.mint(_mint_args(root, cert_path)) == 0
    cert = json.loads(cert_path.read_text())
    assert "hmac" in cert
    assert tc.verify(argparse.Namespace(certificate=str(cert_path))) == 0
    out = capsys.readouterr().out
    assert "OK — signed by grader key" in out
