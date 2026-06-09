#!/usr/bin/env python3
"""
analyze_flows.py — VPC flow log anomaly detector.

Reads a VPC flow log file and reports:
  1. REJECT storms: source IPs with more than REJECT_THRESHOLD REJECT flows
     (indicator of port scanning).
  2. Large transfers: flows with byte count > LARGE_TRANSFER_BYTES to
     non-RFC-1918 destination addresses (potential exfiltration candidates).

Usage:
  python analyze_flows.py data/vpc-flow-logs.log
  python analyze_flows.py data/vpc-flow-logs.log --reject-threshold 5 --large-bytes 10000000
"""

import sys
import ipaddress
import argparse
from collections import defaultdict

# Thresholds (can be overridden via CLI flags)
DEFAULT_REJECT_THRESHOLD = 5        # REJECTs per source IP before flagging
DEFAULT_LARGE_TRANSFER_BYTES = 10_000_000  # 10 MB

# RFC-1918 private address ranges
PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Link-local (IMDS)
    ipaddress.ip_network("169.254.0.0/16"),
]


def is_private(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
        return any(addr in net for net in PRIVATE_RANGES)
    except ValueError:
        return True  # treat unparseable as internal (safe default)


def parse_flow_logs(path: str) -> list[dict]:
    """Parse VPC flow log lines into dicts. Skips comment lines and headers."""
    records = []
    fields = [
        "version", "account_id", "interface_id", "srcaddr", "dstaddr",
        "srcport", "dstport", "protocol", "packets", "bytes",
        "start", "end", "action", "log_status",
    ]
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < len(fields):
                continue
            records.append(dict(zip(fields, parts)))
    return records


def find_reject_storms(records: list[dict], threshold: int) -> list[dict]:
    """Find source IPs with >= threshold REJECT flows (port scan indicator)."""
    reject_counts = defaultdict(list)
    for r in records:
        if r.get("action") == "REJECT":
            reject_counts[r["srcaddr"]].append(r)

    storms = []
    for src_ip, flows in reject_counts.items():
        if len(flows) >= threshold:
            dst_ips = {f["dstaddr"] for f in flows}
            dst_ports = sorted({f["dstport"] for f in flows})
            storms.append({
                "source_ip": src_ip,
                "reject_count": len(flows),
                "target_ips": list(dst_ips),
                "ports_tried": dst_ports[:20],  # cap display at 20
                "is_external_source": not is_private(src_ip),
            })
    return sorted(storms, key=lambda x: x["reject_count"], reverse=True)


def find_large_transfers(records: list[dict], min_bytes: int) -> list[dict]:
    """Find large outbound flows to non-RFC-1918 destinations."""
    large = []
    for r in records:
        try:
            byte_count = int(r.get("bytes", 0))
        except ValueError:
            continue
        dst = r.get("dstaddr", "")
        src = r.get("srcaddr", "")
        # Flag: large transfer, internal source, external destination
        if byte_count >= min_bytes and is_private(src) and not is_private(dst):
            large.append({
                "source_ip": src,
                "destination_ip": dst,
                "destination_port": r.get("dstport"),
                "bytes": byte_count,
                "bytes_human": f"{byte_count / 1_000_000:.1f} MB",
                "action": r.get("action"),
                "start": r.get("start"),
                "end": r.get("end"),
            })
    return sorted(large, key=lambda x: x["bytes"], reverse=True)


def main():
    parser = argparse.ArgumentParser(description="VPC flow log anomaly detector")
    parser.add_argument("logfile", help="Path to VPC flow log file")
    parser.add_argument("--reject-threshold", type=int, default=DEFAULT_REJECT_THRESHOLD,
                        help=f"REJECT flows per source to flag (default: {DEFAULT_REJECT_THRESHOLD})")
    parser.add_argument("--large-bytes", type=int, default=DEFAULT_LARGE_TRANSFER_BYTES,
                        help=f"Byte threshold for large transfers (default: {DEFAULT_LARGE_TRANSFER_BYTES})")
    args = parser.parse_args()

    records = parse_flow_logs(args.logfile)
    print(f"Parsed {len(records)} flow log records from {args.logfile}\n")

    # --- REJECT storm detection ---
    storms = find_reject_storms(records, args.reject_threshold)
    print(f"=== Port Scan Candidates (>= {args.reject_threshold} REJECTs from same source) ===")
    if not storms:
        print("  None found.")
    for s in storms:
        external = "EXTERNAL" if s["is_external_source"] else "internal"
        print(f"  Source: {s['source_ip']} ({external})")
        print(f"    REJECT count: {s['reject_count']}")
        print(f"    Targets: {', '.join(s['target_ips'])}")
        print(f"    Ports tried: {', '.join(s['ports_tried'])}")
        print()

    # --- Large transfer detection ---
    transfers = find_large_transfers(records, args.large_bytes)
    print(f"=== Large Transfer Candidates (>= {args.large_bytes / 1_000_000:.0f} MB to external destination) ===")
    if not transfers:
        print("  None found.")
    for t in transfers:
        print(f"  Source: {t['source_ip']}  -->  Destination: {t['destination_ip']}:{t['destination_port']}")
        print(f"    Transfer size: {t['bytes_human']}  |  Action: {t['action']}")
        print(f"    Time window: {t['start']} - {t['end']}")
        print()

    total_findings = len(storms) + len(transfers)
    if total_findings > 0:
        print(f"Total findings: {total_findings} (review manually before escalating)")
        sys.exit(1)
    else:
        print("No anomalies detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
