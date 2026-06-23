#!/usr/bin/env python3
"""GOOD parser — the tuned Module-02 SSH brute-force flagger.

Reads a JSONL corpus of raw auth-log lines (one {"id", "line"} object per row),
groups failed-password events by source IP, and emits a per-IP verdict as JSON:

    {"203.0.113.10": "attack", "10.0.5.20": "benign", ...}

This is the tool UNDER TEST. The eval harness (eval.py) grades these verdicts
against the held-out answer key (data/auth-labels.json). Standard library only.

Detection logic (tuned so it catches the hard cases in the corpus):
  * Matches BOTH "Failed password for <user>" and the "invalid user" variant.
  * attack if  >= BURST_THRESHOLD failures inside any WINDOW_SECONDS window
               (fast brute force), OR
               >= VOLUME_THRESHOLD failures total over the whole capture
               (the slow-and-low spray that never trips the per-minute rule).
"""
import json
import re
import sys
import datetime
import collections

# Matches "Failed password for root from 1.2.3.4" AND
#         "Failed password for invalid user oracle from 1.2.3.4".
# Requires a full dotted-quad IP, so truncated/garbage lines simply don't match.
FAILED_RE = re.compile(
    r"(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"\S+\s+sshd\[\d+\]:\s+Failed password for (?:invalid user )?(?P<user>\S+) "
    r"from (?P<ip>\d{1,3}(?:\.\d{1,3}){3}) port \d+"
)

BURST_THRESHOLD = 10      # failures inside a single window -> fast brute force
WINDOW_SECONDS = 60
VOLUME_THRESHOLD = 10     # total failures over the whole capture -> slow-and-low


def parse_ts(month: str, day: str, time_str: str) -> datetime.datetime:
    return datetime.datetime.strptime(f"2024 {month} {day} {time_str}", "%Y %b %d %H:%M:%S")


def collect_failures(corpus_path: str) -> dict[str, list[datetime.datetime]]:
    failures: dict[str, list[datetime.datetime]] = collections.defaultdict(list)
    with open(corpus_path, encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            line = record.get("line", "")
            m = FAILED_RE.search(line)
            if not m:
                continue  # non-failure or malformed line -> ignored, never crashes
            failures[m.group("ip")].append(parse_ts(m.group("month"), m.group("day"), m.group("time")))
    return failures


def is_attack(times: list[datetime.datetime]) -> bool:
    times = sorted(times)
    # Slow-and-low: enough total volume to be a deliberate spray.
    if len(times) >= VOLUME_THRESHOLD:
        return True
    # Fast burst: BURST_THRESHOLD failures inside any WINDOW_SECONDS window.
    for i, start in enumerate(times):
        in_window = [t for t in times[i:] if (t - start).total_seconds() <= WINDOW_SECONDS]
        if len(in_window) >= BURST_THRESHOLD:
            return True
    return False


def classify(corpus_path: str) -> dict[str, str]:
    failures = collect_failures(corpus_path)
    return {ip: ("attack" if is_attack(times) else "benign") for ip, times in failures.items()}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: parser_good.py <corpus.jsonl>")
    print(json.dumps(classify(sys.argv[1]), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
