#!/usr/bin/env python3
"""
detect.py — Offline Sigma rule matcher against flat JSON event records.

Usage:
    python3 detect.py --rule rules/mydetection.yml --events data/events.json

`data/events.json` is REAL Windows telemetry produced by `make convert`
(sbousseaden/EVTX-ATTACK-SAMPLES rendered to flat JSON via evtx_dump.py +
evtx_to_json.py). Each record is one Windows event with Sigma-friendly field
names (EventID, Channel, Image, SourceImage, TargetImage, GrantedAccess, ...)
plus a `phase` tag and `_source` filename.

This is a teaching matcher for offline use. It supports the subset of Sigma
common in host-compromise detections:
  - detection.selection: field: value matching (case-insensitive substring)
  - detection.filter_*: exclusion conditions
  - condition: "selection and not filter_*"

It does NOT support all Sigma features (regex, near, etc.). For full coverage
use sigma-cli (also installed) to convert rules to a real backend.
"""

import argparse
import json
import sys

import yaml


def flatten(d, prefix=""):
    """Flatten nested dict to dot-separated keys (events are already mostly flat)."""
    result = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            result.update(flatten(v, key))
        else:
            result[key] = str(v)
    return result


def matches_selection(event_flat, selection):
    """All fields in the selection must match the event (case-insensitive substring)."""
    for field, value in selection.items():
        event_val = event_flat.get(field, "").lower()
        if isinstance(value, list):
            if not any(str(v).lower() in event_val for v in value):
                return False
        else:
            if str(value).lower() not in event_val:
                return False
    return True


def evaluate_rule(rule, events):
    detection = rule.get("detection", {})
    condition = detection.get("condition", "selection")

    selections, filters = {}, {}
    for key, val in detection.items():
        if key == "condition":
            continue
        (filters if key.startswith("filter") else selections)[key] = val

    matches = []
    for event in events:
        flat = flatten(event)
        sel_result = all(matches_selection(flat, sel) for sel in selections.values())
        filter_result = any(matches_selection(flat, filt) for filt in filters.values())

        if "and not" in condition:
            result = sel_result and not filter_result
        elif "and" in condition:
            result = sel_result and filter_result
        elif "not" in condition:
            result = not filter_result
        else:
            result = sel_result

        if result:
            matches.append(event)
    return matches


def load_events(path):
    """Accept a JSON array or JSONL (one event per line)."""
    with open(path) as f:
        text = f.read().strip()
    if not text:
        return []
    if text[0] == "[":
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def describe(ev):
    eid = ev.get("EventID", "?")
    chan = ev.get("Channel", ev.get("Provider", "?"))
    img = ev.get("Image") or ev.get("SourceImage") or ev.get("TargetImage") or ""
    return f"EventID={eid} | {chan} | {img}".rstrip(" |")


def main():
    parser = argparse.ArgumentParser(description="Offline Sigma rule matcher")
    parser.add_argument("--rule", required=True, help="Path to Sigma rule YAML")
    # --events is canonical; --alerts kept as an alias for older invocations.
    parser.add_argument("--events", "--alerts", dest="events", required=True,
                        help="Path to flat JSON events (data/events.json)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    with open(args.rule) as f:
        rule = yaml.safe_load(f)
    events = load_events(args.events)

    matches = evaluate_rule(rule, events)

    print(f"Rule: {rule.get('title', args.rule)}")
    print(f"MITRE ATT&CK: {', '.join(rule.get('tags', []))}")
    print(f"Events scanned: {len(events)}")
    print(f"Matches: {len(matches)}")
    print()

    if matches:
        for m in matches:
            phase = m.get("phase", "")
            src = m.get("_source", "")
            tag = f" | phase={phase}" if phase else ""
            tag += f" | src={src}" if src else ""
            print(f"  [MATCH] {describe(m)}{tag}")
            if args.verbose:
                print(f"          {json.dumps(m, indent=10)}")
    else:
        print("  No matches found.")

    sys.exit(0 if matches else 1)


if __name__ == "__main__":
    main()
