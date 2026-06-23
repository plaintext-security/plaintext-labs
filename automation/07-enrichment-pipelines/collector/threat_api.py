"""Threat-intel enrichment API for the pipeline lab.

Grounds verdicts in a REAL, free, no-key threat feed: abuse.ch Feodo Tracker's
IP blocklist (botnet C2 servers for Dridex, Emotet, TrickBot, QakBot, BazarLoader).
  Feed:  https://feodotracker.abuse.ch/downloads/ipblocklist.json   (no API key)
  Docs:  https://feodotracker.abuse.ch/blocklist/

On startup it fetches the live blocklist. If the runner is offline (or abuse.ch is
unreachable), it falls back to data/feodo_snapshot.json — a small committed snapshot of
real Feodo entries — so the lab is still reproducible at zero cost. Either way the verdict
is grounded in real C2 intelligence, not random.choices().

An IP on the Feodo C2 list -> "malicious" (with the real malware family + abuse_score 90+).
Anything else -> "clean" (a benign lookup the analyst can deprioritise).
"""
import json
import os
from pathlib import Path

import httpx
from flask import Flask, jsonify

FEODO_URL = os.environ.get(
    "FEODO_URL", "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
)
SNAPSHOT = Path(os.environ.get("FEODO_SNAPSHOT", "/data/feodo_snapshot.json"))

app = Flask(__name__)


def load_c2_index() -> dict:
    """Return {ip_address: entry} from the live Feodo feed, falling back to the snapshot."""
    entries = None
    try:
        resp = httpx.get(FEODO_URL, timeout=httpx.Timeout(connect=5.0, read=15.0))
        if resp.status_code == 200:
            entries = resp.json()
            print(f"[THREAT-API] Loaded {len(entries)} C2 IPs from live Feodo Tracker feed", flush=True)
    except Exception as e:  # offline runner, DNS blocked, etc.
        print(f"[THREAT-API] Live feed unavailable ({e}); using committed snapshot", flush=True)

    if entries is None:
        entries = json.loads(SNAPSHOT.read_text())
        print(f"[THREAT-API] Loaded {len(entries)} C2 IPs from snapshot {SNAPSHOT}", flush=True)

    return {e["ip_address"]: e for e in entries}


C2_INDEX = load_c2_index()


@app.route("/api/v3/ip/<ip>")
def enrich_ip(ip: str):
    hit = C2_INDEX.get(ip)
    if hit:
        return jsonify({
            "ioc": ip,
            "verdict": "malicious",
            "abuse_score": 95,
            "malware": hit.get("malware"),
            "source": "abuse.ch Feodo Tracker",
            "last_online": hit.get("last_online"),
        })
    return jsonify({"ioc": ip, "verdict": "clean", "abuse_score": 0, "source": "abuse.ch Feodo Tracker"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
