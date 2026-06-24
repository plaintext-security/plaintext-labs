#!/usr/bin/env python3
"""Convert a Windows EVTX file to the JSON shape `analyze.py` consumes.

`analyze.py` expects a list of events like:
    {"System": {"EventID": 1, "TimeCreated": "...Z", "Computer": "..."},
     "EventData": {"Image": "...", "CommandLine": "...", "ParentImage": "...", ...}}

EVTX-ATTACK-SAMPLES ships real Sysmon `.evtx` captures. This script reads one with
python-evtx, pulls the System fields and the flat EventData name/value pairs out of
each record's XML, and emits the JSON list to stdout.

Usage:
    pip install python-evtx
    python3 evtx_to_json.py <file.evtx> > data/real_sysmon_events.json
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from Evtx.Evtx import Evtx
except ImportError:
    sys.exit("python-evtx not installed — run: pip install python-evtx")

# Sysmon / Windows event XML namespace
NS = "{http://schemas.microsoft.com/win/2004/08/events/event}"


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def parse_record(xml_str: str) -> dict | None:
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return None

    system = root.find(f"{NS}System")
    if system is None:
        return None

    def sys_text(name: str) -> str:
        el = system.find(f"{NS}{name}")
        return el.text if el is not None and el.text else ""

    time_el = system.find(f"{NS}TimeCreated")
    time_created = time_el.get("SystemTime") if time_el is not None else ""

    sys_out = {
        "EventID": int(sys_text("EventID") or 0),
        "TimeCreated": time_created,
        "Computer": sys_text("Computer"),
        "Channel": sys_text("Channel"),
    }

    # EventData: <Data Name="Image">...</Data> pairs (Sysmon style)
    event_data: dict[str, str] = {}
    ed = root.find(f"{NS}EventData")
    if ed is not None:
        for data in ed.findall(f"{NS}Data"):
            name = data.get("Name")
            if name:
                event_data[name] = data.text or ""

    return {"System": sys_out, "EventData": event_data}


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: evtx_to_json.py <file.evtx>")
    path = Path(sys.argv[1])
    if not path.exists():
        sys.exit(f"not found: {path}")

    events = []
    with Evtx(str(path)) as log:
        for record in log.records():
            ev = parse_record(record.xml())
            if ev:
                events.append(ev)

    json.dump(events, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
