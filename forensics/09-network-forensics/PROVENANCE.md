# Data provenance — Lab 09 (Network Forensics)

## Real dataset (preferred artifact)
- **Malware-Traffic-Analysis.net — Redline Stealer infection traffic (2024-10-23).**
  - Exercise page: <https://www.malware-traffic-analysis.net/2024/10/23/index.html>
  - PCAP zip (~4.4 MB): <https://www.malware-traffic-analysis.net/2024/10/23/2024-10-23-Redline-Stealer-infection-traffic.pcap.zip>
  - IOCs zip: <https://www.malware-traffic-analysis.net/2024/10/23/2024-10-23-IOCs-for-Redline-Stealer-infection.txt.zip>
- **Password-protected:** the zip uses the standard malware-traffic-analysis.net password
  `infected` (documented on the site's About page: <https://www.malware-traffic-analysis.net/about.html>).
- **Terms/license:** content from Malware-Traffic-Analysis.net is provided by Brad Duncan for
  training and research; review the site's About/terms page before redistribution. The lab does
  **not** commit the PCAP — it is fetched per-learner.
- **Handling:** the archive contains a **real malware infection capture**. `make fetch-data`
  downloads the zip but does **not** unzip it; the learner unzips with the password, analyzes in
  the lab container, and never replays the traffic.
- **SHA-256 (fill after fetch):**
  - PCAP zip: `TBD`
  - extracted `capture.pcap`: `TBD`

## Narrative anchor (story)
- The DFIR Report "Lunar Spider" intrusion (2025-09-29) anchors the track; Redline here stands in
  as the real "stealer/loader phones home to C2" network artifact, since the case's own PCAP is
  DFIR-Labs-gated.
  <https://thedfirreport.com/2025/09/29/from-a-single-click-how-lunar-spider-enabled-a-near-two-month-intrusion/>

## Replaces
- The synthetic `scripts/gen_pcap.py` output (`data/capture.pcap`) is now an **offline fallback**
  only (run via `make pcap`). The real Redline PCAP above replaces it as the primary artifact. The
  fallback's synthetic C2 domain was changed to `workspacin.cloud` (the real Latrodectus C2 from the
  anchored case) for grounding.

## Notes
- Download, unzip, and SHA-256 capture are **deferred to runner-validation** — no downloads were run
  while authoring this lab.
