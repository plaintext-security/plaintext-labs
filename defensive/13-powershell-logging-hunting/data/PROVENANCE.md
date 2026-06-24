# Data provenance — Module 13, Hunt Malicious PowerShell (4104)

## What ships in this repo (the seed)

`scriptblock-4104.json` is a **small curated seed** — nine **Event ID 4104** (PowerShell
Script Block Logging) records hand-built to model a legible mix of malicious and benign
PowerShell: download cradles, in-memory `IEX`, Base64 payloads, AMSI tamper, `[char]`
obfuscation, plus routine admin (an AD query, a process listing, and one *internal*
save-to-disk download you must not over-flag). The seed exists so `make demo` runs
**fully offline** with no download. It uses neutral, non-attributable placeholder names —
hosts `FIN-WKSTN-07` / `FIN-DC-01`, users `WIN10-01\user01`, `CORP\svc-patch`, an
internal `patches.corp.internal` host — it is illustrative, not a real capture.

## The real artifact (`make fetch-data`)

The real exercise hunts over a **genuine PowerShell 4104 capture** from
**[EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)** — Samir
Bousseaden's public corpus of real Windows event logs organised by MITRE ATT&CK tactic.

- **Dataset:** EVTX-ATTACK-SAMPLES (real Windows `.evtx`, MITRE ATT&CK-tagged)
- **Repo:** https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- **Sample used (verified path):** `Other/emotet/exec_emotet_ps_4104.evtx`
  — direct:
  https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/blob/master/Other/emotet/exec_emotet_ps_4104.evtx
- **Why this sample:** it is a real **Emotet** PowerShell loader captured in
  `Microsoft-Windows-PowerShell/Operational` **Event ID 4104** script-block records —
  the obfuscated, in-memory download-and-execute tradecraft (`New-Object Net.WebClient`,
  `DownloadFile`/`DownloadString`, `IEX`) that `hunt.ps1`'s indicators are built to
  catch. The deobfuscated `ScriptBlockText` is exactly the field the lab teaches.
- **License:** GPL-3.0 (the EVTX-ATTACK-SAMPLES repo). Do not redistribute the `.evtx`
  from this repo — fetch it from the source. The sample is a benign capture of attacker
  tradecraft, safe to parse offline.

To use a different sample, set `EVTX_SAMPLE=` on `make fetch-data` (any 4104-bearing
capture, e.g.
`Credential Access/phish_windows_credentials_powershell_scriptblockLog_4104.evtx`) and
update this file.

## Fetch + convert pipeline

`make fetch-data` performs the following — it is **not run in CI; you run it locally**
(requires `git` and `python-evtx`):

1. `git clone --depth 1` EVTX-ATTACK-SAMPLES into `data/EVTX-ATTACK-SAMPLES/`
   (gitignored).
2. `pip install python-evtx`
   ([python-evtx](https://github.com/williballenthin/python-evtx) parses the EVTX
   binary format).
3. `python3 convert_evtx.py <sample>.evtx data/scriptblock-4104.json` — keeps only
   EventID 4104 records and emits the
   `{TimeCreated, Id, LogName, Level, Computer, UserId, ScriptBlockText}` shape that
   `hunt.ps1` consumes.
4. Hunt: `make demo` (or `make hunt FILE=data/scriptblock-4104.json`) over the real
   records.

The cloned repo and any raw `*.evtx` are gitignored (`data/.gitignore`); only the
curated seed `scriptblock-4104.json` is committed.

## One-line citation

> Samir Bousseaden, "EVTX-ATTACK-SAMPLES" (Windows EVTX corpus), sample
> `Other/emotet/exec_emotet_ps_4104.evtx`,
> https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES. Parsed with python-evtx
> (https://github.com/williballenthin/python-evtx).
