# Answer key — planted errors in `ai-drafts/`

> Do not open this until your own `review-findings.md` is committed. `make reveal`
> prints it. Five drafts; **four carry a planted bug, one is correct** (the control).
> Catching the control as "fine" matters as much as catching the bugs — flagging
> the good rule is a false positive in *your* review.

| Draft | Planted bug | Tell (how you know) | Primary-source proof | Fire-proof |
|-------|-------------|---------------------|----------------------|------------|
| `01_encoded_powershell.yml` | **Wrong field** — keys on `ProcessCommandLine`; this estate's Sysmon events carry `CommandLine`. | Converts and runs cleanly but matches 0/2 of its tagged malicious samples. | Sigma taxonomy / a real SigmaHQ process_creation rule uses `CommandLine`. | Fix field -> fires 2/2 on the encoded-PowerShell events, 0 FPs. |
| `02_rundll32_lolbin.yml` | **Over-broad condition** — matches every `rundll32.exe` with no command-line constraint. | False-positives on the benign `Control_RunDLL desk.cpl` event. | T1218.011 is the *script/JS protocol* abuse, not all rundll32. | Constrain to `javascript:`/`script:` in CommandLine -> fires on the malicious call, quiet on the benign one. |
| `03_wmic_process_create.yml` | **Fabricated ATT&CK ID** — tagged `attack.t1047.002`, which does not exist (T1047 has no `.002`). Detection logic is correct. | Tag fails to resolve against the ATT&CK ID list. | attack.mitre.org/techniques/T1047 — no sub-techniques. | Retag to `attack.t1047` -> resolves; still fires on its known-bad. |
| `04_wrong_logsource_creds.yml` | **Wrong logsource** — LSASS access is Sysmon EID 10 (`process_access`), but it declares `process_creation`. Fields (`TargetImage`,`GrantedAccess`) belong to the wrong event class. | "No target sample / never fires" against a process-creation corpus — the pipeline can't even exercise it. | Sysmon schema: `GrantedAccess`/`TargetImage` are EID 10 fields. | Set `category: process_access` and test against a process_access sample -> fires on the LSASS-access known-bad. |
| `05_encoded_powershell_correct.yml` | **None — control.** Right field, right modifier, real tag, right logsource. | Fires 2/2 malicious, 0 FPs, tag resolves. | — | Already correct; do **not** "fix" it. |

## Why each survived a casual read

- **01** — "detects encoded PowerShell, tagged T1059.001" reads correct; only the
  field name is wrong, and it converts without error.
- **02** — "detects rundll32 LOLBin" sounds right; breadth only shows when fired
  at benign traffic.
- **03** — `t1047.002` looks like any other plausible sub-technique ID.
- **04** — the condition is textbook LSASS detection; the *logsource line* is the lie.
- **05** — it's correct, which is the trap: an over-eager review "finds" a bug.

The standing lesson: conversion passing != correct. **Fire it at ground truth and
resolve every ID against the primary source** — that is the only gate that doesn't lie.
