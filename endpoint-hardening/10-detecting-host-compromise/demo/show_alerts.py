#!/usr/bin/env python3
"""Print a summary of the real Windows EVTX events staged for this lab.

Reads data/events.json (produced by `make convert` from EVTX-ATTACK-SAMPLES via
evtx_dump.py + evtx_to_json.py): one flat record per Windows event, tagged with
its attack `phase` and source `.evtx` filename.
"""
import json
import sys


def load_events(path):
    with open(path) as f:
        text = f.read().strip()
    if not text:
        return []
    if text[0] == "[":
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


path = sys.argv[1] if len(sys.argv) > 1 else "data/events.json"
events = load_events(path)
print(f"Total events: {len(events)}")
print()

# group by phase for a quick triage view
by_phase = {}
for e in events:
    by_phase.setdefault(e.get("phase", "unknown"), []).append(e)

for phase, evs in by_phase.items():
    print(f"== phase: {phase}  ({len(evs)} events) ==")
    for e in evs[:5]:
        eid = e.get("EventID", "?")
        chan = e.get("Channel", e.get("Provider", "?"))
        img = e.get("Image") or e.get("SourceImage") or e.get("TargetImage") or ""
        src = e.get("_source", "")
        print(f"  EventID={eid:>4} | {chan:40.40} | {img[:40]:40.40} | {src}")
    if len(evs) > 5:
        print(f"  ... and {len(evs) - 5} more")
    print()
