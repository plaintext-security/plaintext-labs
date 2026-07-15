#!/usr/bin/env python3
# sift triage — the copilot's "it works" draft. This is the state of sift after
# you asked for feed triage: it reads the alert feed straight into dicts and
# trusts their shape all the way down. It behaves on data/alerts.json and
# misbehaves on data/alerts_malformed.json — some garbage sails through, some
# crashes three calls deep. Lab 02 replaces this trust with a typed boundary.
import json
import os
import sys

SEVERITY_SCORE = {"low": 1, "medium": 5, "high": 8, "critical": 10}


def load_alerts(path):
    with open(path) as f:
        return json.load(f)


def normalize(alert):
    # patch up feeds that send severity as a number instead of a name
    sev = alert.get("severity")
    if isinstance(sev, int):
        alert["severity"] = "critical" if sev >= 9 else "high"
    return alert


def enrich(alert):
    # would call VirusTotal — key pulled straight from the environment, and if
    # it's missing we just... carry on without saying so
    key = os.environ.get("SIFT_VT_API_KEY", "")
    ind = alert.get("indicator", {})
    alert["vt"] = {"checked": bool(key), "kind": ind.get("kind"), "value": ind.get("value")}
    return alert


def score(alert):
    sev = alert.get("severity", "low")            # unknown severity? call it low.
    base = SEVERITY_SCORE.get(sev, 1)
    if alert["indicator"]["kind"] == "ipv4":      # assumes the shape; never checks the value
        base += 2
    return base


def triage(alerts):
    enriched = [enrich(normalize(a)) for a in alerts]
    return sorted(enriched, key=lambda a: (-score(a), a["id"]))  # assumes id is a number


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/alerts.json"
    for a in triage(load_alerts(path)):
        ind = a.get("indicator") or {}
        print(
            f"[{a.get('severity', '?'):>8}] #{a['id']} {a.get('source', 'unknown')}: "
            f"{ind.get('kind', '?')}={ind.get('value', '?')} score={score(a)}"
        )


if __name__ == "__main__":
    main()
