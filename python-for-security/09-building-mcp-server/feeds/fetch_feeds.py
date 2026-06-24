#!/usr/bin/env python3
"""
Fetch REAL threat-intel feeds from abuse.ch and build a local enrichment database.

Sources (free, no API key, real IOCs):
  * Feodo Tracker IP blocklist   https://feodotracker.abuse.ch/downloads/ipblocklist.json
        -> malicious botnet C2 IP addresses (Dridex/QakBot/Emotet/... ), with ASN/country/malware.
  * URLhaus recent URLs CSV      https://urlhaus.abuse.ch/downloads/csv_recent/
        -> recently-reported malware-distribution URLs; we derive the host IP and the
           payload's tags/malware family as the "hash-like" sample dimension.

These feeds are the real-world artifacts a SOC actually enriches against. We snapshot them
into `db.json` (committed as the OFFLINE FALLBACK) so the lab runs with no network, and the
local API server then answers `/api/v3/ip/<ip>` and `/api/v3/hash/<hash>` from that snapshot
in the same response shape the lab expects.

Provenance: every record carries `source` and `fetched_at` so the data's origin is auditable.
Run `python feeds/fetch_feeds.py` to refresh the snapshot from the live feeds.
"""

from __future__ import annotations

import csv
import datetime
import io
import ipaddress
import json
import sys
from pathlib import Path

import httpx

FEODO_URL = "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
URLHAUS_URL = "https://urlhaus.abuse.ch/downloads/csv_recent/"
DB_PATH = Path(__file__).parent / "db.json"

# A few well-known benign anchors so the corpus has guaranteed "clean" answers
# (Google / Cloudflare public resolvers) and RFC1918 examples for the report.
BENIGN_IPS = {
    "8.8.8.8": {"asn": "AS15169 Google", "country": "US"},
    "1.1.1.1": {"asn": "AS13335 Cloudflare", "country": "AU"},
    "9.9.9.9": {"asn": "AS19281 Quad9", "country": "CH"},
}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def fetch_feodo(client: httpx.Client) -> list[dict]:
    """Malicious C2 IPs from Feodo Tracker."""
    resp = client.get(FEODO_URL)
    resp.raise_for_status()
    rows = resp.json()
    out = []
    for r in rows:
        out.append(
            {
                "ip": r["ip_address"],
                "verdict": "malicious",
                "asn": f"AS{r.get('as_number', '?')} {r.get('as_name', '')}".strip(),
                "country": r.get("country", "??"),
                "malware": r.get("malware", "unknown"),
                "port": r.get("port"),
                "first_seen": r.get("first_seen"),
                "source": "abuse.ch Feodo Tracker",
            }
        )
    return out


def fetch_urlhaus(client: httpx.Client) -> tuple[list[dict], list[dict]]:
    """Malware-distribution URLs from URLhaus -> (ip records, sample records)."""
    resp = client.get(URLHAUS_URL)
    resp.raise_for_status()
    # The CSV has a multi-line comment header beginning with '#'.
    lines = [ln for ln in resp.text.splitlines() if not ln.startswith("#") and ln.strip()]
    reader = csv.reader(io.StringIO("\n".join(lines)))
    ip_records: list[dict] = []
    sample_records: list[dict] = []
    seen_ips: set[str] = set()
    for row in reader:
        # id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter
        if len(row) < 8:
            continue
        url_id, dateadded, url, url_status, _last, threat, tags, link = row[:8]
        host = url.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]
        try:
            ip = str(ipaddress.ip_address(host))
        except ValueError:
            ip = None  # host is a domain, not a literal IP; skip for the IP feed
        if ip and ip not in seen_ips:
            seen_ips.add(ip)
            ip_records.append(
                {
                    "ip": ip,
                    "verdict": "malicious",
                    "asn": "unknown",
                    "country": "??",
                    "malware": tags or threat,
                    "first_seen": dateadded,
                    "source": "abuse.ch URLhaus",
                    "urlhaus_link": link,
                }
            )
        # Each URLhaus entry doubles as a real "sample" keyed by its URLhaus id, so the
        # lab's hash endpoint has real, provenance-stamped records to enrich.
        sample_records.append(
            {
                "id": url_id,
                "verdict": "malicious",
                "threat": threat,
                "tags": tags,
                "url_status": url_status,
                "first_seen": dateadded,
                "source": "abuse.ch URLhaus",
                "urlhaus_link": link,
            }
        )
    return ip_records, sample_records


def build_db(limit_ips: int = 200, limit_samples: int = 100) -> dict:
    fetched_at = _now()
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        feodo = fetch_feodo(client)
        urlhaus_ips, urlhaus_samples = fetch_urlhaus(client)

    ips: dict[str, dict] = {}
    for rec in feodo + urlhaus_ips:
        rec["fetched_at"] = fetched_at
        ips.setdefault(rec["ip"], rec)
        if len(ips) >= limit_ips:
            break
    for ip, meta in BENIGN_IPS.items():
        ips[ip] = {
            "ip": ip,
            "verdict": "clean",
            "asn": meta["asn"],
            "country": meta["country"],
            "malware": None,
            "source": "well-known public resolver",
            "fetched_at": fetched_at,
        }

    samples: dict[str, dict] = {}
    for rec in urlhaus_samples[:limit_samples]:
        rec["fetched_at"] = fetched_at
        samples[rec["id"]] = rec

    return {
        "fetched_at": fetched_at,
        "sources": [FEODO_URL, URLHAUS_URL],
        "ips": ips,
        "samples": samples,
    }


def main() -> None:
    print("Fetching live feeds from abuse.ch (Feodo Tracker + URLhaus)...", file=sys.stderr)
    db = build_db()
    DB_PATH.write_text(json.dumps(db, indent=2))
    print(
        f"Wrote {len(db['ips'])} IP records and {len(db['samples'])} sample records "
        f"to {DB_PATH} (fetched_at={db['fetched_at']}).",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
