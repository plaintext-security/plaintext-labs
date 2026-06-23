#!/usr/bin/env python3
"""
trigger.py — Fire a test alert at the n8n SOAR webhook and log the result.

Usage:
    python3 scripts/trigger.py --severity HIGH
    python3 scripts/trigger.py --severity CRITICAL
    python3 scripts/trigger.py --alert-file data/custom-alert.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "requests"], check=True)
    import requests

N8N_HOST = os.environ.get("N8N_HOST", "http://n8n:5678")
WEBHOOK_PATH = "/webhook/alert"

# Test alert payloads per severity level
TEST_ALERTS = {
    "CRITICAL": {
        "id": f"TEST-CRIT-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": "WKS-031",
        "title": "Shadow copy deletion followed by mass file encryption",
        "description": (
            "vssadmin.exe Delete Shadows /All /Quiet executed on WKS-031 by unknown process ransomware.exe. "
            "Immediately followed by 847 files renamed with .locked extension within 30 seconds. "
            "Ransom note RESTORE_FILES.txt created in each directory. Real-time protection disabled."
        ),
    },
    "HIGH": {
        "id": f"TEST-HIGH-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": "FIN-07",
        "title": "Outbound connection to known Tor exit node",
        "description": (
            "svchost.exe established an outbound TCP connection to 185.220.101.42:443 (known Tor exit node). "
            "Duration: 42 minutes. No established business justification for this IP. "
            "CrowdStrike confidence: HIGH. No prior communication with this IP from this host."
        ),
    },
    "MEDIUM": {
        "id": f"TEST-MED-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": "FIN-09",
        "title": "Unapproved browser extension with broad permissions",
        "description": (
            "Chrome extension 'PDF Converter Pro' installed by user. "
            "Extension requests access to all website data and clipboard content. "
            "Not on IT approved extension list. No malware signatures detected."
        ),
    },
    "LOW": {
        "id": f"TEST-LOW-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": "WKS-042",
        "title": "Scheduled antivirus scan completed",
        "description": (
            "CrowdStrike scheduled scan completed on WKS-042. "
            "148,223 files scanned. 0 threats detected. Duration: 47 minutes."
        ),
    },
}


def fire_webhook(alert: dict, n8n_host: str) -> dict:
    url = f"{n8n_host}{WEBHOOK_PATH}"
    print(f"POST {url}")
    print(f"Alert: [{alert['id']}] {alert['title']}")
    print()

    try:
        r = requests.post(url, json=alert, timeout=90)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot reach n8n at {n8n_host}")
        print("Is the workflow imported and active? Try: make import-workflow")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: {e}")
        print("Ensure the workflow is imported and the webhook path '/webhook/alert' is correct.")
        sys.exit(1)


def log_result(alert: dict, response: dict):
    os.makedirs("results", exist_ok=True)
    log_path = "results/audit-log.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_id": alert["id"],
        "host": alert["host"],
        "alert_title": alert["title"],
        "webhook_response": response,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Logged to {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Fire a test alert at the n8n SOAR webhook")
    parser.add_argument("--severity", choices=["CRITICAL", "HIGH", "MEDIUM", "LOW"], default="HIGH")
    parser.add_argument("--alert-file", type=str, help="Path to a custom alert JSON file")
    parser.add_argument("--n8n-host", default=N8N_HOST)
    args = parser.parse_args()

    if args.alert_file:
        with open(args.alert_file) as f:
            alert = json.load(f)
    else:
        alert = TEST_ALERTS[args.severity]

    print(f"=== Triggering SOAR Webhook ({args.severity}) ===")
    print()

    response = fire_webhook(alert, args.n8n_host)

    print("=== Workflow Response ===")
    print(json.dumps(response, indent=2))
    print()

    log_result(alert, response)


if __name__ == "__main__":
    main()
