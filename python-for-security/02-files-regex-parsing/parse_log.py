#!/usr/bin/env python3
"""
Reference solution: parse a REAL SSH auth log (loghub OpenSSH_2k.log, captured from an
internet-facing server 'LabSZ'), find brute-force sources. Standard library only.

The corpus is real, so the parser must survive real-world messiness: the "invalid user"
variant, the standalone "message repeated N times" meta-line, and assorted non-failure
lines. See data/PROVENANCE.txt for the source.
"""

import re
import collections
import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "data" / "sshd.log"

# Named-group regex for failed-password lines from real sshd output. Matches both
#   Dec 10 07:13:43 LabSZ sshd[24227]: Failed password for root from 5.36.59.76 port 42393 ssh2
# and the invalid-user variant
#   Dec 10 06:55:48 LabSZ sshd[24200]: Failed password for invalid user webmaster from 173.234.31.186 port 38926 ssh2
FAILED_RE = re.compile(
    r"(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"\S+\s+sshd\[\d+\]:\s+Failed password for (?:invalid user )?(?P<user>\S+) "
    r"from (?P<ip>\d{1,3}(?:\.\d{1,3}){3}) port \d+"
)

BRUTE_THRESHOLD = 5
WINDOW_SECONDS = 60


def parse_timestamp(month: str, day: str, time_str: str) -> datetime.datetime:
    """Parse a syslog-style timestamp; assume current year."""
    return datetime.datetime.strptime(
        f"2024 {month} {day} {time_str}", "%Y %b %d %H:%M:%S"
    )


def main() -> None:
    failures: dict[str, list[datetime.datetime]] = collections.defaultdict(list)
    counter: collections.Counter = collections.Counter()

    for line in LOG_FILE.open():
        m = FAILED_RE.search(line)
        if not m:
            continue
        ip = m.group("ip")
        ts = parse_timestamp(m.group("month"), m.group("day"), m.group("time"))
        counter[ip] += 1
        failures[ip].append(ts)

    print("=== Top 5 IPs by failed-login count ===")
    for ip, count in counter.most_common(5):
        print(f"  {ip:<20} {count:>4} failures")

    print("\n=== Brute-force sources (>= 10 failures in 60 s) ===")
    brute_sources = []
    for ip, times in failures.items():
        times_sorted = sorted(times)
        for i, t_start in enumerate(times_sorted):
            window = [t for t in times_sorted[i:] if (t - t_start).total_seconds() <= WINDOW_SECONDS]
            if len(window) >= BRUTE_THRESHOLD:
                brute_sources.append((ip, len(window), t_start))
                break

    if brute_sources:
        for ip, count, when in sorted(brute_sources, key=lambda x: -x[1]):
            print(f"  {ip:<20} {count} failures in {WINDOW_SECONDS}s window starting {when}")
    else:
        print("  (none detected)")


if __name__ == "__main__":
    main()
