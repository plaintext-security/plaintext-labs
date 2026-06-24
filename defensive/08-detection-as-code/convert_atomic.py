#!/usr/bin/env python3
"""Convert Atomic Red Team T1059.001 atomics into the events.jsonl shape detect.py consumes.

This is the DEFERRED real-artifact bridge for `make fetch-data` — it is NOT run by
`make demo`/CI, only when you fetch the genuine Atomic Red Team test. It reads the
real `T1059.001.yaml` from the atomic-red-team repo, finds the atomic tests whose
command runs PowerShell with an encoded command (`-EncodedCommand` / `-enc` / `-e`),
and emits one Sysmon-shaped process-creation record per test — the same schema as
the curated `data/events.jsonl` seed — so your Sigma rule can fire on a real,
published attacker-tooling command instead of a hand-built sample.

Source / provenance: see data/PROVENANCE.md.
"""
import json
import re
import sys

import yaml

# PowerShell encoded-command flags (Sigma's T1059.001 detections key on these).
ENC_FLAG = re.compile(r"(?<!\w)-(?:enc(?:odedcommand)?|e)\b", re.IGNORECASE)
POWERSHELL = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"


def iter_encoded_tests(art_doc):
    """Yield (name, command) for atomic tests that run an encoded PowerShell command."""
    for test in art_doc.get("atomic_tests", []):
        executor = test.get("executor", {}) or {}
        command = executor.get("command", "") or ""
        # ART parameterises commands with #{...} placeholders; substitute defaults.
        for arg, spec in (test.get("input_arguments") or {}).items():
            default = "" if spec is None else str(spec.get("default", ""))
            command = command.replace("#{%s}" % arg, default)
        if ENC_FLAG.search(command):
            yield test.get("name", "<unnamed>"), command.strip()


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: convert_atomic.py <T1059.001.yaml> <out.jsonl>")

    doc = yaml.safe_load(open(sys.argv[1]))
    rows = []
    for name, command in iter_encoded_tests(doc):
        # Keep it single-line and bounded; the real encoded blob can be long.
        cmdline = " ".join(command.split())
        rows.append({
            "EventID": 1,
            "Image": POWERSHELL,
            "CommandLine": cmdline,
            "ParentImage": r"C:\Windows\System32\cmd.exe",
            "User": "CORP\\auser",
            "Computer": "WK21.corp.local",
            "_source": "Atomic Red Team T1059.001",
            "_atomic": name,
        })

    if not rows:
        sys.exit("No encoded-PowerShell atomic tests found — check the ART YAML structure.")

    with open(sys.argv[2], "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    print(f"Wrote {len(rows)} real encoded-PowerShell event(s) to {sys.argv[2]}.")


if __name__ == "__main__":
    main()
