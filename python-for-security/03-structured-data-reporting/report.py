#!/usr/bin/env python3
"""
Reference solution: read Suricata eve.json alerts, deduplicate, filter by
severity, write CSV and render a rich table.

Input shape — real Suricata eve.json `alert` records (one JSON object each, here
as a JSON array). The fields we use:
  - top level:  timestamp, src_ip, dest_ip, dest_port, proto
  - nested under "alert":  signature, category, severity (integer)

Suricata severity is an INTEGER where LOWER = more urgent:
  1 = highest priority, 2 = medium, 3 = low.
We map those ints to HIGH/MEDIUM/LOW labels for the report and keep the most
urgent ones. Some real records are missing the nested `severity` field entirely,
so every access is defensive (`.get()`), and missing-severity records are skipped.
"""

import csv
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

DATA_FILE = Path(__file__).parent / "data" / "alerts.json"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_CSV = OUTPUT_DIR / "report.csv"

# Suricata severity int -> label. Lower int = more urgent (1 is highest).
SEVERITY_LABELS = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}
# Keep severities up to and including this threshold (remember: lower int = more
# urgent, so 3 keeps everything that HAS a severity, 1 keeps only HIGH). The
# WRCCDC scan traffic is all severity 2/3, so the default keeps it; records with
# NO severity (real eve.json has these) are always skipped.
MAX_SEVERITY_KEPT = 3
KEEP_SEVERITIES = {s for s in SEVERITY_LABELS if s <= MAX_SEVERITY_KEPT}
SEVERITY_COLORS = {1: "red", 2: "yellow", 3: "dim"}

FIELDNAMES = [
    "timestamp",
    "severity",
    "signature",
    "category",
    "src_ip",
    "dest_ip",
    "dest_port",
    "proto",
]


def severity_of(alert: dict):
    """Pull the nested Suricata severity int, or None if missing."""
    return alert.get("alert", {}).get("severity")  # Defensive: null/missing-safe


def flatten(alert: dict) -> dict:
    """Project an eve.json alert into the flat row the CSV/table want."""
    rule = alert.get("alert", {})
    sev = rule.get("severity")
    return {
        "timestamp": str(alert.get("timestamp", ""))[:19],
        "severity": SEVERITY_LABELS.get(sev, ""),
        "signature": rule.get("signature", ""),
        "category": rule.get("category", ""),
        "src_ip": alert.get("src_ip", ""),
        "dest_ip": alert.get("dest_ip", ""),
        "dest_port": alert.get("dest_port", ""),
        "proto": alert.get("proto", ""),
        "_severity_int": sev,  # kept for colour coding; ignored by CSV writer
    }


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    console = Console()

    with DATA_FILE.open() as f:
        raw_alerts = json.load(f)

    total_raw = len(raw_alerts)
    seen_fingerprints: set[tuple] = set()
    deduplicated: list[dict] = []

    for alert in raw_alerts:
        sev = severity_of(alert)
        # Skip records with no severity (real eve.json has these) and anything
        # outside the kept classes.
        if sev not in KEEP_SEVERITIES:
            continue

        rule = alert.get("alert", {})
        # Fingerprint: same rule firing on the same src/dest/port counts once.
        fp = (
            rule.get("signature", ""),
            alert.get("src_ip", ""),
            alert.get("dest_ip", ""),
            str(alert.get("dest_port", "")),
        )
        if fp in seen_fingerprints:
            continue
        seen_fingerprints.add(fp)
        deduplicated.append(flatten(alert))

    # Write CSV (extrasaction="ignore" drops the _severity_int helper field).
    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(deduplicated)

    # Render rich table
    table = Table(title="Suricata Alert Report (WRCCDC-2018)", show_lines=True)
    table.add_column("Timestamp", style="dim")
    table.add_column("Severity", justify="center")
    table.add_column("Signature", style="bold")
    table.add_column("Category")
    table.add_column("Source IP")
    table.add_column("Dest IP")
    table.add_column("Port")

    for row in deduplicated:
        color = SEVERITY_COLORS.get(row["_severity_int"], "white")
        table.add_row(
            row["timestamp"],
            f"[{color}]{row['severity']}[/{color}]",
            row["signature"],
            row["category"],
            row["src_ip"],
            row["dest_ip"],
            str(row["dest_port"]),
        )

    console.print(table)
    console.print(
        f"\n[bold]Total raw alerts:[/bold] {total_raw} → "
        f"[bold]kept (deduplicated):[/bold] {len(deduplicated)}"
    )
    console.print(f"[dim]Report written to {OUTPUT_CSV}[/dim]")


if __name__ == "__main__":
    main()
