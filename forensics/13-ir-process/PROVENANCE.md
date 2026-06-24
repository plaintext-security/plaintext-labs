# Data provenance — Lab 13 (IR Process / NIST SP 800-61)

## Real reference case: DFIR Report "Lunar Spider"

- **Case (narrative anchor):** The DFIR Report — "From a Single Click: How Lunar Spider Enabled a
  Near Two-Month Intrusion" (2025-09-29).
  <https://thedfirreport.com/2025/09/29/from-a-single-click-how-lunar-spider-enabled-a-near-two-month-intrusion/>
- **How it is used here:** the bundled `data/incident-brief.md` and `data/incident-timeline.csv`
  are a **synthetic training scenario modelled on that case's chain** (JavaScript-disguised
  attachment `Form_W-9.js` → `update.msi` → Latrodectus loader → credential theft → cloud pivot)
  with neutral naming (`BEACHHEAD-WS01`, `jsmith`, `svc-backup`, `prod-deploy`, C2
  `workspacin.cloud`). They are *modelled-on* the real case — not a verbatim export (the case's full
  PCAP/EVTX are DFIR-Labs-gated). See `../ANCHOR.md` for the naming convention.

## Bundled exercise data (committed, zero-cost)

- `data/incident-brief.md` — two-page incident brief with a partial timeline, three `[UNKNOWN]`
  gaps, and decision points to analyse against NIST SP 800-61.
- `data/incident-timeline.csv` — structured timeline (`timestamp,phase,action,actor`) used by the
  learner's `ir_timeline_checker.py` automation step.

This is a **concept/exercise lab** — `make demo` just prints the brief and the prompts; no container
or network is required.

## Optional REAL artifact (`make fetch-data`)

- **Dataset:** EVTX-ATTACK-SAMPLES (~200 real `.evtx` logs mapped to MITRE ATT&CK).
- **Author / source:** sbousseaden, <https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES> (GPL-3.0).
- **File wired:**

  | Purpose | File | Raw URL |
  |---|---|---|
  | Real Zerologon (CVE-2020-1472) NetLogon error — the anchor case's escalation technique | `Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Credential%20Access/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx |

- **Why:** lets the learner ground the synthetic brief against a genuine artifact for the case's
  escalation step, rather than reasoning only from prose.

## SHA-256 (fill after fetch)

```
<fill after fetch>  data/artifacts/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx
```

## Notes

- The download is **deferred to runner-validation** — not run while authoring. The exercise (`make
  demo`) needs no network; `make fetch-data` is opt-in.
