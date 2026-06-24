#!/usr/bin/env python3
"""
evtx_to_json.py — render real Windows EVTX into the flat JSON-events shape the
offline Sigma matcher (detect.py) and sigma-cli consume.

It does NOT parse EVTX directly: it consumes the XML that python-evtx's
`evtx_dump.py` emits (the standard, real conversion tool), so this stays a thin,
deterministic shim over real telemetry rather than a reimplementation.

Pipeline (see Makefile `convert` target):
    for f in data/evtx/*.evtx:
        evtx_dump.py "$f" | python3 evtx_to_json.py --phase <name> >> records
    ... combined into data/events.json

Each EVTX record becomes one JSON object with Windows event fields flattened to
the names Sigma rules expect (EventID, Channel, Image, TargetImage, CommandLine,
GrantedAccess, ...) plus a `phase` tag and `_source` filename for triage.
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET


def localname(tag):
    """Strip the {namespace} prefix ElementTree keeps on Windows Event XML."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def parse_event(elem):
    """Turn one <Event> element into a flat dict of Sigma-friendly field names."""
    rec = {}
    for child in elem:
        name = localname(child.tag)
        if name == "System":
            for sysnode in child:
                key = localname(sysnode.tag)
                # EventID, Channel, Computer, Provider(@Name), Level, etc.
                if key == "Provider":
                    rec["Provider"] = sysnode.get("Name", "")
                elif (sysnode.text or "").strip():
                    rec[key] = sysnode.text.strip()
                # EventID may carry text; some providers use Qualifiers attr too.
        elif name == "EventData":
            for data in child:
                dname = data.get("Name")
                if dname:
                    rec[dname] = (data.text or "").strip()
        elif name == "UserData":
            # Some channels (e.g. some Sysmon variants) nest under UserData.
            for sub in child.iter():
                dname = localname(sub.tag)
                if (sub.text or "").strip() and dname not in ("UserData",):
                    rec.setdefault(dname, sub.text.strip())
    return rec


def main():
    ap = argparse.ArgumentParser(description="evtx_dump.py XML -> flat JSON events")
    ap.add_argument("--phase", default="", help="attack-phase tag for these records")
    ap.add_argument("--source", default="", help="source EVTX filename for triage")
    args = ap.parse_args()

    xml_text = sys.stdin.read()
    # evtx_dump.py wraps records in <Events>...</Events>; tolerate a missing root.
    if "<Events>" not in xml_text:
        xml_text = "<Events>\n" + xml_text + "\n</Events>"
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        sys.stderr.write(f"[evtx_to_json] XML parse error: {e}\n")
        sys.exit(2)

    out = []
    for elem in root.iter():
        if localname(elem.tag) == "Event":
            rec = parse_event(elem)
            if args.phase:
                rec["phase"] = args.phase
            if args.source:
                rec["_source"] = args.source
            out.append(rec)

    for rec in out:
        print(json.dumps(rec))


if __name__ == "__main__":
    main()
