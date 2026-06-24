#!/usr/bin/env python3
"""
Reference MISP workflow: create event → add attributes → enrich → tag → publish.
Uses direct HTTP (requests) against the mock MISP/VT APIs.
"""

import os
import re
from pathlib import Path

import requests

MISP_URL = os.environ.get("MISP_URL", "http://localhost:8080")
MISP_KEY = os.environ.get("MISP_KEY", "demo-misp-key")
VT_URL   = os.environ.get("VT_URL", "http://localhost:8081")

DATA_FILE = Path(__file__).parent / "data" / "iocs.txt"

IP_RE   = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
SAMPLE_RE = re.compile(r"^\d{4,}$")  # URLhaus sample id (numeric)

SESSION = requests.Session()
SESSION.headers.update({"Authorization": MISP_KEY, "Content-Type": "application/json", "Accept": "application/json"})


def detect_attr_type(ioc: str) -> str:
    if IP_RE.match(ioc):
        return "ip-dst"
    if SAMPLE_RE.match(ioc):
        return "other"  # URLhaus payload reference (real malware-distribution sample)
    return "other"


def enrich_ioc(ioc: str, ioc_type: str) -> str:
    try:
        if ioc_type == "ip-dst":
            r = requests.get(f"{VT_URL}/api/v3/ip_addresses/{ioc}", timeout=5)
        else:
            r = requests.get(f"{VT_URL}/api/v3/files/{ioc}", timeout=5)
        if r.status_code == 200:
            stats = r.json()["data"]["attributes"]["last_analysis_stats"]
            malicious = stats.get("malicious", 0)
            total = sum(stats.values())
            return f"VT: {malicious}/{total} engines malicious"
        return "VT: not found"
    except Exception as e:
        return f"VT: error ({e})"


def main() -> None:
    iocs = [l.strip() for l in DATA_FILE.read_text().splitlines() if l.strip()]

    # 1. Create event
    event_payload = {
        "info": "Phishing campaign — abuse.ch-sourced IOCs",
        "threat_level_id": "2",
        "analysis": "1",
        "distribution": "0",
    }
    r = SESSION.post(f"{MISP_URL}/events", json={"Event": event_payload})
    r.raise_for_status()
    event = r.json()["Event"]
    event_id = event["id"]
    print(f"[+] Created MISP event {event_id}: {event['info']}")

    # 2. Add attributes with enrichment
    for ioc in iocs:
        attr_type = detect_attr_type(ioc)
        comment = enrich_ioc(ioc, attr_type)
        attr_payload = {
            "type": attr_type,
            "value": ioc,
            "category": "Network activity" if attr_type == "ip-dst" else "Payload delivery",
            "comment": comment,
            "to_ids": True,
        }
        SESSION.post(f"{MISP_URL}/attributes/add/{event_id}", json={"Attribute": attr_payload})
        print(f"  + {ioc:<50} type={attr_type:<12} {comment}")

    # 3. Tag event
    for tag_name in ["tlp:amber", "misp-galaxy:mitre-attack-pattern=\"Phishing T1566\""]:
        SESSION.post(f"{MISP_URL}/tags/attachTagToObject/{event_id}/Event", json={"name": tag_name})
    print(f"[+] Tagged event with tlp:amber and ATT&CK Phishing")

    # 4. Publish
    SESSION.post(f"{MISP_URL}/events/publish/{event_id}")
    print(f"[+] Published event: {MISP_URL}/events/{event_id}")

    # 5. Verify: query by tag
    r = SESSION.post(f"{MISP_URL}/events/index", json={"tag": "tlp:amber"})
    matched = r.json()
    print(f"[+] Query by tlp:amber returned {len(matched)} event(s)")


if __name__ == "__main__":
    main()
