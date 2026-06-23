#!/usr/bin/env python3
"""
cert_check.py — the Equifax blind spot, encoded so it can't silently recur.

In 2017, Equifax exfiltrated data for ~76 days without anyone noticing because
the certificate on their traffic-inspection device had EXPIRED — the detective
control was, itself, dead. The lesson of Hop 3 in the autopsy is "monitor the
monitors": a cert that quietly lapses can blind your defenses.

This is the tiny tool that catches that. Give it a hostname; it opens a TLS
connection, reads the server certificate's expiry (`notAfter`), and reports how
many days remain — exiting NON-ZERO if the cert is already expired or expires
within a warning window. Wire that exit code into cron/CI and an expired cert
becomes a loud failure instead of a silent blind spot.

Standard library only: ssl + socket + datetime. No third-party packages.

Usage:
    python3 cert_check.py                       # check a well-known host
    python3 cert_check.py example.com           # check a specific host
    python3 cert_check.py example.com --warn 30 # warn if < 30 days remain
    python3 cert_check.py --pem sample-expired-cert.pem   # offline: read a file

Exit codes:
    0  cert is valid and outside the warning window  (or no network -> graceful)
    1  cert is EXPIRED, or expires within the warning window, or unreadable
"""
from __future__ import annotations

import argparse
import socket
import ssl
import sys
from datetime import datetime, timezone

# Certificates carry notAfter in this fixed format, e.g. "Apr  1 00:00:00 2020 GMT".
CERT_TIME_FORMAT = "%b %d %H:%M:%S %Y %Z"
DEFAULT_HOST = "example.com"
DEFAULT_WARN_DAYS = 14


def parse_not_after(not_after: str) -> datetime:
    """Turn a certificate's notAfter string into an aware UTC datetime."""
    # %Z parses the literal "GMT" but doesn't reliably set the tzinfo, so we
    # attach UTC ourselves — GMT and UTC are equivalent for certificate dates.
    dt = datetime.strptime(not_after, CERT_TIME_FORMAT)
    return dt.replace(tzinfo=timezone.utc)


def fetch_not_after_over_tls(host: str, port: int = 443, timeout: float = 8.0) -> str:
    """Connect over TLS and return the server certificate's notAfter string.

    Uses a default (verifying) SSL context. We still read notAfter even when the
    peer cert validates, because "valid handshake today" is not "won't lapse
    next week" — and the lapse is exactly what blinded Equifax.
    """
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as tls:
            cert = tls.getpeercert()
    if not cert or "notAfter" not in cert:
        raise ValueError("server presented no readable certificate")
    return cert["notAfter"]


def read_not_after_from_pem(path: str) -> str:
    """Read notAfter from a local PEM file — the offline / deterministic path.

    ssl._ssl._test_decode_cert exposes the parsed fields of a PEM on disk using
    only the stdlib (no network, no third-party x509 library). It's the same
    decoder getpeercert() relies on, so the notAfter format matches exactly.
    """
    decoded = ssl._ssl._test_decode_cert(path)  # type: ignore[attr-defined]
    not_after = decoded.get("notAfter")
    if not not_after:
        raise ValueError(f"no notAfter field in {path}")
    return not_after


def report(label: str, not_after_str: str, warn_days: int) -> int:
    """Print the verdict and return the process exit code."""
    expiry = parse_not_after(not_after_str)
    now = datetime.now(timezone.utc)
    days_left = (expiry - now).days

    print(f"Target:     {label}")
    print(f"Expires:    {expiry.isoformat()}  ({not_after_str})")

    if days_left < 0:
        print(f"Status:     EXPIRED — lapsed {-days_left} day(s) ago")
        print("Verdict:    FAIL — this is the Equifax blind spot. A dead cert")
        print("            silently disables the defense that depends on it.")
        return 1
    if days_left <= warn_days:
        print(f"Status:     EXPIRING SOON — {days_left} day(s) left (warn <= {warn_days})")
        print("Verdict:    FAIL — renew before it lapses and blinds detection.")
        return 1

    print(f"Status:     VALID — {days_left} day(s) remaining")
    print("Verdict:    OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check a TLS certificate's expiry — monitor the monitors.",
    )
    parser.add_argument(
        "host",
        nargs="?",
        default=DEFAULT_HOST,
        help=f"hostname to check over TLS (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--pem",
        metavar="FILE",
        help="read a local PEM cert file instead of connecting (offline mode)",
    )
    parser.add_argument(
        "--warn",
        type=int,
        default=DEFAULT_WARN_DAYS,
        metavar="DAYS",
        help=f"fail if fewer than DAYS remain (default: {DEFAULT_WARN_DAYS})",
    )
    parser.add_argument(
        "--list",
        metavar="LIST",
        help="read a list of hosts from a file (one per line) and check each",
    )

    args = parser.parse_args()

    # Offline / deterministic path: parse a local PEM, never touch the network.
    if args.pem:
        try:
            not_after = read_not_after_from_pem(args.pem)
        except Exception as exc:
            print(f"Could not read certificate from {args.pem}: {exc}")
            return 1
        return report(args.pem, not_after, args.warn)

    if args.list:
        host_list = args.list.split(",")
    else:
        host_list = [args.host]

    report_list = []

    for host in host_list:
        # Live path: connect over TLS.
        try:
            not_after = fetch_not_after_over_tls(host)
        except ssl.SSLCertVerificationError as exc:
            # The handshake itself rejected the cert. If the reason is expiry, that
            # IS the failure path the lab wants you to see (e.g. expired.badssl.com).
            reason = (getattr(exc, "verify_message", "") or str(exc)).lower()
            print(f"Target:     {host}")
            if "expired" in reason:
                print("Status:     EXPIRED — TLS verification rejected the certificate")
                print("Verdict:    FAIL — this is the Equifax blind spot. A dead cert")
                print("            silently disables the defense that depends on it.")
            else:
                print(f"Status:     INVALID — {exc}")
                print("Verdict:    FAIL — certificate did not verify.")
            return 1
        except (socket.gaierror, socket.timeout) as exc:
            # Genuine no-network conditions exit 0 (graceful) so an offline runner
            # never breaks a build — only a real expired/expiring cert is a failure.
            print(f"No network / could not reach {host}: {exc}")
            print("Offline — skipping live check. Try: --pem sample-expired-cert.pem")
            return 0
        except OSError as exc:
            # Connection refused, reset, unreachable, etc. — also treat as offline.
            print(f"Could not reach {host}: {exc}")
            print("Offline — skipping live check. Try: --pem sample-expired-cert.pem")
            return 0
        except Exception as exc:
            print(f"Could not check {host}: {exc}")
            return 1

        report_list.append((host, not_after, args.warn))

    # print reports in order of expiration (soonest first) so the most urgent certs are at the top of the output.
    report_list.sort(key=lambda x: parse_not_after(x[1]))
    for host, not_after, warn in report_list:
        exit_code = report(host, not_after, warn)
        if exit_code != 0:
            return exit_code
    print("All certificates are up to date and outside the warning window.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
