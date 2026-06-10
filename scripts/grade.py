#!/usr/bin/env python3
"""Plaintext lab grader — turns a lab's "Success criteria" into executable checks.

A lab declares its checks in a `grade.yaml` manifest and exposes a `make grade` target.
Each check is one of a small set of *types* so the same grader serves every lab:

  flag              submit a secret only completion exposes; we compare its sha256
  structural        the learner's artifact exists and matches/avoids patterns (lint-ish)
  artifact_functional   run the learner's artifact and assert its exit/output
  target_state      inspect the live lab for proof (a marker written, a fix now holds)
  advisory          informational only (e.g. an AI rubric) — never fails the grade

On success the grader writes a completion receipt (JSON: lab id, timestamp, checks
passed, artifact hashes, a digest). Because this is an OPEN repo, the receipt is
self-verification + portfolio evidence, not proctoring — see docs. If GRADER_HMAC_KEY
is set, an HMAC is added so a holder of the key (e.g. a future server-side grader) can
verify it wasn't hand-edited.

Usage:
    python3 ../../scripts/grade.py grade.yaml          # grade the current lab
    FLAG=hunter2 python3 ../../scripts/grade.py grade.yaml
Exit 0 = all required checks passed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)


# --- check implementations: each returns (passed: bool, detail: str) ----------
def check_flag(c: dict) -> tuple[bool, str]:
    env_var = c.get("env", "FLAG")
    submitted = os.environ.get(env_var)
    if not submitted:
        return False, f"set {env_var}=... ({c.get('prompt', 'submit the flag')})"
    ok = sha256_text(submitted.strip()) == c["expects_sha256"]
    return ok, "flag matches" if ok else "flag does not match expected hash"


def check_structural(c: dict) -> tuple[bool, str]:
    f = Path(c["file"])
    if not f.is_file():
        return False, f"missing artifact: {f}"
    text = f.read_text(errors="replace")
    for pat in c.get("must_match", []):
        if not re.search(pat, text, re.IGNORECASE):
            return False, f"{f}: expected to find /{pat}/"
    for pat in c.get("must_not_match", []):
        if re.search(pat, text, re.IGNORECASE):
            return False, f"{f}: should not contain /{pat}/"
    if c.get("json_valid"):
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            return False, f"{f}: invalid JSON ({e})"
    return True, f"{f} present and well-formed"


def check_artifact_functional(c: dict) -> tuple[bool, str]:
    artifact = c.get("artifact")
    if artifact and not Path(artifact).is_file():
        return False, f"missing artifact: {artifact}"
    cmd = c["run"].format(artifact=artifact or "")
    try:
        proc = run(cmd, timeout=c.get("timeout", 120))
    except subprocess.TimeoutExpired:
        return False, f"timed out: {cmd}"
    if proc.returncode != c.get("expect_exit", 0):
        return False, f"exit {proc.returncode} (wanted {c.get('expect_exit', 0)}): {cmd}"
    needle = c.get("expect_stdout_contains")
    if needle and needle not in proc.stdout:
        return False, f"stdout missing {needle!r}"
    return True, "artifact ran and produced expected result"


def check_target_state(c: dict) -> tuple[bool, str]:
    try:
        proc = run(c["run"], timeout=c.get("timeout", 60))
    except subprocess.TimeoutExpired:
        return False, f"timed out: {c['run']}"
    ok = proc.returncode == c.get("expect_exit", 0)
    return ok, "target in expected state" if ok else f"check failed (exit {proc.returncode})"


def check_advisory(c: dict) -> tuple[bool, str]:
    # Informational only — surfaces a note, never fails the grade.
    return True, c.get("note", "advisory check (no automated gate)")


CHECKS = {
    "flag": check_flag,
    "structural": check_structural,
    "artifact_functional": check_artifact_functional,
    "target_state": check_target_state,
    "advisory": check_advisory,
}


def write_receipt(manifest: dict, results: list[dict], path: Path) -> None:
    payload = {
        "lab": manifest["lab"],
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "checks": [{"name": r["name"], "type": r["type"], "passed": r["passed"]}
                   for r in results],
        "artifacts": {
            c["file"]: sha256_file(Path(c["file"]))
            for c in manifest.get("checks", [])
            if c.get("type") == "structural" and Path(c.get("file", "")).is_file()
        },
        "grader_version": 1,
    }
    payload["digest"] = sha256_text(json.dumps(payload, sort_keys=True))
    key = os.environ.get("GRADER_HMAC_KEY")
    if key:
        payload["hmac"] = hmac.new(key.encode(),
                                   json.dumps(payload, sort_keys=True).encode(),
                                   hashlib.sha256).hexdigest()
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", nargs="?", default="grade.yaml")
    ap.add_argument("--no-receipt", action="store_true", help="don't write receipt.json on pass")
    args = ap.parse_args()

    manifest = yaml.safe_load(Path(args.manifest).read_text())
    print(f"Grading: {manifest['lab']}\n")

    results, hard_fail = [], False
    for c in manifest.get("checks", []):
        ctype = c.get("type")
        fn = CHECKS.get(ctype)
        if fn is None:
            print(f"  ?? {c.get('name','?')}: unknown check type {ctype!r}")
            hard_fail = True
            continue
        passed, detail = fn(c)
        required = c.get("required", ctype != "advisory")
        results.append({"name": c["name"], "type": ctype, "passed": passed})
        if passed:
            mark = "PASS"
        elif required:
            mark, hard_fail = "FAIL", True
        else:
            mark = "note"
        print(f"  [{mark}] {c['name']:32} {detail}")

    print()
    if hard_fail:
        print("Result: NOT yet complete — fix the FAILs above and re-run `make grade`.")
        return 1
    if not args.no_receipt:
        write_receipt(manifest, results, Path("receipt.json"))
        print("Result: PASS — wrote receipt.json (commit it to your portfolio repo).")
    else:
        print("Result: PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
