# Data provenance — Lab 02 (Endpoint Telemetry)

## Real dataset: EVTX-ATTACK-SAMPLES (Sysmon)

- **Dataset:** EVTX-ATTACK-SAMPLES — real Windows Event Log (`.evtx`) captures organized by
  MITRE ATT&CK tactic.
- **Repository (verified):** https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- **Specific sample used (verified to exist):**
  `Execution/exec_sysmon_1_lolbin_rundll32_advpack_RegisterOCX.evtx`
  — a real **Sysmon EventID 1 (Process Create)** capture of a `rundll32.exe` LOLBin execution
  (`advpack.dll,RegisterOCX`), the same rundll32-LOLBin technique the bundled seed narrates.
  Raw: https://raw.githubusercontent.com/sbousseaden/EVTX-ATTACK-SAMPLES/master/Execution/exec_sysmon_1_lolbin_rundll32_advpack_RegisterOCX.evtx
- **License:** GPL-3.0 (see the repo's `LICENSE.GPL`). Honor GPL terms on reuse/redistribution.
- **What it contains:** genuine Sysmon operational-channel records (process creation with full
  command line, parent image, hashes, integrity level) emitted by a real attack-technique run —
  not hand-authored events.
- **How `make fetch-data` retrieves it:**
  1. `git clone --depth 1` the EVTX-ATTACK-SAMPLES repo into `data/EVTX-ATTACK-SAMPLES/` (gitignored).
  2. `pip install python-evtx` (https://github.com/williballenthin/python-evtx).
  3. `evtx_to_json.py` converts the `.evtx` into the `{System, EventData}` JSON shape `analyze.py`
     reads, writing `data/real_sysmon_events.json` (gitignored).
  4. Analyze the real capture: `python3 analyze.py data/real_sysmon_events.json`.
  Browse other tactics (`Persistence/`, `CredentialAccess/`, …) and point `evtx_to_json.py` at any
  Sysmon EID1/EID4104 sample to extend the lab.

## Committed seed: `sysmon_events.json`

A small hand-authored 10-event chain (host `WIN10-01`, user `user01`) — WINWORD → cmd → encoded
PowerShell → rundll32 LOLBin → LSASS access → Run-key persistence → C2 — kept so the offline
`make demo` exercises every analysis pass deterministically. It is a *teaching* sample, not real
telemetry; run `make fetch-data` to analyze a genuine EVTX capture.

## Citation

> @sbousseaden, "EVTX-ATTACK-SAMPLES," GitHub: https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
> (GPL-3.0). EVTX→JSON conversion via python-evtx (Willi Ballenthin):
> https://github.com/williballenthin/python-evtx
