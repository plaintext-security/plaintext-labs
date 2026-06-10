"""Tests for verify_receipt.py — digest + HMAC verification of a completion receipt.

We build receipts by actually running grade.py's write_receipt (the source of truth for
the digest/HMAC scheme), so verify is tested against genuinely-minted receipts, then
tamper with fields to prove it catches edits.
"""
from __future__ import annotations

import json

import grade
import verify_receipt as vr


def _mint_receipt(in_tmp, *, key=None, monkeypatch=None):
    """Mint a real receipt.json via grade.write_receipt and return its parsed dict."""
    if key is not None:
        monkeypatch.setenv("GRADER_HMAC_KEY", key)
    manifest = {"lab": "test/lab", "checks": [{"name": "c", "type": "structural", "file": "a.md"}]}
    (in_tmp / "a.md").write_text("hello")
    results = [{"name": "c", "type": "structural", "passed": True}]
    path = in_tmp / "receipt.json"
    grade.write_receipt(manifest, results, path)
    return json.loads(path.read_text())


def test_valid_receipt(in_tmp):
    data = _mint_receipt(in_tmp)
    result = vr.verify_receipt_dict(data)
    assert result.digest_ok
    assert result.valid
    assert result.all_checks_passed


def test_tampered_field_invalid(in_tmp):
    data = _mint_receipt(in_tmp)
    data["lab"] = "test/other-lab"  # edit a field without recomputing the digest
    result = vr.verify_receipt_dict(data)
    assert result.digest_ok is False
    assert result.valid is False


def test_tampered_check_status_invalid(in_tmp):
    data = _mint_receipt(in_tmp)
    data["checks"][0]["passed"] = False  # pretend a fail was a pass
    assert vr.verify_receipt_dict(data).digest_ok is False


def test_hmac_verified_when_keyed(in_tmp, monkeypatch):
    data = _mint_receipt(in_tmp, key="topsecret", monkeypatch=monkeypatch)
    assert "hmac" in data
    result = vr.verify_receipt_dict(data, key="topsecret")
    assert result.hmac_checked and result.hmac_ok and result.valid


def test_hmac_wrong_key_invalid(in_tmp, monkeypatch):
    data = _mint_receipt(in_tmp, key="topsecret", monkeypatch=monkeypatch)
    result = vr.verify_receipt_dict(data, key="wrong-key")
    assert result.hmac_checked and result.hmac_ok is False
    assert result.valid is False


def test_hmac_tampered_payload_invalid(in_tmp, monkeypatch):
    data = _mint_receipt(in_tmp, key="topsecret", monkeypatch=monkeypatch)
    data["lab"] = "edited"
    result = vr.verify_receipt_dict(data, key="topsecret")
    # digest mismatch alone makes it invalid; HMAC over edited payload also fails
    assert result.valid is False


def test_no_key_present_hmac_not_checked(in_tmp):
    data = _mint_receipt(in_tmp)
    result = vr.verify_receipt_dict(data)
    assert result.hmac_checked is False
    assert result.hmac_present is False


def test_cli_valid_returns_0(in_tmp, monkeypatch, capsys):
    _mint_receipt(in_tmp)
    monkeypatch.setattr("sys.argv", ["verify_receipt.py", str(in_tmp / "receipt.json")])
    assert vr.main() == 0
    assert "VALID" in capsys.readouterr().out


def test_cli_tampered_returns_1(in_tmp, monkeypatch, capsys):
    data = _mint_receipt(in_tmp)
    data["lab"] = "edited"
    (in_tmp / "receipt.json").write_text(json.dumps(data, indent=2))
    monkeypatch.setattr("sys.argv", ["verify_receipt.py", str(in_tmp / "receipt.json")])
    assert vr.main() == 1
    assert "INVALID" in capsys.readouterr().out


def test_cli_keyed_missing_hmac_invalid(in_tmp, monkeypatch):
    _mint_receipt(in_tmp)  # minted WITHOUT a key -> no hmac field
    monkeypatch.setenv("GRADER_HMAC_KEY", "topsecret")
    monkeypatch.setattr("sys.argv", ["verify_receipt.py", str(in_tmp / "receipt.json")])
    assert vr.main() == 1
