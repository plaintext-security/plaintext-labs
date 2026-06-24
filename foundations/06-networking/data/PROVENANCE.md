# Data provenance — 06-networking captures

This lab has two captures, and they come from different places on purpose.

## 1. `capture_annotated.txt` + `beacon_capture.txt` — SYNTHETIC teaching aids

These are small, hand-authored, `tcpdump`-format text files. The first walks a clean DNS lookup + TCP
handshake; the second is mostly-benign DNS with **one DNS-based C2 beacon** mixed in, **modeled on
SUNBURST** (SolarWinds, 2020), whose C2 tunneled over DGA-style lookups to `*.avsvmcloud.com`. The C2
domain here (`cloudtelemetry-svc.net`) is invented and resolves nowhere. These exist so the beacon-hunt
lesson works **offline, instantly, and safely** — no malware, no download. They are clearly labeled as
synthetic in their own headers.

## 2. The REAL upgrade — `make fetch-data` (Malware-Traffic-Analysis.net)

For a genuine artifact, `make fetch-data` downloads a **real malware C2 capture** from
Malware-Traffic-Analysis.net:

- **Exercise:** "2024-07-30 — Traffic analysis exercise: You dirty rat!" (a real RAT C2 infection)
- **Post (verified):** <https://www.malware-traffic-analysis.net/2024/07/30/index.html>
- **PCAP zip:** `2024-07-30-traffic-analysis-exercise.pcap.zip` (~10.8 MB)
- **Author:** Brad Duncan / Malware-Traffic-Analysis.net

### Why this step is deliberately manual (and not a one-line auto-extract)

MTA.net distributes pcaps as **password-protected zip archives on purpose** — the archives can contain
live malware and the password is published as an *image* on the site's
[about page](https://www.malware-traffic-analysis.net/about.html) specifically to stop automated
scraping/extraction. We honor that: `fetch-data` downloads the zip but **does not unzip it**. You fetch
the password yourself and extract it inside the throwaway lab container. That friction is the correct,
safety-aware handling of real malicious traffic — not an oversight. Redistribution of the pcap is not
ours to grant, which is the second reason we fetch rather than vendor it.

## RUNNER-VALIDATION NEEDED

- `make fetch-data` reaches the network and has **not** been run here.
- Extraction needs the manual MTA.net password, so it cannot be fully automated/validated on CI.
- A runner with the password can validate: `make fetch-data` → unzip → open the `.pcap` in the lab
  container (`tcpdump -r` / Wireshark) → confirm the real RAT C2 DNS/HTTP callbacks are visible and that
  the same "read the lookups, find the odd one" workflow applies to real traffic.
