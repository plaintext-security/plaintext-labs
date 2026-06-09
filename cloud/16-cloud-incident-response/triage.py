#!/usr/bin/env python3
"""
triage.py — Cloud incident response timeline builder for plaintext module 16.

Usage:
    python triage.py [cloudtrail_file] [flowlogs_file]

Parses CloudTrail JSON and VPC flow log CSV, extracts attacker-relevant events,
and prints a chronological timeline with ATT&CK phase labels, IOCs, and a
containment checklist.

Hayabusa-inspired approach: build a timeline sorted by timestamp, tag each
event with its kill-chain phase, and surface IOCs (IPs, keys, identities)
so the responder can act quickly.
"""
import csv
import json
import sys
from datetime import datetime, timezone
from collections import defaultdict

# --------------------------------------------------------------------------
# IOC catalogue — populated as we parse
# --------------------------------------------------------------------------

class IOCSet:
    def __init__(self):
        self.ips: set[str] = set()
        self.access_keys: set[str] = set()
        self.iam_principals: set[str] = set()
        self.buckets: set[str] = set()
        self.external_accounts: set[str] = set()

    def summary(self) -> str:
        lines = []
        if self.ips:
            lines.append(f"  Source IPs         : {', '.join(sorted(self.ips))}")
        if self.access_keys:
            lines.append(f"  Access keys        : {', '.join(sorted(self.access_keys))}")
        if self.iam_principals:
            lines.append(f"  IAM principals     : {', '.join(sorted(self.iam_principals))}")
        if self.buckets:
            lines.append(f"  Buckets accessed   : {', '.join(sorted(self.buckets))}")
        if self.external_accounts:
            lines.append(f"  External accounts  : {', '.join(sorted(self.external_accounts))}")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

INTERNAL_CIDR_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                           "172.20.", "172.30.", "172.31.", "192.168.", "127.")
MERIDIAN_ACCOUNT = "123456789012"

# IPs considered attacker-controlled based on incident analysis
ATTACKER_IPS = {"203.0.113.42"}

# Large transfer threshold in bytes (10 MB)
LARGE_TRANSFER_BYTES = 10_000_000

PHASE_ORDER = {
    "INITIAL_ACCESS": 1,
    "ENUMERATION": 2,
    "PRIVILEGE_ESCALATION": 3,
    "COLLECTION": 4,
    "DEFENSE_EVASION": 5,
    "EXFILTRATION": 6,
    "PERSISTENCE": 7,
    "REMEDIATION": 8,
}

PHASE_LABELS = {
    "INITIAL_ACCESS":       "Initial Access",
    "ENUMERATION":          "Enumeration",
    "PRIVILEGE_ESCALATION": "Privilege Escalation",
    "COLLECTION":           "Collection",
    "DEFENSE_EVASION":      "Defense Evasion",
    "EXFILTRATION":         "Exfiltration / Transfer",
    "PERSISTENCE":          "Persistence",
    "REMEDIATION":          "Remediation (SOC)",
}


def parse_time(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def is_external(ip: str) -> bool:
    return not any(ip.startswith(prefix) for prefix in INTERNAL_CIDR_PREFIXES)


# --------------------------------------------------------------------------
# CloudTrail parser
# --------------------------------------------------------------------------

def parse_cloudtrail(path: str, iocs: IOCSet) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    records = data.get("Records", [])

    timeline_entries = []
    for rec in records:
        ts = parse_time(rec["eventTime"])
        src_ip = rec.get("sourceIPAddress", "")
        event_name = rec.get("eventName", "")
        event_source = rec.get("eventSource", "")
        uid = rec.get("userIdentity", {})
        phase = rec.get("PHASE", "UNKNOWN")
        technique = rec.get("TECHNIQUE", "")
        note = rec.get("ANALYST_NOTE", "")

        # Collect IOCs
        if is_external(src_ip) and not src_ip.startswith("54.") and not src_ip.startswith("52."):
            # Exclude AWS service IPs (heuristic)
            iocs.ips.add(src_ip)
        key = uid.get("accessKeyId", "")
        if key:
            iocs.access_keys.add(key)
        arn = uid.get("arn", "")
        if arn:
            iocs.iam_principals.add(arn)

        params = rec.get("requestParameters") or {}
        bucket = params.get("bucketName", "")
        if bucket:
            iocs.buckets.add(bucket)

        # External account in replication
        replication = params.get("ReplicationConfiguration", {})
        for rule in replication.get("Rules", []):
            dest_account = rule.get("Destination", {}).get("Account", "")
            if dest_account and dest_account != MERIDIAN_ACCOUNT:
                iocs.external_accounts.add(dest_account)

        timeline_entries.append({
            "ts": ts,
            "phase": phase,
            "technique": technique,
            "event_name": event_name,
            "event_source": event_source,
            "principal": uid.get("arn", uid.get("type", "?")),
            "src_ip": src_ip,
            "note": note,
            "params_summary": _summarize_params(params),
        })

    return timeline_entries


def _summarize_params(params: dict) -> str:
    if not params:
        return ""
    parts = []
    for key in ("roleArn", "userName", "bucketName", "key", "policyArn",
                "name", "accessKeyId", "groupId", "status"):
        val = params.get(key)
        if val:
            parts.append(f"{key}={val}")
    # Check for replication destination
    replication = params.get("ReplicationConfiguration", {})
    for rule in replication.get("Rules", []):
        dest = rule.get("Destination", {}).get("Bucket", "")
        if dest:
            parts.append(f"replication_dest={dest}")
    return " | ".join(parts)


# --------------------------------------------------------------------------
# VPC flow log parser
# --------------------------------------------------------------------------

def parse_flowlogs(path: str, iocs: IOCSet) -> list[dict]:
    entries = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f, delimiter=" ")
        for row in reader:
            src = row.get("srcaddr", "")
            dst = row.get("dstaddr", "")
            bytes_count = int(row.get("bytes", 0))
            action = row.get("action", "")
            start_ts = int(row.get("start", 0))
            dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)

            # Flag flows to/from attacker IPs with large byte counts
            involves_attacker = src in ATTACKER_IPS or dst in ATTACKER_IPS
            is_large = bytes_count >= LARGE_TRANSFER_BYTES

            if involves_attacker or is_large:
                direction = "OUT" if src.startswith("10.") else "IN"
                note = ""
                if involves_attacker and is_large and direction == "OUT":
                    note = "LARGE OUTBOUND to known attacker IP — potential data exfiltration"
                    iocs.ips.add(src if not src.startswith("10.") else dst)
                elif is_large and not involves_attacker:
                    note = "Large transfer (possible data movement)"

                entries.append({
                    "ts": dt,
                    "phase": "EXFILTRATION" if involves_attacker and direction == "OUT" else "NETWORK",
                    "technique": "T1537" if involves_attacker and direction == "OUT" else "",
                    "src": src,
                    "dst": dst,
                    "bytes": bytes_count,
                    "direction": direction,
                    "action": action,
                    "note": note,
                })

    return entries


# --------------------------------------------------------------------------
# Timeline renderer
# --------------------------------------------------------------------------

def print_timeline(ct_entries: list[dict], flow_entries: list[dict]) -> None:
    # Merge and sort
    all_entries = []
    for e in ct_entries:
        all_entries.append(("cloudtrail", e))
    for e in flow_entries:
        all_entries.append(("flowlog", e))
    all_entries.sort(key=lambda x: x[1]["ts"])

    print("=" * 72)
    print("  MERIDIAN FINANCIAL — INCIDENT TIMELINE")
    print("  Source: CloudTrail + VPC Flow Logs")
    print("=" * 72)

    current_phase = None
    for source, entry in all_entries:
        phase = entry.get("phase", "UNKNOWN")
        if phase != current_phase:
            current_phase = phase
            label = PHASE_LABELS.get(phase, phase)
            print()
            print(f"  ── {label} ──────────────────────────────")

        if source == "cloudtrail":
            tech = f"[{entry['technique']}]" if entry.get("technique") else ""
            print(
                f"  {fmt_dt(entry['ts'])}  {entry['event_name']:<35} {tech}"
            )
            print(f"    Principal : {entry['principal']}")
            print(f"    Source IP : {entry['src_ip']}")
            if entry.get("params_summary"):
                print(f"    Params    : {entry['params_summary']}")
            if entry.get("note"):
                print(f"    >>> {entry['note']}")
        else:
            flag = "  *** " if entry.get("note") else "      "
            print(
                f"  {fmt_dt(entry['ts'])}  VPC FLOW {entry['direction']:<4}  "
                f"{entry['src']:>15} → {entry['dst']:<15}  "
                f"{entry['bytes']:>12,} B  {entry['action']}"
            )
            if entry.get("note"):
                print(f"    {flag}{entry['note']}")


# --------------------------------------------------------------------------
# IOC and containment report
# --------------------------------------------------------------------------

def print_ioc_report(iocs: IOCSet) -> None:
    print()
    print("=" * 72)
    print("  INDICATORS OF COMPROMISE (IOCs)")
    print("=" * 72)
    print(iocs.summary())


def print_containment_checklist(iocs: IOCSet) -> None:
    print()
    print("=" * 72)
    print("  CONTAINMENT CHECKLIST")
    print("=" * 72)
    for key in sorted(iocs.access_keys):
        print(f"  [ ] Disable/delete access key: {key}")
    for account in sorted(iocs.external_accounts):
        print(f"  [ ] Remove S3 replication rules pointing to account: {account}")
    for ip in sorted(iocs.ips):
        print(f"  [ ] Block IP in security groups / WAF / network ACL: {ip}")
    print("  [ ] Re-enable CloudTrail logging if StopLogging was called")
    print("  [ ] Rotate all credentials for affected IAM principals")
    print("  [ ] Audit S3 bucket policies and replication config on all buckets")
    print("  [ ] Review GuardDuty and CloudTrail for additional lateral movement")
    print("  [ ] Notify legal / privacy team if PII buckets were accessed")
    print()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ct_file = sys.argv[1] if len(sys.argv) > 1 else "data/cloudtrail/incident.json"
    flow_file = sys.argv[2] if len(sys.argv) > 2 else "data/vpc/flowlogs.csv"

    iocs = IOCSet()
    ct_entries = parse_cloudtrail(ct_file, iocs)
    flow_entries = parse_flowlogs(flow_file, iocs)

    print_timeline(ct_entries, flow_entries)
    print_ioc_report(iocs)
    print_containment_checklist(iocs)


if __name__ == "__main__":
    main()
