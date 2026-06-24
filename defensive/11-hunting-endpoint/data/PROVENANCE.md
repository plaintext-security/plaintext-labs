# Data provenance — Module 11, Hunt the Endpoint (Sysmon)

## What ships in this repo (the seed)

`sysmon_events.json` is a **small curated seed** — 21 Sysmon-shaped events hand-built
to model a clean, legible phishing-to-persistence chain (Office macro → encoded
PowerShell → certutil dropper → scheduled task + Run key) mixed with baseline
activity. The seed exists so `make demo` runs **fully offline** with no download. It
uses neutral, non-attributable placeholder names — host `WIN10-01`, user
`WIN10-01\user01`, RFC 1918 internal IPs — it is illustrative, not a real capture.

## The real artifact (`make fetch-data`)

The real exercise hunts over a **genuine Sysmon capture** from
**[EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)** — Samir
Bousseaden's public corpus of real Windows event logs organised by MITRE ATT&CK
tactic.

- **Dataset:** EVTX-ATTACK-SAMPLES (real Windows `.evtx`, MITRE ATT&CK-tagged)
- **Repo:** https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- **Sample used (verified path):**
  `Execution/exec_persist_rundll32_mshta_scheduledtask_sysmon_1_3_11.evtx`
  — direct:
  https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/blob/master/Execution/exec_persist_rundll32_mshta_scheduledtask_sysmon_1_3_11.evtx
- **Why this sample:** it carries Sysmon **EventID 1** (process creation), **3**
  (network connection), and **11** (file create) — the exact event types `hunt.py`
  queries — across a real `rundll32`/`mshta` execution chain that establishes
  **scheduled-task persistence (T1053.005)**. It maps cleanly onto the seed's hunt
  steps (process-tree pivots, LOLBin execution, persistence write).
- **License:** GPL-3.0 (the EVTX-ATTACK-SAMPLES repo). Do not redistribute the
  `.evtx` from this repo — fetch it from the source. The samples are benign captures
  of attacker tradecraft, safe to parse offline.

To use a different sample, set `EVTX_SAMPLE=` on `make fetch-data` (any EID-1-bearing
capture under `Execution/`, `Defense Evasion/`, etc.) and update this file.

## Fetch + convert pipeline

`make fetch-data` performs the following — it is **not run in CI; you run it
locally** (requires `git` and `python-evtx`):

1. `git clone --depth 1` EVTX-ATTACK-SAMPLES into `data/EVTX-ATTACK-SAMPLES/`
   (gitignored).
2. `pip install python-evtx`
   ([python-evtx](https://github.com/williballenthin/python-evtx) parses the EVTX
   binary format).
3. `python3 convert_evtx.py <sample>.evtx data/sysmon_events.json` — flattens each
   Windows event to one record `{EventID, UtcTime, <EventData fields>}`, the same
   shape `hunt.py` loads into SQLite.
4. Hunt: `python3 hunt.py` (or `make demo`) over the real events.

The cloned repo and any raw `*.evtx` are gitignored (`data/.gitignore`); only the
curated seed `sysmon_events.json` is committed.

## One-line citation

> Samir Bousseaden, "EVTX-ATTACK-SAMPLES" (Windows EVTX corpus), sample
> `Execution/exec_persist_rundll32_mshta_scheduledtask_sysmon_1_3_11.evtx`,
> https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES. Parsed with python-evtx
> (https://github.com/williballenthin/python-evtx).
