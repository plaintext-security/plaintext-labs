# Lab 03 — Parsing Windows Telemetry at Scale

Environment for **Track 13 · Module 03**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/03-telemetry-at-scale/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer + Pester container
make shell   # drop into pwsh
make demo    # run the module gate (PSScriptAnalyzer + Pester) over the reference Vigil module
make down    # stop when done
```

- `data/events.jsonl` — a small pre-exported Windows-event artifact (15 events: Security 4688/4624,
  Sysmon 1/3, PowerShell 4104; 7 suspicious). Shaped exactly like `evtx_dump -o jsonl` output so the
  Linux container needs no Windows Event Log API.
- `Vigil/` — the **reference** end-state module (cumulative from Modules 01–02, plus this module's
  scaled `Get-VigilEvent` reading the JSONL artifact with source-side `-EventId`/`-Provider` filters,
  and `Write-VigilLog` structured JSON logging). Your job is the *process*, not copying it.

**Honesty note.** `Get-WinEvent -FilterHashtable`/XPath is the real Windows technique taught in the
module and cheatsheet, but `Get-WinEvent` is **Windows-only** (it calls the Windows Event Log API) and
does **not** run in this Linux container. Here `Get-VigilEvent` consumes an **exported** `.evtx`
artifact instead. On a real Windows host you would point it at the live log via `Get-WinEvent`; that
step is **assessed-not-demonstrated** in the container (an optional Windows step in `lab.md`). To
re-export your own `.evtx` (e.g. from [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)):
`cargo install evtx` then `evtx_dump -o jsonl sample.evtx > events.jsonl`.
