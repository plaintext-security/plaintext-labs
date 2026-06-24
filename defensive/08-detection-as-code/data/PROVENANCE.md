# Data provenance — Module 08, Detection-as-Code

## What ships in this repo (the seed)

`events.jsonl` is a **small curated seed** of six real-shaped Windows
process-creation (Sysmon EventID 1) events, one of which is malicious: an Office
parent (`WINWORD.EXE`) spawning `powershell.exe -enc <base64>` — the encoded
PowerShell behaviour (ATT&CK **T1059.001**) the lab rule detects. It uses neutral
placeholder naming (`CORP\jdoe`, `WK21.corp.local`). The seed exists so `make demo`
and the CI `.ci-demo` run **fully offline** with no download.

## The real artifact (`make fetch-data`)

The seed's encoded command is hand-built. For a **genuine, published** encoded
PowerShell event, `make fetch-data` pulls a real Atomic Red Team test and converts
it into the same `events.jsonl` shape `detect.py` consumes:

- **Dataset:** Atomic Red Team — technique **T1059.001** (PowerShell), the atomic
  tests that run an encoded command (e.g. *"PowerShell Command Execution"*, GUID
  `a538de64-1c74-46ed-aa60-b995ed302598`, which runs `powershell -e <base64>`; the
  base64 decodes to an obfuscated `Write-Host` string — a real, safe demonstration
  of the evasion).
- **Source (verified):**
  https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/atomics/T1059.001/T1059.001.yaml
  (directory: https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1059.001)
- **Project:** Atomic Red Team (https://github.com/redcanaryco/atomic-red-team),
  Red Canary's library of small, reproducible ATT&CK technique tests.
- **License:** MIT. Atomic Red Team is freely reusable with attribution.
- **Contains:** real attacker-tooling command lines for encoded PowerShell — the
  exact behaviour your Sigma rule must catch, as published by the project that
  defines the test.

## Fetch + convert pipeline

`make fetch-data` performs (and this file documents) the following — it is **not run
in CI; you run it locally**:

1. `curl -fL` `T1059.001.yaml` from the URL above → `data/raw/T1059.001.yaml`.
2. `python convert_atomic.py data/raw/T1059.001.yaml data/real_events.jsonl` —
   extracts every atomic test whose command runs encoded PowerShell and emits one
   Sysmon-shaped record per test, in the `events.jsonl` schema.
3. Fire your rule at the real events:
   `python detect.py detection.yml data/real_events.jsonl` — confirm it matches the
   genuine encoded-command line, then compare its FP behaviour against the seed.

Fetched ART YAML (`data/raw/`) and the converted `data/real_events.jsonl` are
gitignored (`data/.gitignore`); only the curated `events.jsonl` seed is committed.

## One-line citation

> Atomic Red Team, "T1059.001 — PowerShell" (atomic tests),
> https://github.com/redcanaryco/atomic-red-team (MIT). Converted to the lab's
> Sysmon-shaped event schema with `convert_atomic.py`.
