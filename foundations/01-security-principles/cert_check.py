#!/usr/bin/env python3
"""
cert_check.py — YOUR build. The Equifax blind spot, encoded so it can't recur.

In 2017, Equifax exfiltrated data for ~76 days without anyone noticing because
the certificate on their traffic-inspection device had EXPIRED — the detective
control was, itself, dead. Hop 3 of your autopsy is "monitor the monitors": a
cert that quietly lapses can blind your defenses.

This file is a SPEC, not a solution. Implement it yourself — have Copilot or
Claude draft it, then review every line and own the result (that's the whole
"Automate & own it" point). The reference build lives in solution/ — only open
it to CHECK your work, after yours runs.

────────────────────────────────────────────────────────────────────────
What it must do (the contract):
  * Take a hostname (default to a well-known host if none is given).
  * Open a TLS connection and read the server certificate's expiry (notAfter).
  * Print how many days remain.
  * Exit NON-ZERO if the cert is already expired OR expires within a warning
    window (default 14 days); exit 0 if it's valid and outside that window.
    -> That exit code is the point: wire it into cron/CI and a lapsing cert
       becomes a loud failure instead of a silent blind spot.

Required behavior to verify before you call it done:
  * `python3 cert_check.py expired.badssl.com`  -> FAIL (exit 1) on the expired
    cert, for the RIGHT reason (expiry — not just "handshake failed").
  * `python3 cert_check.py example.com`         -> OK (exit 0).

Suggested CLI (match this and `make cert-demo` will exercise your script):
    python3 cert_check.py                         # check a default host
    python3 cert_check.py example.com             # check a specific host
    python3 cert_check.py example.com --warn 30   # warn if < 30 days remain
    python3 cert_check.py --pem FILE              # offline: read a local PEM

Stay in the standard library: ssl + socket + datetime (+ argparse). No pip.

Hints (resist until you're stuck):
  * `ssl.create_default_context()` + `socket.create_connection()` +
    `context.wrap_socket(sock, server_hostname=host)`, then `getpeercert()`.
  * notAfter looks like "Apr  1 00:00:00 2020 GMT" — parse with
    datetime.strptime(s, "%b %d %H:%M:%S %Y %Z") and attach UTC yourself.
  * Decide what an UNREACHABLE host should do. An offline CI runner shouldn't
    fail the build — only a genuinely expired/expiring cert should.
  * Offline/deterministic path (optional, used by `make cert-demo`): parse a
    local PEM with the stdlib instead of hitting the network.

Stretch (from lab.md): accept a list of hosts and print them sorted
"soonest to expire" — the start of a real monitor-the-monitors check.
"""
from __future__ import annotations

import argparse
import socket
import ssl
import sys
from datetime import datetime, timezone

CERT_TIME_FORMAT = "%b %d %H:%M:%S %Y %Z"
DEFAULT_HOST = "example.com"
DEFAULT_WARN_DAYS = 14


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check a TLS certificate's expiry — monitor the monitors.",
    )
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST,
                        help=f"hostname to check over TLS (default: {DEFAULT_HOST})")
    parser.add_argument("--warn", type=int, default=DEFAULT_WARN_DAYS, metavar="DAYS",
                        help=f"fail if fewer than DAYS remain (default: {DEFAULT_WARN_DAYS})")
    parser.add_argument("--pem", metavar="FILE",
                        help="read a local PEM cert file instead of connecting (offline)")
    args = parser.parse_args()

    # TODO: implement the contract described in the module docstring.
    #   1. Get the certificate's notAfter (live over TLS, or from args.pem).
    #   2. Compute days remaining vs. now (UTC).
    #   3. Print the verdict and return the right exit code (0 ok / 1 fail).
    raise NotImplementedError(
        "cert_check.py is yours to build — implement main(), then run "
        "`make cert-demo`. See solution/ only to check your work."
    )


if __name__ == "__main__":
    sys.exit(main())
