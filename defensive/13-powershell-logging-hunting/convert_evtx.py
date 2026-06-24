#!/usr/bin/env python3
"""Convert a real PowerShell Operational .evtx into the scriptblock-4104 JSON shape.

Used by `make fetch-data` to turn a genuine EVTX-ATTACK-SAMPLES capture of
Script Block Logging (Event ID 4104) records into data/scriptblock-4104.json.
Each output record matches the bundled seed:
    {TimeCreated, Id, LogName, Level, Computer, UserId, ScriptBlockText}

Only EventID 4104 records are kept — 4104 carries the deobfuscated
ScriptBlockText that hunt.ps1 matches its indicators against.

Requires python-evtx:  pip install python-evtx
EVTX schema reference: https://github.com/williballenthin/python-evtx

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
    """Extract one 4104 record into the scriptblock-4104 shape, or None."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    system = root.find(f"{NS}System")
    if system is None:
        return None
    eid_el = system.find(f"{NS}EventID")
    if eid_el is None or eid_el.text != "4104":
        return None

    ts_el = system.find(f"{NS}TimeCreated")
    chan_el = system.find(f"{NS}Channel")
    lvl_el = system.find(f"{NS}Level")
    comp_el = system.find(f"{NS}Computer")
    sec_el = system.find(f"{NS}Security")

    data = root.find(f"{NS}EventData")
    fields = {}
    if data is not None:
        for d in data.findall(f"{NS}Data"):
            name = d.get("Name")
            if name:
                fields[name] = d.text

    return {
        "TimeCreated": ts_el.get("SystemTime") if ts_el is not None else None,
        "Id": 4104,
        "LogName": chan_el.text if chan_el is not None else "Microsoft-Windows-PowerShell/Operational",
        "Level": lvl_el.text if lvl_el is not None else None,
        "Computer": comp_el.text if comp_el is not None else None,
        "UserId": sec_el.get("UserID") if sec_el is not None else None,
        "ScriptBlockText": fields.get("ScriptBlockText", ""),
    }


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(f"usage: {sys.argv[0]} <input.evtx> [output.json]")
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/scriptblock-4104.json")
    records: list[dict] = []
    with Evtx(str(src)) as log:
        for rec in log.records():
            d = record_to_dict(rec.xml())
            if d:
                records.append(d)
    dst.write_text(json.dumps(records, indent=2))
    print(f"Wrote {len(records)} Event ID 4104 record(s) → {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
