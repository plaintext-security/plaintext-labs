"""
Local threat-intel API backed by REAL abuse.ch feeds.

This is NOT a synthetic verdict generator. It serves the snapshot in
`feeds/db.json`, which is built from two real, free, no-key feeds:
  * abuse.ch Feodo Tracker  (malicious botnet C2 IPs: Emotet / QakBot / Dridex ...)
  * abuse.ch URLhaus        (recently-reported malware-distribution URLs / samples)

It mirrors a VirusTotal/AbuseIPDB-style API so the lab's HTTP/retry/auth patterns are
realistic, but the verdicts and IOCs are genuine threat intel with provenance
(`source`, `fetched_at`, and for URLhaus the `urlhaus_link`). Refresh the snapshot with
`python feeds/fetch_feeds.py`; the committed snapshot keeps the lab runnable offline.

Two real malicious IPs return HTTP 429 once before succeeding, to exercise retry logic.
"""

from pathlib import Path
import json

from flask import Flask, jsonify

app = Flask(__name__)

DB_PATH = Path("/feeds/db.json")
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent.parent / "feeds" / "db.json"

DB = json.loads(DB_PATH.read_text())
IP_DATA: dict[str, dict] = DB["ips"]
SAMPLE_DATA: dict[str, dict] = DB["samples"]

# Two real C2 IPs from the snapshot that we 429 once, to force retry handling.
# Picked deterministically from the loaded feed so the behaviour is stable.
_malicious_ips = [ip for ip, rec in IP_DATA.items() if rec.get("verdict") == "malicious"]
RATE_LIMITED = set(_malicious_ips[:2])
_retry_counts: dict[str, int] = {}


@app.route("/api/v3/ip/<ip>")
def enrich_ip(ip: str):
    if ip in RATE_LIMITED:
        if _retry_counts.get(ip, 0) == 0:
            _retry_counts[ip] = 1
            return jsonify({"error": "rate limited"}), 429

    rec = IP_DATA.get(ip)
    if rec is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"ioc": ip, "type": "ip", **rec})


@app.route("/api/v3/hash/<sample_id>")
def enrich_hash(sample_id: str):
    # In this real-feed build a "hash" is a URLhaus sample id (the feed does not ship
    # file hashes for these payloads). The lab's IOC list uses these real ids.
    rec = SAMPLE_DATA.get(sample_id)
    if rec is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"ioc": sample_id, "type": "sample", **rec})


@app.route("/api/v3/meta")
def meta():
    """Provenance endpoint: where the data came from and when."""
    return jsonify(
        {
            "sources": DB.get("sources", []),
            "fetched_at": DB.get("fetched_at"),
            "ip_count": len(IP_DATA),
            "sample_count": len(SAMPLE_DATA),
            "rate_limited_ips": sorted(RATE_LIMITED),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
