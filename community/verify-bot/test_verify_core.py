#!/usr/bin/env python3
"""Tests for verify_core — the pure verification math behind the verify-bot.

No network or Discord; run with `python3 test_verify_core.py` (or pytest).
"""
import hashlib
import json

import verify_core as vc


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def receipt(lab: str, passed: bool = True, tamper: bool = False) -> dict:
    p = {
        "lab": lab,
        "completed_at": "2026-06-10T12:00:00+00:00",
        "checks": [{"name": "c1", "type": "structural", "passed": passed}],
        "artifacts": {},
        "grader_version": 1,
    }
    p["digest"] = sha(json.dumps(p, sort_keys=True))
    if tamper:
        p["lab"] = lab + "-HACKED"  # edited after the digest was computed
    return p


def test_capstone_completes_track_and_grants_roles():
    out = vc.evaluate([
        receipt("defensive/07-log-parsing"),
        receipt("defensive/08-detection-as-code"),
        receipt("defensive/capstone"),
    ])
    assert out.valid_count == 3
    assert out.per_track["defensive"].complete is True
    assert out.earned_roles == ["Plaintext Verified", "Defensive ✓"]


def test_modules_without_capstone_do_not_complete():
    out = vc.evaluate([receipt("foundations/04-linux"), receipt("foundations/06-networking")])
    assert out.per_track["foundations"].modules_done == 2
    assert out.per_track["foundations"].complete is False
    assert out.earned_roles == []


def test_tampered_and_failed_and_unknown_are_skipped():
    out = vc.evaluate([
        receipt("offensive/06-web-injection", tamper=True),
        receipt("cloud/01-iam", passed=False),
        receipt("bogus/01-x"),
    ])
    assert out.valid_count == 0
    assert out.per_track == {}
    assert any("digest mismatch" in s for s in out.skipped)
    assert any("checks not all passed" in s for s in out.skipped)
    assert any("unknown track" in s for s in out.skipped)


def test_hmac_required_when_key_supplied():
    # A receipt with no HMAC must NOT count when a key is supplied (anti-cheat mode).
    out = vc.evaluate([receipt("defensive/capstone")], hmac_key="secret")
    assert out.valid_count == 0
    assert any("HMAC invalid" in s for s in out.skipped)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} tests passed")


if __name__ == "__main__":
    _run_all()
