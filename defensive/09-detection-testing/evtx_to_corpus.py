#!/usr/bin/env python3
"""Convert real EVTX-ATTACK-SAMPLES .evtx captures into this lab's corpus shape.

`make fetch-events` uses this to turn genuine attacker telemetry from
sbousseaden/EVTX-ATTACK-SAMPLES (real Sysmon EventID-1/13/10 records for the
exact techniques this lab's rules target) into a JSONL corpus that eval.py and
test_detections.py can score the SHIPPED Sigma rules against — no SIEM, no
Windows host. The committed heldout/corpus.jsonl stays the deterministic
regression gate; this gives you the same rules judged on *real* events.

Each output line is one event flattened to a single dict:
    {"id": "<evtx-stem>#<n>", "label": "malicious", "technique": "<Txxxx>",
     "EventID": 1, "Image": "...", "CommandLine": "...", "ParentImage": "...", ...}

Every EVTX-ATTACK-SAMPLES record is attacker activity, so each is labelled
`malicious` and tagged with the ATT&CK technique of the source file's tree. (To
measure false-positive rate you still need benign lookalikes — keep the synthetic
benign half, or export benign events from your own SIEM; this corpus is the
malicious-recall half only.)

Requires python-evtx:  pip install python-evtx
EVTX schema / tool source of truth: https://github.com/williballenthin/python-evtx

Usage:
    python3 evtx_to_corpus.py OUT.jsonl  TECH:FILE.evtx  [TECH:FILE.evtx ...]
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
            try:
                out["EventID"] = int(eid.text)
            except ValueError:
                out["EventID"] = eid.text
        ts = system.find(f"{NS}TimeCreated")
        if ts is not None:
            out["UtcTime"] = ts.get("SystemTime")
    data = root.find(f"{NS}EventData")
    if data is not None:
        for d in data.findall(f"{NS}Data"):
            name = d.get("Name")
            if name and d.text is not None:
                out[name] = d.text
    return out or None


def main() -> int:
    if len(sys.argv) < 3:
        sys.exit(f"usage: {sys.argv[0]} OUT.jsonl TECH:FILE.evtx [TECH:FILE.evtx ...]")
    dst = Path(sys.argv[1])
    specs = sys.argv[2:]

    records: list[dict] = []
    for spec in specs:
        if ":" not in spec:
            sys.exit(f"bad spec '{spec}' — expected TECH:FILE.evtx")
        tech, _, fpath = spec.partition(":")
        src = Path(fpath)
        if not src.is_file():
            print(f"[warn] missing EVTX, skipping: {src}", file=sys.stderr)
            continue
        n = 0
        with Evtx(str(src)) as log:
            for rec in log.records():
                d = record_to_dict(rec.xml())
                if not d:
                    continue
                n += 1
                d["id"] = f"{src.stem}#{n}"
                d["label"] = "malicious"
                d["technique"] = tech
                records.append(d)
        print(f"[ok] {src.name}: {n} event(s)  ({tech})", file=sys.stderr)

    if not records:
        sys.exit("no events converted — check the EVTX paths (they may have moved "
                 "in the upstream repo; see PROVENANCE.md for the current tree).")

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print(f"Wrote {len(records)} real event(s) → {dst}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
