# Data provenance — Module 04, Network Monitoring (Zeek)

## What ships in this repo (the seed)

`zeek/conn.log`, `zeek/dns.log`, `zeek/http.log` are a **small curated seed** of
Zeek logs — hand-built to model a clean, legible C2 compromise (periodic HTTPS
beaconing at ~300 s, DGA-style NXDOMAIN queries, a `dropper.ps1` download, and a
large outbound transfer). The seed exists so `make demo` runs **fully offline**
with no download. It uses neutral, non-attributable placeholder names
(`c2.evil-update.invalid`, RFC 1918 internal hosts) — it is illustrative, not a
real capture.

## The real artifact (`make fetch-data`)

The real exercise runs Zeek over a genuine malicious packet capture from
**Malware-Traffic-Analysis.net** (MTA.net), Brad Duncan's public traffic-analysis
blog.

- **Dataset:** 2024-12-17 — "SmartApeSG injected script leads to NetSupport RAT"
- **Source page (write-up):** https://www.malware-traffic-analysis.net/2024/12/17/index.html
- **PCAP download (verified, currently listed):**
  https://www.malware-traffic-analysis.net/2024/12/17/2024-12-17-SmartApeSG-to-NetSupport-RAT.pcap.zip
- **Archive password:** `infected` (MTA.net's standard scheme; see the site's
  About page)
- **Contains:** a SmartApeSG fake-update injection chain delivering NetSupport RAT,
  including the RAT's HTTP command-and-control callbacks — real beaconing and
  download traffic to detect.
- **License / usage:** MTA.net traffic analysis exercises are published for free
  educational and research use. Do not redistribute the PCAP from this repo;
  fetch it from the source. The capture contains live malware traffic — handle
  only in an isolated lab.

If this dated entry is ever delisted, pick any recent capture from the
MTA.net index (https://www.malware-traffic-analysis.net/training-exercises.html or
the per-year index) and set `PCAP_URL=` on `make fetch-data`; update this file.

## Fetch + process pipeline

`make fetch-data` performs (and `data/PROVENANCE.md` documents) the following — it
is **not run in CI; you run it locally**:

1. `curl -fL` the `.pcap.zip` from the URL above.
2. `unzip -P infected` the archive → `capture.pcap`.
3. Run Zeek over it: `zeek -C -r capture.pcap` → regenerates `zeek/conn.log`,
   `dns.log`, `http.log`, `ssl.log`, `files.log`, etc.
4. Analyze: `python3 analyze.py data/zeek`, then check findings against the
   MTA.net write-up linked above.

Fetched `*.pcap` / `*.pcap.zip` and Zeek run metadata are gitignored
(`data/.gitignore`); only the curated seed `*.log` files are committed.

## One-line citation

> Malware-Traffic-Analysis.net, "2024-12-17 — SmartApeSG injected script leads to
> NetSupport RAT" (PCAP), https://www.malware-traffic-analysis.net/2024/12/17/index.html.
> Logs generated with Zeek (https://zeek.org).
