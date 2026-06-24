# Data provenance — Module 18, Detection Drift

## What ships in this repo

This lab is built on **curated synthetic fixtures**, by design: drift is only
observable as a *delta between two points in time*, which no single public capture
gives you. Everything is committed so `make demo` / `make baseline` / `make
drift-check` run fully offline and deterministically.

- `data/events_t0.jsonl`, `data/events_t30.jsonl` — Sysmon-shaped process-creation
  events (EventID 1) for a 4-host `corp.local` estate (`WIN10-01`, `FS01`, `DC01`,
  `LEGACY03`) using neutral placeholder names and RFC 1918 context. `t0` is the
  healthy baseline; `t30` bakes in the three injected drifts (a dead source, a
  degraded source, and a renamed `CommandLine`→`ProcessCommandLine` field) so the
  learner has to *detect* them, not read them off a manifest.
- `corpus/corpus_t0.jsonl`, `corpus/corpus_t30.jsonl` — a small labelled re-scoring
  corpus (malicious encoded-PowerShell + benign events, ground truth in `_label`).
  The same shape and lineage as the labelled corpus in modules 08/09.
- `baseline/sources.yml` — the declared "expected" half (heartbeat interval + volume
  floor per source) the learner tunes.

## The real artifacts it is anchored to

- **Detection under test:** `rules/encoded_powershell.yml` is a **real Sigma rule**
  shape (the SigmaHQ schema) for encoded-PowerShell execution, tagged to MITRE ATT&CK
  **T1059.001 PowerShell** — https://attack.mitre.org/techniques/T1059/001/. It is
  carried over from module 08's detection-as-code lineage.
  - Sigma specification: https://github.com/SigmaHQ/sigma-specification
  - Real upstream rules of this kind: https://github.com/SigmaHQ/sigma
- **The drift classes are real operational failure modes** — agent cert expiry
  (source goes silent), collector backpressure (volume degradation), and a vendor
  field rename across a product update (schema drift that silently rots a rule). The
  field rename `CommandLine` → `ProcessCommandLine` mirrors the genuine
  Sysmon-vs-Windows-Security-Auditing field-name difference detection engineers hit
  in practice.

## One-line citation

> Synthetic two-point telemetry fixtures over a `corp.local` estate, with a real
> SigmaHQ-schema rule for MITRE ATT&CK T1059.001
> (https://attack.mitre.org/techniques/T1059/001/) that rots under an injected
> schema-drift field rename.
