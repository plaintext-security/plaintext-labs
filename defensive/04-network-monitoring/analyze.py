#!/usr/bin/env python3
"""Zeek log analysis: find C2 beaconing, DNS anomalies, and suspicious downloads.

Zeek turns raw PCAP into structured logs — one per protocol. This script reads
conn.log, dns.log, and http.log from a Zeek run and surfaces the attack pattern
that raw packet capture would bury. The scenario: an internal host (10.0.1.55)
was compromised and is calling home.

Usage:
    python3 analyze.py [zeek_log_dir]    # default: data/zeek/
"""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

ZEEK_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data" / "zeek"


# ── Zeek TSV parser ──────────────────────────────────────────────────────────

def parse_zeek_tsv(path: Path) -> list[dict]:
    fields: list[str] = []
    records: list[dict] = []
    for line in path.read_text().splitlines():
        if line.startswith("#fields"):
            # Strip the keyword (may be separated by tab or space)
            rest = line[len("#fields"):].lstrip("\t ")
            fields = rest.split("\t")
        elif line.startswith("#") or not line.strip():
            continue
        elif fields:
            values = line.split("\t")
            records.append(dict(zip(fields, values + [""] * (len(fields) - len(values)))))
    return records


# ── Analysis functions ───────────────────────────────────────────────────────

def detect_beaconing(conn_records: list[dict], cv_threshold: float = 0.15,
                     min_events: int = 4) -> list[dict]:
    """Find hosts making periodic connections to the same dest (C2 beacon pattern)."""
    sessions: defaultdict = defaultdict(list)
    for r in conn_records:
        try:
            ts = float(r["ts"])
            key = (r["id.orig_h"], r["id.resp_h"], r["id.resp_p"])
            sessions[key].append(ts)
        except (ValueError, KeyError):
            continue

    beacons = []
    for (src, dst, dport), timestamps in sessions.items():
        if len(timestamps) < min_events:
            continue
        timestamps.sort()
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
        if len(intervals) < 2:
            continue
        avg = mean(intervals)
        sd = stdev(intervals) if len(intervals) > 1 else 0.0
        if avg > 0 and (sd / avg) < cv_threshold:  # coefficient of variation
            beacons.append({"src": src, "dst": dst, "dport": dport,
                            "count": len(timestamps), "interval_avg": avg,
                            "interval_sd": sd})
    return beacons


def detect_dga_dns(dns_records: list[dict], min_entropy_proxy: int = 14) -> list[dict]:
    """Flag NX-domain queries for long, high-entropy hostnames (DGA-like)."""
    suspicious = []
    for r in dns_records:
        query = r.get("query", "")
        rcode = r.get("rcode", "0")
        # NX domain (rcode=3) or long subdomain (>12 chars before first dot) = DGA signal
        label = query.split(".")[0] if query else ""
        if rcode == "3" and len(label) >= min_entropy_proxy:
            suspicious.append({"query": query, "src": r.get("id.orig_h", "?"),
                                "rcode": rcode})
    return suspicious


def detect_suspicious_downloads(http_records: list[dict]) -> list[dict]:
    """Find script/executable downloads (MIME type or filename extension)."""
    BAD_EXTS = {".ps1", ".exe", ".bat", ".vbs", ".jar", ".hta", ".scr"}
    BAD_MIME = {"application/octet-stream", "application/x-executable",
                "application/x-msdos-program"}
    results = []
    for r in http_records:
        uri = r.get("uri", "")
        filename = r.get("filename", "") or r.get("resp_filenames", "")
        mime = r.get("resp_mime_types", "")
        method = r.get("method", "")
        ext = re.search(r"\.\w+$", uri)
        if (ext and ext.group().lower() in BAD_EXTS) or any(m in mime for m in BAD_MIME):
            results.append({
                "src": r.get("id.orig_h", "?"),
                "dst": r.get("id.resp_h", "?"),
                "host": r.get("host", "?"),
                "uri": uri,
                "method": method,
                "mime": mime,
                "resp_bytes": r.get("response_body_len", "?"),
            })
    return results


def detect_large_outbound(conn_records: list[dict], threshold: int = 1_000_000) -> list[dict]:
    """Flag connections with large outbound byte counts (potential exfil)."""
    results = []
    for r in conn_records:
        try:
            orig_bytes = int(r.get("orig_bytes", "0") or "0")
            if orig_bytes >= threshold:
                results.append({
                    "src": r.get("id.orig_h", "?"),
                    "dst": r.get("id.resp_h", "?"),
                    "dport": r.get("id.resp_p", "?"),
                    "orig_bytes": orig_bytes,
                    "duration": r.get("duration", "?"),
                })
        except ValueError:
            continue
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 62)
    print("SOC — Zeek Log Analysis")
    print(f"Reading logs from: {ZEEK_DIR}")
    print("=" * 62)

    conn_path = ZEEK_DIR / "conn.log"
    dns_path  = ZEEK_DIR / "dns.log"
    http_path = ZEEK_DIR / "http.log"

    conn = parse_zeek_tsv(conn_path) if conn_path.exists() else []
    dns  = parse_zeek_tsv(dns_path)  if dns_path.exists()  else []
    http = parse_zeek_tsv(http_path) if http_path.exists() else []
    print(f"Parsed: {len(conn)} conn records, {len(dns)} dns records, {len(http)} http records\n")

    # Beaconing
    beacons = detect_beaconing(conn)
    print(f"[1] Beaconing candidates ({len(beacons)} found):")
    if beacons:
        for b in beacons:
            print(f"    ⚠  {b['src']} → {b['dst']}:{b['dport']}"
                  f"  count={b['count']}"
                  f"  interval={b['interval_avg']:.0f}s ± {b['interval_sd']:.1f}s")
    else:
        print("    (none)")

    # DGA-like DNS
    dga = detect_dga_dns(dns)
    print(f"\n[2] DGA-like DNS queries ({len(dga)} found):")
    if dga:
        for d in dga:
            print(f"    ⚠  {d['src']} queried {d['query']}  (NXDOMAIN)")
    else:
        print("    (none)")

    # C2 domain in DNS
    c2_lookups = [r for r in dns if r.get("query", "").endswith(".invalid")
                  and r.get("answers", "-") not in ("-", "(empty)")]
    if c2_lookups:
        print(f"\n[3] C2 domain resolutions ({len(c2_lookups)} found):")
        seen = set()
        for r in c2_lookups:
            key = (r["query"], r.get("answers", "?"))
            if key not in seen:
                seen.add(key)
                print(f"    ⚠  {r['id.orig_h']} resolved {r['query']} → {r.get('answers','?')}")

    # Suspicious downloads
    downloads = detect_suspicious_downloads(http)
    print(f"\n[4] Suspicious downloads ({len(downloads)} found):")
    if downloads:
        for d in downloads:
            print(f"    ⚠  {d['src']} ← {d['host']}{d['uri']}"
                  f"  [{d['mime']}  {d['resp_bytes']} bytes]")
    else:
        print("    (none)")

    # Large outbound (exfil)
    exfil = detect_large_outbound(conn)
    print(f"\n[5] Large outbound transfers >{1_000_000 // 1_000_000}MB ({len(exfil)} found):")
    if exfil:
        for e in exfil:
            print(f"    ⚠  {e['src']} → {e['dst']}:{e['dport']}"
                  f"  {e['orig_bytes'] // 1024 // 1024:.1f}MB"
                  f"  duration={e['duration']}s")

    # Summary
    print("\n── Indicator summary ──────────────────────────────────────────")
    c2_ips = {b["dst"] for b in beacons} | {r.get("answers", "") for r in c2_lookups}
    c2_ips.discard("-")
    c2_ips.discard("(empty)")
    if c2_ips:
        print(f"  C2 IPs to block: {', '.join(sorted(c2_ips))}")
    c2_domains = {r["query"] for r in c2_lookups}
    if c2_domains:
        print(f"  C2 domains: {', '.join(sorted(c2_domains))}")
    print("\nNext step: check these IPs/domains against a threat intel feed (module 14)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
