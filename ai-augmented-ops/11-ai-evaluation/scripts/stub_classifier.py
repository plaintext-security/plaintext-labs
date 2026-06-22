#!/usr/bin/env python3
"""
stub_classifier.py — a TINY, DETERMINISTIC stand-in for the real triage model.

This exists so the eval loop runs end-to-end offline, with no live LLM: it reads the held-out
corpus and emits a predictions.json in the same shape your real model would. It is a crude
keyword/heuristic classifier on purpose — good enough to be non-trivially right and non-trivially
wrong, so the scorecard has something to say.

HONESTY NOTE: this is NOT how you'd classify alerts in production. In real use you delete this and
plug in your Module-07 triage model (or any classifier); the corpus, eval.py, the scorecard, and
the gate are unchanged. The stub keeps the *measurement* machinery runnable and deterministic in CI
while you develop the *system* separately.

Usage:
  python3 scripts/stub_classifier.py --corpus data/triage-heldout.jsonl --out results/predictions-stub.json
"""

import argparse
import json
import os

# Tokens that, in this corpus, lean malicious vs. benign. Deliberately imperfect.
MALICIOUS_HINTS = [
    "-enc", "-encodedcommand", "downloadstring", "iex", "mshta", "certutil -decode",
    "vssadmin", "delete shadows", "lsass", "minidump", "dcsync", "getncchanges",
    "wdigest", "ntlmv1", "impossible travel", "rclone", "mega.nz", "bcp", "domain admins",
    "rdp from any", "tcp 3389 from any", "no ticket", "not approved", "unknown binary",
    "no business use", "off-hours", "downgrade",
]
BENIGN_HINTS = [
    "approved", "signed by", "scheduled", "matches the", "routine", "self-service",
    "maintenance window", "wsus", "sccm", "exit 0", "no anomalies", "no security",
    "operational event", "matching jira", "matching support ticket", "recorded session",
    "policy-compliant", "expected", "current stable", "heartbeat", "nominal",
]


def classify(text: str) -> str:
    t = text.lower()
    mal = sum(1 for h in MALICIOUS_HINTS if h in t)
    ben = sum(1 for h in BENIGN_HINTS if h in t)
    # Bias toward 'malicious' on a tie — the security-correct default (miss nothing for free).
    return "malicious" if mal >= ben and mal > 0 else "benign"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/triage-heldout.jsonl")
    ap.add_argument("--out", default="results/predictions-stub.json")
    args = ap.parse_args()

    preds = {}
    with open(args.corpus) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            blob = f"{item.get('title','')} {item.get('description','')}"
            preds[item["id"]] = classify(blob)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(preds, f, indent=2)
    print(f"Wrote {len(preds)} predictions to {args.out} (deterministic stub — swap for your real model).")


if __name__ == "__main__":
    main()
