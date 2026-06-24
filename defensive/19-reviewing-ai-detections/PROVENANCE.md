# Data provenance — Module 19, Reviewing AI Detections

## What ships in this repo

The artifacts are **curated synthetic fixtures** by design: the lab teaches reviewing
AI-drafted detections, so it needs drafts with *known, planted* errors and a labelled
corpus with *known ground truth* — neither of which a public capture provides. Every
file is committed so `make demo` / `make review` / `make reveal` run fully offline and
deterministically.

- `ai-drafts/01..05_*.yml` — five Sigma rules in the real **SigmaHQ schema**, four
  seeded with realistic, planted errors (wrong field, over-broad condition, fabricated
  ATT&CK sub-technique, wrong logsource) and one correct control. The errors model the
  exact failure modes LLM-drafted detections actually exhibit.
- `corpus/corpus.jsonl` — labelled known-bad + known-good Sysmon-shaped events (ground
  truth in `_label` / `_technique`), same lineage as the labelled corpora in modules
  08/09.
- `attack/attack_ids.txt` — a local list of valid MITRE ATT&CK technique IDs for
  offline tag resolution.
- `solution/findings.md` — the sealed answer key.

## The real artifacts it is anchored to

- **Sigma:** rules follow the SigmaHQ specification and mirror real upstream rules.
  - Spec: https://github.com/SigmaHQ/sigma-specification
  - Rule corpus: https://github.com/SigmaHQ/sigma
  - Converted with **sigma-cli**: https://github.com/SigmaHQ/sigma-cli
- **MITRE ATT&CK** — every tag is checked against the real technique catalog; the
  planted `T1047.002` is fabricated precisely because **T1047 has no sub-techniques**:
  - T1047 Windows Management Instrumentation — https://attack.mitre.org/techniques/T1047/
  - T1059.001 PowerShell — https://attack.mitre.org/techniques/T1059/001/
  - T1218.011 Rundll32 — https://attack.mitre.org/techniques/T1218/011/
- **Sysmon schema** — the wrong-logsource bug is real: LSASS access
  (`GrantedAccess` / `TargetImage`) is Sysmon **EventID 10 `process_access`**, not
  `process_creation`. Sysmon docs:
  https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon

## One-line citation

> Synthetic AI-drafted Sigma rules (SigmaHQ schema,
> https://github.com/SigmaHQ/sigma) with planted errors checked against MITRE ATT&CK
> (https://attack.mitre.org/) and the Sysmon event schema, fired at a labelled
> module-08/09-lineage corpus.
