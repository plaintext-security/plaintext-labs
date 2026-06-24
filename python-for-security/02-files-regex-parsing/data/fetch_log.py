#!/usr/bin/env python3
"""
Fetch a REAL public SSH authentication-log corpus for the parsing lab.

Source: loghub — a curated collection of real system logs used in log-analysis research.
        OpenSSH_2k.log is 2,000 lines captured from a real internet-facing SSH server
        ("LabSZ"), full of genuine brute-force / invalid-user campaigns from real source IPs.
        https://github.com/logpai/loghub  (file: OpenSSH/OpenSSH_2k.log)

This is the real artifact a SOC analyst actually parses — not a synthesised log. The lab ships
a small committed excerpt (`sshd.log`) as the OFFLINE FALLBACK so it runs with no network; run
`python data/fetch_log.py` to pull the full 2,000-line corpus into `sshd.log`.

Provenance is written to `data/PROVENANCE.txt` (source URL + retrieval date).
"""

from __future__ import annotations

import datetime
from pathlib import Path

import urllib.request

URL = "https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log"
HERE = Path(__file__).parent
OUT = HERE / "sshd.log"
PROV = HERE / "PROVENANCE.txt"


def main() -> None:
    print(f"Fetching real OpenSSH auth-log corpus from {URL} ...")
    with urllib.request.urlopen(URL, timeout=30) as resp:  # noqa: S310 (trusted public corpus)
        data = resp.read().decode("utf-8", errors="replace")
    OUT.write_text(data)
    n = data.count("\n")
    PROV.write_text(
        "Source: loghub OpenSSH_2k.log (real internet-facing SSH server 'LabSZ')\n"
        f"URL: {URL}\n"
        f"Retrieved: {datetime.date.today().isoformat()}\n"
        f"Lines: {n}\n"
        "License/terms: loghub research dataset, see https://github.com/logpai/loghub\n"
    )
    print(f"Wrote {n} lines to {OUT}; provenance in {PROV}.")


if __name__ == "__main__":
    main()
