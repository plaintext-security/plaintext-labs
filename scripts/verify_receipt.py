#!/usr/bin/env python3
"""Verify a Plaintext completion receipt (the T7 credential mechanism).

Recomputes the receipt's digest (and HMAC, if a key is provided) to confirm it wasn't
hand-edited, and prints a human summary. This is what a public verification page — or a
peer reviewing a portfolio — runs against a learner's committed `receipt.json`.

    python3 scripts/verify_receipt.py path/to/receipt.json
    GRADER_HMAC_KEY=... python3 scripts/verify_receipt.py receipt.json   # also check HMAC

Open-repo honesty: digest verification proves the receipt is internally consistent and
unedited, not that grading was proctored. A tamper-evident, anti-cheat credential needs the
HMAC verified with a key the learner never had (a future server-side grader).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


@dataclass
class VerifyResult:
    """Outcome of verifying a receipt's integrity (reused by track_certificate.py)."""
    digest_ok: bool
    recomputed_digest: str
    hmac_checked: bool          # whether a key was supplied to check the HMAC
    hmac_ok: bool               # only meaningful when hmac_checked
    hmac_present: bool
    all_checks_passed: bool

    @property
    def valid(self) -> bool:
        if not self.digest_ok:
            return False
        if self.hmac_checked and not self.hmac_ok:
            return False
        return True


def verify_receipt_dict(data: dict, key: str | None = None) -> VerifyResult:
    """Verify a receipt mapping (does not mutate the input).

    Recomputes the digest over the payload minus its `digest`/`hmac` fields, and — if
    `key` is given — recomputes the HMAC the grader would have written. This is the single
    source of truth for "is this receipt internally consistent and unedited"; the CLI below
    and `track_certificate.py` both call it so the scheme can never drift between them.
    """
    payload = {k: v for k, v in data.items() if k not in ("digest", "hmac")}
    claimed_digest = data.get("digest")
    claimed_hmac = data.get("hmac")
    recomputed = sha256_text(json.dumps(payload, sort_keys=True))
    digest_ok = claimed_digest == recomputed

    checks = data.get("checks", [])
    all_passed = bool(checks) and all(c.get("passed") for c in checks)

    hmac_checked = key is not None
    hmac_ok = False
    if hmac_checked and claimed_hmac is not None:
        signed = dict(payload)
        signed["digest"] = recomputed
        expected = hmac.new(key.encode(), json.dumps(signed, sort_keys=True).encode(),
                            hashlib.sha256).hexdigest()
        hmac_ok = hmac.compare_digest(expected, claimed_hmac)

    return VerifyResult(
        digest_ok=digest_ok,
        recomputed_digest=recomputed,
        hmac_checked=hmac_checked,
        hmac_ok=hmac_ok,
        hmac_present=claimed_hmac is not None,
        all_checks_passed=all_passed,
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_receipt.py <receipt.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(sys.argv[1]).read_text())

    key = os.environ.get("GRADER_HMAC_KEY")
    result = verify_receipt_dict(data, key=key)
    ok = result.digest_ok

    print(f"Lab:        {data.get('lab')}")
    print(f"Completed:  {data.get('completed_at')}")
    passed = sum(1 for c in data.get("checks", []) if c.get("passed"))
    print(f"Checks:     {passed}/{len(data.get('checks', []))} passed")
    print(f"Digest:     {'OK — unedited' if ok else 'MISMATCH — receipt was modified'}")

    if key:
        if not result.hmac_present:
            print("HMAC:       missing (receipt was made without a key)")
            ok = False
        else:
            print(f"HMAC:       {'OK — signed by grader key' if result.hmac_ok else 'INVALID'}")
            ok = ok and result.hmac_ok
    elif result.hmac_present:
        print("HMAC:       present but not checked (set GRADER_HMAC_KEY to verify)")

    print("\nResult:", "VALID" if ok else "INVALID")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
