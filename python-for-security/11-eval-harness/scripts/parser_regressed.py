#!/usr/bin/env python3
"""REGRESSED parser — the SAME tool with one rule quietly weakened.

A teammate "simplified" the detector: they DROPPED the total-volume fallback and
kept ONLY the strict per-minute burst rule. The unit tests still pass and the
demo log still lights up, so the change looks harmless. But it now UNDER-DETECTS:
the slow-and-low spray from 198.51.100.7 (12 failures spread over ~17 minutes,
never 10 inside any 60s window) is silently marked "benign" — a false "all clear"
on a real attack. That dropped recall is exactly what the eval gate must catch.

Diff vs. parser_good.py: `is_attack()` no longer checks VOLUME_THRESHOLD.
"""
import json
import re
import sys
import datetime
import collections

FAILED_RE = re.compile(
    r"(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"\S+\s+sshd\[\d+\]:\s+Failed password for (?:invalid user )?(?P<user>\S+) "
    r"from (?P<ip>\d{1,3}(?:\.\d{1,3}){3}) port \d+"
)

BURST_THRESHOLD = 10
WINDOW_SECONDS = 60


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
            m = FAILED_RE.search(record.get("line", ""))
            if not m:
                continue
            failures[m.group("ip")].append(parse_ts(m.group("month"), m.group("day"), m.group("time")))
    return failures


def is_attack(times: list[datetime.datetime]) -> bool:
    times = sorted(times)
    # REGRESSION: the slow-and-low (total-volume) fallback was removed here.
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
        sys.exit("usage: parser_regressed.py <corpus.jsonl>")
    print(json.dumps(classify(sys.argv[1]), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
