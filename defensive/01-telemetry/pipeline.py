#!/usr/bin/env python3
"""Log pipeline demo: ingest → structure → search → gap analysis.

A raw log file is just text. A log *pipeline* parses it into structured records
so you can answer questions: who logged in from where, how many failures before a
success, which IPs are scanning. This script shows all three pipeline stages and
ends with a gap analysis — the question you must ask before writing a detection.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
# Prefer the real loghub OpenSSH log if `make fetch-data` has pulled it;
# otherwise fall back to the small committed seed so `make demo` works offline.
_REAL = DATA_DIR / "OpenSSH_2k.log"
LOG_PATH = _REAL if _REAL.exists() else DATA_DIR / "ssh_auth.txt"

# ── Stage 1: Ingest — raw lines ──────────────────────────────────────────────

SYSLOG_RE = re.compile(
    r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\S+)\s+(?P<host>\S+)"
    r"\s+sshd\[(?P<pid>\d+)\]:\s+(?P<message>.+)$"
)
ACCEPTED_RE = re.compile(r"Accepted (?P<method>\S+) for (?P<user>\S+) from (?P<src_ip>\S+)")
FAILED_RE   = re.compile(r"Failed \S+ for (?:invalid user )?(?P<user>\S+) from (?P<src_ip>\S+)")
INVALID_RE  = re.compile(r"Invalid user (?P<user>\S+) from (?P<src_ip>\S+)")
DISCONNECT_RE = re.compile(r"Disconnected from (?:user (?P<user>\S+) )?(?P<src_ip>\S+)")


def parse_line(raw: str) -> dict | None:
    m = SYSLOG_RE.match(raw.strip())
    if not m:
        return None
    rec = m.groupdict()
    msg = rec["message"]
    rec["event_type"] = "other"
    if am := ACCEPTED_RE.search(msg):
        rec.update(am.groupdict(), event_type="login_success")
    elif fm := FAILED_RE.search(msg):
        rec.update(fm.groupdict(), event_type="login_failure")
    elif im := INVALID_RE.search(msg):
        rec.update(im.groupdict(), event_type="invalid_user")
    elif dm := DISCONNECT_RE.search(msg):
        rec.update(dm.groupdict(), event_type="disconnect")
    return rec


# ── Stage 2: Search / query ──────────────────────────────────────────────────

def failed_logins(records: list[dict]) -> list[dict]:
    return [r for r in records if r["event_type"] in ("login_failure", "invalid_user")]


def successful_logins(records: list[dict]) -> list[dict]:
    return [r for r in records if r["event_type"] == "login_success"]


def brute_force_candidates(records: list[dict], threshold: int = 3) -> list[tuple]:
    """IPs with >= threshold failures."""
    counts: Counter = Counter()
    for r in records:
        if r["event_type"] in ("login_failure", "invalid_user"):
            counts[r.get("src_ip", "unknown")] += 1
    return [(ip, n) for ip, n in counts.most_common() if n >= threshold]


def success_after_failure(records: list[dict]) -> list[dict]:
    """Successes from IPs that also had prior failures — possible credential stuffing."""
    fail_ips = {r.get("src_ip") for r in records
                if r["event_type"] in ("login_failure", "invalid_user")}
    return [r for r in records
            if r["event_type"] == "login_success" and r.get("src_ip") in fail_ips]


# ── Stage 3: Gap analysis ────────────────────────────────────────────────────

GAPS = [
    ("Lateral movement",
     "SSH logins between internal hosts (10.x → 10.x) are visible, but we can't "
     "tell if the credential was stolen — need endpoint telemetry (auditd/EDR) on "
     "the source host to confirm whether the session came from a legitimate user process."),
    ("Exfiltration over SSH (SCP/SFTP)",
     "This sshd log records auth events but not data transfer. File transfers over "
     "SCP/SFTP don't appear here — you need either file-integrity monitoring or "
     "network flow data to catch bulk transfers."),
    ("Key-based auth abuse",
     "Accepted publickey events show the key fingerprint, but we have no mapping "
     "from fingerprint → owner in this pipeline. A compromised key looks identical "
     "to a legitimate one."),
]


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    raw_lines = LOG_PATH.read_text().splitlines()
    records = [r for line in raw_lines if (r := parse_line(line))]

    print("=" * 62)
    print("SOC — SSH Log Pipeline Demo")
    print(f"Source: {LOG_PATH.name}")
    print(f"Ingested {len(raw_lines)} raw lines → {len(records)} structured records")
    print("=" * 62)

    # Search 1: failed logins
    failures = failed_logins(records)
    print(f"\n[Query 1] Failed / invalid logins: {len(failures)}")
    ip_counts: Counter = Counter(r.get("src_ip", "?") for r in failures)
    for ip, n in ip_counts.most_common(5):
        print(f"  {ip:20s}  {n} attempts")

    # Search 2: successful logins
    successes = successful_logins(records)
    print(f"\n[Query 2] Successful logins: {len(successes)}")
    for r in successes:
        print(f"  {r['time']}  {r.get('user','?'):12s}  from {r.get('src_ip','?')}"
              f"  via {r.get('method','password')}")

    # Search 3: brute force
    bf = brute_force_candidates(records)
    print(f"\n[Query 3] Brute-force candidates (>=3 failures):")
    for ip, n in bf:
        print(f"  {ip:20s}  {n} failures")

    # Search 4: success after failure (credential stuffing signal)
    saf = success_after_failure(records)
    if saf:
        print(f"\n[Query 4] ⚠ SUCCESS after prior failures (possible credential stuffing):")
        for r in saf:
            print(f"  {r['time']}  user={r.get('user','?')}  src={r.get('src_ip','?')}"
                  f"  method={r.get('method','?')}")

    # Stage 3: gaps
    import textwrap
    print(f"\n── Telemetry gaps ──────────────────────────────────────────")
    for title, explanation in GAPS:
        print(f"\n  [GAP] {title}")
        for line in textwrap.wrap(explanation, width=60, initial_indent="        ", subsequent_indent="        "):
            print(line)

    # Emit structured output to stdout as newline-delimited JSON (what a real shipper would produce)
    out_path = Path("/tmp/pipeline_output.ndjson")
    with out_path.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print(f"\nStructured records written to {out_path} (newline-delimited JSON)")
    print("In a production pipeline, this stream would go to Elasticsearch, Loki, or Splunk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
