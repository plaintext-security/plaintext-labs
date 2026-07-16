#!/usr/bin/env python3
# sift triage — the copilot's "it works" draft. This is the state of sift after
# you asked for Suricata EVE triage: it reads eve.json line by line straight into
# dicts and trusts their shape all the way down. It behaves on data/eve.json and
# misbehaves on data/eve_malformed.json — some garbage sails through, some crashes
# three calls deep, and a truncated line takes out the whole run. Lab 02 replaces
# this trust with a typed boundary.
import json
import os
import sys


def load_events(path):
    # slurp every line as JSON — one bad/truncated line and the whole load dies
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def enrich(event):
    # would call VirusTotal on the dest_ip — key pulled straight from the
    # environment, and if it's missing we just... carry on without saying so
    key = os.environ.get("SIFT_VT_API_KEY", "")
    event["vt"] = {"checked": bool(key), "dest_ip": event.get("dest_ip")}
    return event


def score(event):
    # Suricata severity is 1 (most severe) .. 3 (least). The copilot "helpfully"
    # inverts it into a score — and blindly indexes alert/severity, assuming shape.
    sev = event["alert"]["severity"]          # KeyError three calls deep on a non-alert line
    base = {1: 10, 2: 6, 3: 3}.get(sev, 1)    # severity 5? silently scored 1.
    if event.get("dest_ip"):                  # None if the feed omitted it — trusted anyway
        base += 2
    return base


def triage(events):
    enriched = [enrich(e) for e in events]
    # assumes flow_id is always an int present on every event
    return sorted(enriched, key=lambda e: (-score(e), e["flow_id"]))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/eve.json"
    for e in triage(load_events(path)):
        sig = e.get("alert", {}).get("signature", "?")
        print(
            f"[sev {e['alert']['severity']}] flow={e.get('flow_id')} "
            f"{e.get('src_ip')}→{e.get('dest_ip')}: {sig} score={score(e)}"
        )


if __name__ == "__main__":
    main()
