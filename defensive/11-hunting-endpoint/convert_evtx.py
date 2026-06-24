#!/usr/bin/env python3
"""Convert a real Sysmon .evtx into the flat JSON shape hunt.py consumes.

Used by `make fetch-data` to turn a genuine EVTX-ATTACK-SAMPLES Sysmon capture
into data/sysmon_events.json. Each output record is one Windows event flattened
to a single dict: the System EventID, a UtcTime, and every Sysmon EventData
field (Image, CommandLine, ParentImage, TargetObject, DestinationIp, …) — the
same columns hunt.py loads into SQLite.

Requires python-evtx:  pip install python-evtx
Source of truth for the EVTX schema:
    https://github.com/williballenthin/python-evtx

Usage:
    python3 convert_evtx.py <input.evtx> [output.json]
"""
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from Evtx.Evtx import Evtx
except ImportError:
    sys.exit("python-evtx is required: pip install python-evtx")

NS = "{http://schemas.microsoft.com/win/2004/08/events/event}"


def record_to_dict(xml: str) -> dict | None:
    """Flatten one <Event> XML record into {EventID, UtcTime, <EventData fields>}."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    out: dict = {}
    system = root.find(f"{NS}System")
    if system is not None:
        eid = system.find(f"{NS}EventID")
        if eid is not None and eid.text:
            out["EventID"] = int(eid.text)
        ts = system.find(f"{NS}TimeCreated")
        if ts is not None:
            out["UtcTime"] = ts.get("SystemTime")
    data = root.find(f"{NS}EventData")
    if data is not None:
        for d in data.findall(f"{NS}Data"):
            name = d.get("Name")
            if name:
                out[name] = d.text
    # Sysmon carries its own UtcTime field; prefer it when present.
    if out.get("UtcTime") is None and "UtcTime" in out:
        pass
    return out or None


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(f"usage: {sys.argv[0]} <input.evtx> [output.json]")
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/sysmon_events.json")
    records: list[dict] = []
    with Evtx(str(src)) as log:
        for rec in log.records():
            d = record_to_dict(rec.xml())
            if d:
                records.append(d)
    dst.write_text(json.dumps(records, indent=2))
    print(f"Wrote {len(records)} event(s) → {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
