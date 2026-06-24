# Data provenance — Module 05, Intrusion Detection (Suricata)

## What ships in this repo (the seed)

`eve.json` is a **small curated seed** of 9 hand-built Suricata alert events that
model a clean, legible compromise: Cobalt Strike Malleable C2 beaconing, an
AsyncRAT CnC checkin, a PowerShell `dropper.ps1` download, DGA DNS queries, and a
large outbound POST (exfil). The signature names and SIDs are real
Emerging Threats rule identifiers; the events themselves are illustrative so
`make demo` runs **fully offline** with no download. Hostnames are neutral,
non-attributable placeholders (`c2.evil-update.invalid`, RFC 1918 internals).

## The real artifact (`make fetch-data`)

The real exercise runs Suricata with the Emerging Threats Open ruleset over a
genuine malicious packet capture from **Malware-Traffic-Analysis.net** (MTA.net),
Brad Duncan's public traffic-analysis blog.

- **Dataset:** 2024-12-17 — "SmartApeSG injected script leads to NetSupport RAT"
- **Source page (write-up):** https://www.malware-traffic-analysis.net/2024/12/17/index.html
- **PCAP download (verified, currently listed):**
  https://www.malware-traffic-analysis.net/2024/12/17/2024-12-17-SmartApeSG-to-NetSupport-RAT.pcap.zip
- **Archive password:** `infected` (MTA.net's standard scheme; see the site's
  About page)
- **Contains:** a SmartApeSG fake-update injection chain delivering NetSupport RAT,
  including the RAT's HTTP command-and-control traffic — real activity for
  signatures to fire on.
- **Detection ruleset:** Emerging Threats Open (ET Open), pulled via
  `suricata-update` (https://rules.emergingthreats.net/). ET Open is free for
  any use.
- **License / usage:** MTA.net exercises are published for free educational and
  research use. Do not redistribute the PCAP from this repo; fetch it from the
  source. The capture contains live malware traffic — handle only in an isolated
  lab.

If this dated entry is ever delisted, pick any recent capture from the
MTA.net index (https://www.malware-traffic-analysis.net/training-exercises.html or
the per-year index) and set `PCAP_URL=` on `make fetch-data`; update this file.

## Fetch + process pipeline

`make fetch-data` performs (and this file documents) the following — it is **not
run in CI; you run it locally**:

1. `curl -fL` the `.pcap.zip` from the URL above.
2. `unzip -P infected` the archive → `capture.pcap`.
3. `suricata-update` to pull the current ET Open ruleset.
4. Run Suricata over the capture: `suricata -r capture.pcap -l data/ -S rules`
   → overwrites `data/eve.json` with real alerts (plus `fast.log`, `stats.log`).
5. Analyze: `python3 parse_alerts.py data/eve.json`, then check the alerts
   against the MTA.net write-up linked above.

Fetched `*.pcap` / `*.pcap.zip` and Suricata's other run output are gitignored
(`data/.gitignore`); the curated seed `eve.json` is committed so the offline demo
works.

## One-line citation

> Malware-Traffic-Analysis.net, "2024-12-17 — SmartApeSG injected script leads to
> NetSupport RAT" (PCAP), https://www.malware-traffic-analysis.net/2024/12/17/index.html.
> Alerts generated with Suricata (https://suricata.io) + Emerging Threats Open ruleset.
