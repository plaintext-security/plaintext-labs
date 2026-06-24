# Data provenance — Lab 08 (Triage & Live Response)

## Narrative anchor (story, not data)
- **The DFIR Report — "From a Single Click: How Lunar Spider Enabled a Near
  Two-Month Intrusion"** (2025-09-29).
  <https://thedfirreport.com/2025/09/29/from-a-single-click-how-lunar-spider-enabled-a-near-two-month-intrusion/>
- Used as the real-incident parallel: `Form_W-9*.js` → MSI → **Latrodectus** loader →
  Brute Ratel C4 / Cobalt Strike → Zerologon (CVE-2020-1472) → Rclone exfil (renamed
  `sihosts.exe`). The full PCAP/EVTX from that case are DFIR-Labs-gated, so the lab uses
  the public dataset below for a real hands-on artifact.

## Real dataset wired via `make fetch-data`
- **EVTX-ATTACK-SAMPLES** — genuine, ATT&CK-mapped Windows event logs.
  - Repo: <https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES>
  - `make fetch-data` shallow-clones the repo into `data/real/EVTX-ATTACK-SAMPLES/`.
  - License/terms: see the repository's LICENSE; samples are provided for research and
    detection engineering.
  - **SHA-256 (fill after fetch):** `TBD — record the hash of the specific EVTX you analyze`
  - Not password-protected (EVTX event logs, not live malware).

## Replaces
- The synthetic `data/pslist.json` / `netstat.json` / `recent_files.json` seed remains the
  one-command demo. The EVTX clone is the **real artifact** layered on top for cross-reference;
  it does not replace the deterministic demo seed.

## Notes
- Naming in the synthetic seed is grounded in the Lunar Spider case: beachhead host
  `BEACHHEAD-WS01`, compromised user `jsmith`, exfil tool `sihosts.exe` (renamed rclone).
- Download/validation and SHA-256 capture are **deferred to runner-validation** — no downloads
  were run while authoring this lab.
