# Data provenance — Lab 14 (Reporting & Root-Cause Analysis)

## Real reference case: DFIR Report "Lunar Spider"

- **Case (narrative anchor):** The DFIR Report — "From a Single Click: How Lunar Spider Enabled a
  Near Two-Month Intrusion" (2025-09-29).
  <https://thedfirreport.com/2025/09/29/from-a-single-click-how-lunar-spider-enabled-a-near-two-month-intrusion/>
- **How it is used here:** `data/incident-findings.md` is a **synthetic set of raw forensic findings
  modelled on that case** (covering Modules 08–12: live response → network → log/cloud →
  anti-forensics → malware), with neutral naming (`BEACHHEAD-WS01`, `jsmith`, `svc-backup`,
  `prod-deploy`, C2 `workspacin.cloud`) consistent with the rest of the track. It is *modelled-on*
  the real case, not a verbatim export. See `../ANCHOR.md`.

## Bundled exercise data (committed, zero-cost)

- `data/incident-findings.md` — the "notes before the report": raw, artifact-cited findings the
  learner turns into a formal report.
- `data/report-template.md` — the forensic incident report template (Executive Summary, Technical
  Findings, Root-Cause Analysis, IOC table).
- `scripts/lint_report.py` — structural linter for the finished report.

This is a **concept/writing lab** — `make demo` prints the rubric and instructions; no container or
network is required.

## Optional REAL artifact (`make fetch-data`)

- **Dataset:** EVTX-ATTACK-SAMPLES (~200 real `.evtx` logs mapped to MITRE ATT&CK).
- **Author / source:** sbousseaden, <https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES> (GPL-3.0).
- **File wired:**

  | Purpose | File | Raw URL |
  |---|---|---|
  | Real Zerologon (CVE-2020-1472) NetLogon error — the anchor case's escalation technique | `Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Credential%20Access/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx |

- **Why:** lets the learner cross-check a finding/IOC against a genuine artifact for the case's
  escalation step and practise citing a real event in the report's Technical Findings section.

## SHA-256 (fill after fetch)

```
<fill after fetch>  data/artifacts/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx
```

## Notes

- The download is **deferred to runner-validation** — not run while authoring. The writing exercise
  (`make demo`) needs no network; `make fetch-data` is opt-in.
