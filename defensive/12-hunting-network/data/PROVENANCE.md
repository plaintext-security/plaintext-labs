# Data provenance — Module 12, Network Hunting (Zeek beacon hunt)

## What ships in this repo (the seed)

`zeek/conn.log` is a **small curated seed** of 22 connections — hand-built to make
the RITA-style beacon-scoring lesson legible: 10 regular C2 callbacks, a periodic
update-service heartbeat (the deliberate "false positive that outscores the real
C2"), CDN browsing, and one large exfil connection. The seed exists so `make demo`
runs **fully offline** with no download, and so the CV-math teaching point is
deterministic. It uses neutral, non-attributable placeholder hosts (RFC 1918
internals; `185.220.101.47` / `204.79.197.200` as external stand-ins) — it is
illustrative, not a real capture.

## The real artifact (`make fetch-data`)

The real hunt runs Zeek over a genuine malicious packet capture from
**Malware-Traffic-Analysis.net** (MTA.net), Brad Duncan's public traffic-analysis
blog, and hunts its `conn.log` for C2 beaconing.

- **Dataset:** 2024-12-17 — "SmartApeSG injected script leads to NetSupport RAT"
  (chosen because NetSupport RAT generates real HTTP C2 callbacks — beaconing to
  hunt for).
- **Source page (write-up):** https://www.malware-traffic-analysis.net/2024/12/17/index.html
- **PCAP download (verified, currently listed):**
  https://www.malware-traffic-analysis.net/2024/12/17/2024-12-17-SmartApeSG-to-NetSupport-RAT.pcap.zip
- **Archive password:** `infected` (MTA.net's standard scheme; see the site's
  About page)
- **Contains:** a SmartApeSG fake-update injection chain delivering NetSupport RAT,
  including the RAT's command-and-control callbacks — the periodic beacon to surface
  with the scorer.
- **License / usage:** MTA.net exercises are published for free educational and
  research use. Do not redistribute the PCAP from this repo; fetch it from the
  source. The capture contains live malware traffic — handle only in an isolated
  lab.

If this dated entry is ever delisted, pick any recent capture (ideally one with C2
beaconing) from the MTA.net index
(https://www.malware-traffic-analysis.net/training-exercises.html or the per-year
index) and set `PCAP_URL=` on `make fetch-data`; update this file.

## Fetch + process pipeline

`make fetch-data` performs (and this file documents) the following — it is **not
run in CI; you run it locally**:

1. `curl -fL` the `.pcap.zip` from the URL above.
2. `unzip -P infected` the archive → `capture.pcap`.
3. Run Zeek over it in `data/zeek/`: `zeek -C -r capture.pcap` → regenerates
   `conn.log` (and dns.log, http.log, ssl.log, …).
4. Hunt: `python3 beacon_hunt.py data/zeek`, then check the surfaced C2 against
   the MTA.net write-up linked above.

Fetched `*.pcap` / `*.pcap.zip` and Zeek run metadata are gitignored
(`data/.gitignore`); only the curated seed `conn.log` is committed.

## One-line citation

> Malware-Traffic-Analysis.net, "2024-12-17 — SmartApeSG injected script leads to
> NetSupport RAT" (PCAP), https://www.malware-traffic-analysis.net/2024/12/17/index.html.
> Logs generated with Zeek (https://zeek.org).
