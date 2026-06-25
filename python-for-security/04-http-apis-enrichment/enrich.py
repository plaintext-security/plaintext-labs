#!/usr/bin/env python3
"""
Reference enrichment solution — queries the local threat-intel API (backed by REAL
abuse.ch feeds: Feodo Tracker + URLhaus) with proper timeout, retry-on-429, and
structured output. The IOCs in data/iocs.txt are real malicious IPs / URLhaus sample
ids plus known-clean public resolvers; provenance (`source`) rides along on each result.
"""

import json
import os
import re
import time
from pathlib import Path

import httpx

DATA_FILE = Path(__file__).parent / "data" / "iocs.txt"
OUTPUT_DIR = Path(__file__).parent / "output"
API_BASE = os.environ.get("THREAT_API_URL", "http://localhost:8080")

IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SAMPLE_RE = re.compile(r"^\d{4,}$")  # URLhaus sample id (numeric)


def detect_type(ioc: str) -> str:
    if IP_RE.match(ioc):
        return "ip"
    if SAMPLE_RE.match(ioc):
        return "sample"
    return "unknown"


def enrich_one(client: httpx.Client, ioc: str) -> dict:
    ioc_type = detect_type(ioc)
    if ioc_type == "unknown":
        return {"ioc": ioc, "type": "unknown", "verdict": "unknown", "error": "unrecognised format"}

    if ioc_type == "ip":
        url = f"{API_BASE}/api/v3/ip/{ioc}"
    else:
        url = f"{API_BASE}/api/v3/hash/{ioc}"

    for attempt in range(2):
        try:
            resp = client.get(url, timeout=httpx.Timeout(10.0, connect=5.0, read=10.0))
        except httpx.TimeoutException:
            return {"ioc": ioc, "type": ioc_type, "verdict": "error", "error": "timeout"}

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            return {"ioc": ioc, "type": ioc_type, "verdict": "unknown"}
        if resp.status_code == 429 and attempt == 0:
            print(f"  [429] rate-limited for {ioc}, retrying in 2s...")
            time.sleep(2)
            continue
        return {"ioc": ioc, "type": ioc_type, "verdict": "error", "error": f"http_{resp.status_code}"}

    return {"ioc": ioc, "type": ioc_type, "verdict": "rate-limited"}


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    iocs = [line.strip() for line in DATA_FILE.read_text().splitlines() if line.strip()]

    results = []
    with httpx.Client(headers={"X-API-Key": os.environ.get("VT_API_KEY", "demo-key")}) as client:
        for ioc in iocs:
            result = enrich_one(client, ioc)
            results.append(result)
            verdict = result.get("verdict", "?")
            print(f"  {ioc:<50} verdict={verdict}")

    output_file = OUTPUT_DIR / "enriched.json"
    output_file.write_text(json.dumps(results, indent=2))

    # Summary
    from collections import Counter
    counts = Counter(r.get("verdict", "?") for r in results)
    print(f"\nSummary: {dict(counts)}")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    main()
