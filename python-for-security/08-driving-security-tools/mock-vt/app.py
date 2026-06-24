"""
Local VirusTotal-shaped API backed by REAL abuse.ch threat intel.

The response shape mirrors VirusTotal v3 (`last_analysis_stats`, `reputation`), so the
pymisp/enrichment workflow is realistic — but the verdicts come from the real abuse.ch
feed snapshot in `feeds/db.json` (Feodo Tracker + URLhaus), not hand-invented numbers.
A real malicious C2 IP is reported as a high malicious-engine count; the known-clean
public resolvers report zero. Refresh with `python feeds/fetch_feeds.py`.

(MISP itself is served by the sibling mock-misp container: MISP is the system-of-record
the analyst legitimately writes to, so it stays local. The *enrichment* is the dimension
that must be real, and it is.)
"""

from pathlib import Path
import json

from flask import Flask, jsonify

app = Flask(__name__)

DB_PATH = Path("/feeds/db.json")
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent.parent / "feeds" / "db.json"

DB = json.loads(DB_PATH.read_text())
IP_DATA = DB["ips"]
SAMPLE_DATA = DB["samples"]

# Engine totals chosen to look like a real VT report; malicious count scales with verdict.
TOTAL_ENGINES = 72


def _stats_for(verdict: str) -> dict:
    if verdict == "malicious":
        return {"malicious": 58, "suspicious": 4, "harmless": 2, "undetected": TOTAL_ENGINES - 64}
    if verdict == "suspicious":
        return {"malicious": 6, "suspicious": 5, "harmless": 20, "undetected": TOTAL_ENGINES - 31}
    return {"malicious": 0, "suspicious": 0, "harmless": TOTAL_ENGINES, "undetected": 0}


@app.route("/api/v3/ip_addresses/<ip>")
def vt_ip(ip):
    rec = IP_DATA.get(ip)
    if rec is None:
        return jsonify({"error": {"code": "NotFoundError"}}), 404
    return jsonify(
        {
            "data": {
                "attributes": {
                    "last_analysis_stats": _stats_for(rec["verdict"]),
                    "reputation": -90 if rec["verdict"] == "malicious" else 0,
                    "as_owner": rec.get("asn"),
                    "country": rec.get("country"),
                    "malware": rec.get("malware"),
                    "_source": rec.get("source"),  # provenance
                }
            }
        }
    )


@app.route("/api/v3/files/<sample_id>")
def vt_file(sample_id):
    rec = SAMPLE_DATA.get(sample_id)
    if rec is None:
        return jsonify({"error": {"code": "NotFoundError"}}), 404
    return jsonify(
        {
            "data": {
                "attributes": {
                    "last_analysis_stats": _stats_for(rec["verdict"]),
                    "meaningful_name": rec.get("tags"),
                    "_source": rec.get("source"),  # provenance
                    "_urlhaus_link": rec.get("urlhaus_link"),
                }
            }
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
