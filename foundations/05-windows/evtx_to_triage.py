#!/usr/bin/env python3
"""
evtx_to_triage.py — feed REAL public .evtx logs into triage.py.

triage.py analyzes a JSON list of flat event dicts. This aid turns a real
Windows .evtx into that exact shape so you can triage genuine captures, not
only the bundled sample.

Why this is needed: `evtx_dump` does NOT hand you something triage.py can read.
  - Its default output is XML (with "Record N" separator lines), not JSON.
  - `-o json` pretty-prints one object per record, again separated by
    "Record N" lines, so the file as a whole is not a single JSON document.
  - `-o jsonl` IS valid line-by-line JSON, but each record is *nested*
    ({"Event": {"System": ..., "EventData": ...}}) with EventID wrapped as
    {"#text": 7045}, not the flat dict triage.py expects.
This aid drives `evtx_dump -o jsonl` for you and flattens each record. It can
also read output you already dumped (jsonl, -o json, or default XML).

Where to get real public .evtx to practice on:
  - EVTX-ATTACK-SAMPLES — https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
    (real, public, ATT&CK-mapped logs; this repo caches a copy under
     .cache/datasets/evtx-attack-samples/). Pick one with 4688/7045/4624.

Dependency: the `evtx_dump` CLI on PATH (Rust `evtx` crate:
`cargo install evtx` or `brew install omerbenamram/tap/evtx`). triage.py's
own demo stays stdlib-only — this aid is only invoked when you pass a .evtx.

Usage:
    python3 evtx_to_triage.py Security.evtx > events.json
    python3 triage.py events.json
  or let triage.py detect the extension and call this for you:
    python3 triage.py Security.evtx
  ingest output you already produced:
    evtx_dump -o jsonl Security.evtx | python3 evtx_to_triage.py - | python3 triage.py -
  options:
    -o FILE   write JSON to FILE instead of stdout
    --all     keep every event (default: only the IDs triage.py sections)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Fields Windows stores as text but triage.py uses as an int (a dict key).
INT_FIELDS = {"LogonType"}

# evtx_dump prints "Record <n>" lines between records in its XML and -o json
# modes; strip them before parsing.
RECORD_SEP = re.compile(r"(?m)^\s*Record\s+\d+\s*$")


def _known_ids() -> set[int] | None:
    """The Event IDs triage.py sections — used to keep conversion output focused.

    Imported lazily so this stays decoupled (and circular-import-safe); if
    triage isn't importable, fall back to keeping everything.
    """
    try:
        from triage import EVENT_LABELS
        return set(EVENT_LABELS)
    except Exception:
        return None


def _coerce_ints(event: dict) -> dict:
    for field in INT_FIELDS:
        if field in event:
            try:
                event[field] = int(event[field])
            except (TypeError, ValueError):
                pass
    return event


def parse_record_xml(xml_text: str) -> dict | None:
    """Map one EVTX record's XML (<Event>...</Event>) to triage.py's dict.

    Pure/stdlib so it is unit-testable without a real .evtx. The `{*}` wildcard
    sidesteps the Windows event-schema XML namespace. Returns None for records
    without a numeric EventID.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    system = root.find("{*}System")
    if system is None:
        return None

    eid_el = system.find("{*}EventID")
    eid_text = (eid_el.text or "").strip() if eid_el is not None else ""
    if not eid_text.isdigit():
        return None

    event: dict = {"EventID": int(eid_text)}

    tc = system.find("{*}TimeCreated")
    # triage.py slices TimeCreated[:19], so it must be a present string.
    event["TimeCreated"] = tc.get("SystemTime", "") if tc is not None else ""

    comp = system.find("{*}Computer")
    if comp is not None and comp.text:
        event["Computer"] = comp.text

    data_parent = root.find("{*}EventData")
    if data_parent is not None:
        for data in data_parent.findall("{*}Data"):
            name = data.get("Name")
            if not name:  # positional/unnamed Data — triage keys by name
                continue
            event[name] = data.text if data.text is not None else ""

    return _coerce_ints(event)


def flatten_dump_record(rec: dict) -> dict | None:
    """Flatten one evtx_dump JSON record ({"Event": {...}}) to triage's dict."""
    ev = rec.get("Event") or {}
    system = ev.get("System") or {}

    eid = system.get("EventID")
    if isinstance(eid, dict):  # {"#text": 7045, "#attributes": {"Qualifiers": ...}}
        eid = eid.get("#text")
    try:
        eid = int(eid)
    except (TypeError, ValueError):
        return None

    event: dict = {"EventID": eid}

    tc = system.get("TimeCreated")
    event["TimeCreated"] = (tc.get("#attributes") or {}).get("SystemTime", "") \
        if isinstance(tc, dict) else ""

    comp = system.get("Computer")
    if comp:
        event["Computer"] = comp

    data = ev.get("EventData")
    if isinstance(data, dict):
        for key, value in data.items():
            if key.startswith("#"):  # skip #text / #attributes wrappers
                continue
            event[key] = value

    return _coerce_ints(event)


def _iter_json_objects(text: str):
    """Yield successive JSON objects from text (handles jsonl AND pretty
    multi-object -o json output via raw_decode)."""
    decoder = json.JSONDecoder()
    idx, n = 0, len(text)
    while idx < n:
        while idx < n and text[idx].isspace():
            idx += 1
        if idx >= n:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break
        yield obj
        idx = end


def normalize_text(text: str) -> list[dict]:
    """Parse already-dumped evtx_dump output — XML (default), -o json, or
    -o jsonl — or a native triage JSON array, into triage event dicts."""
    cleaned = RECORD_SEP.sub("", text)
    stripped = cleaned.lstrip()
    events: list[dict] = []

    if stripped.startswith("<"):  # XML dump
        for xml in re.findall(r"<Event\b.*?</Event>", cleaned, re.DOTALL):
            ev = parse_record_xml(xml)
            if ev is not None:
                events.append(ev)
    else:  # JSON: jsonl, pretty -o json, or a native flat array
        for obj in _iter_json_objects(cleaned):
            if isinstance(obj, list):  # native triage array
                events.extend(o for o in obj if isinstance(o, dict) and "EventID" in o)
            elif "Event" in obj:  # evtx_dump nested record
                ev = flatten_dump_record(obj)
                if ev is not None:
                    events.append(ev)
            elif "EventID" in obj:  # already a flat triage dict
                events.append(_coerce_ints(obj))
    return events


def convert(evtx_path: str | Path, keep_all: bool = False) -> list[dict]:
    """Run `evtx_dump -o jsonl` on a .evtx and flatten to triage event dicts."""
    if shutil.which("evtx_dump") is None:
        sys.exit("evtx_to_triage: `evtx_dump` not found on PATH "
                 "(install the Rust `evtx` crate: cargo install evtx).")

    proc = subprocess.run(
        ["evtx_dump", "-o", "jsonl", "--no-confirm-overwrite", str(evtx_path)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"evtx_to_triage: evtx_dump failed:\n{proc.stderr.strip()}")

    keep_ids = None if keep_all else _known_ids()
    events: list[dict] = []
    skipped = 0
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            skipped += 1
            continue
        ev = flatten_dump_record(rec)
        if ev is None:
            continue
        if keep_ids is None or ev["EventID"] in keep_ids:
            events.append(ev)
    if skipped:
        print(f"evtx_to_triage: skipped {skipped} unparseable line(s)",
              file=sys.stderr)
    return events


def main(argv: list[str]) -> int:
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2

    keep_all = "--all" in args
    out_path = None
    if "-o" in args:
        i = args.index("-o")
        if i + 1 >= len(args):
            sys.exit("evtx_to_triage: -o needs a filename")
        out_path = args[i + 1]

    source = args[0]
    if source == "-":
        events = normalize_text(sys.stdin.read())
        if not keep_all:
            keep = _known_ids()
            if keep is not None:
                events = [e for e in events if e["EventID"] in keep]
    elif Path(source).suffix.lower() == ".evtx":
        events = convert(source, keep_all=keep_all)
    elif Path(source).is_file():
        events = normalize_text(Path(source).read_text())
        if not keep_all:
            keep = _known_ids()
            if keep is not None:
                events = [e for e in events if e["EventID"] in keep]
    else:
        sys.exit(f"evtx_to_triage: no such file: {source}")

    payload = json.dumps(events, indent=2)
    if out_path:
        Path(out_path).write_text(payload)
        print(f"Wrote {len(events)} event(s) -> {out_path}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
