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
from pathlib import Path


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_receipt.py <receipt.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(sys.argv[1]).read_text())

    claimed_digest = data.pop("digest", None)
    claimed_hmac = data.pop("hmac", None)
    recomputed = sha256_text(json.dumps(data, sort_keys=True))

    ok = claimed_digest == recomputed
    print(f"Lab:        {data.get('lab')}")
    print(f"Completed:  {data.get('completed_at')}")
    passed = sum(1 for c in data.get("checks", []) if c.get("passed"))
    print(f"Checks:     {passed}/{len(data.get('checks', []))} passed")
    print(f"Digest:     {'OK — unedited' if ok else 'MISMATCH — receipt was modified'}")

    key = os.environ.get("GRADER_HMAC_KEY")
    if key:
        if claimed_hmac is None:
            print("HMAC:       missing (receipt was made without a key)")
            ok = False
        else:
            payload = dict(data)
            payload["digest"] = recomputed
            expected = hmac.new(key.encode(), json.dumps(payload, sort_keys=True).encode(),
                                hashlib.sha256).hexdigest()
            hmac_ok = hmac.compare_digest(expected, claimed_hmac)
            print(f"HMAC:       {'OK — signed by grader key' if hmac_ok else 'INVALID'}")
            ok = ok and hmac_ok
    elif claimed_hmac:
        print("HMAC:       present but not checked (set GRADER_HMAC_KEY to verify)")

    print("\nResult:", "VALID" if ok else "INVALID")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
