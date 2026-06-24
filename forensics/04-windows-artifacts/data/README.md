# Module 04 — Data Directory

## Real EVTX (primary artifact)
The primary artifact for this lab is **real** Windows `.evtx` from the public
[EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) corpus
(by sbousseaden) — ~200 `.evtx` files mapped to MITRE ATT&CK. Run `make fetch-data` to
download them into this directory; see `PROVENANCE.md` for exact filenames, raw URLs, and
SHA-256 placeholders. The samples wired in cover the lab's three questions — who authenticated
(logon / 4624), what ran (process creation / 4688), and how the attacker covered tracks
(`Defense Evasion/DE_1102_security_log_cleared.evtx`, a real EID 1102 log-clear).

Run `chainsaw hunt` / `chainsaw search` (or hayabusa) against the fetched `.evtx` files directly.

## security-events.jsonl (synthetic fallback)
Pre-shaped Windows Security event records in JSON format, retained as an offline fallback so
`make demo` works before `fetch-data` has been run. These represent events from
`BEACHHEAD-WS01.corp.internal` during the incident window (2024-03-15 02:09–02:31 UTC), modelled
on the Lunar Spider intrusion (see the track ANCHOR). The real `.evtx` above is the primary artifact.

## ntuser-parsed.json
Pre-parsed synthetic registry hive representing `NTUSER.DAT` from the compromised
`svc-backup` account. In a real investigation, use `python-registry` against a real hive:
```python
from Registry import Registry
reg = Registry.Registry('NTUSER.DAT')
```
Real training hives are available from:
- https://github.com/EricZimmermanTrainingFiles (free training datasets)
