# Lab 09 — Network Forensics: Zeek + tshark on a Real Infection Capture

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/09-network-forensics
make up         # builds the Zeek + tshark container and mounts the PCAP
make fetch-data # downloads the REAL Redline Stealer infection PCAP (password-protected zip)
make demo       # runs Zeek over the capture and prints conn.log, dns.log, http.log highlights
make shell      # drops you into the container for hands-on analysis
make down        # stop when done
```

**The real artifact (preferred).** This lab analyzes a genuine malware-infection capture from
**[Malware-Traffic-Analysis.net](https://www.malware-traffic-analysis.net/)** — a 2024-10-23
**Redline Stealer** infection:

- Exercise page: <https://www.malware-traffic-analysis.net/2024/10/23/index.html>
- PCAP zip: <https://www.malware-traffic-analysis.net/2024/10/23/2024-10-23-Redline-Stealer-infection-traffic.pcap.zip> (~4.4 MB)
- IOCs: <https://www.malware-traffic-analysis.net/2024/10/23/2024-10-23-IOCs-for-Redline-Stealer-infection.txt.zip>

`make fetch-data` downloads the PCAP zip but **does not unzip it** — the archive is
**password-protected** (the standard malware-traffic-analysis.net password, documented on the
site's [About page](https://www.malware-traffic-analysis.net/about.html), is `infected`). Unzip it
yourself before `make demo`:

```bash
cd data && unzip 2024-10-23-Redline-Stealer-infection-traffic.pcap.zip   # password: infected
mv 2024-10-23-Redline-Stealer-infection-traffic.pcap capture.pcap
```

> The zip contains a **real malware infection capture**. Treat it as live evidence: analyze it in
> the lab container, never replay the traffic, and only handle captures you are authorised to possess.

**Offline fallback.** If you cannot reach the site, `make pcap` regenerates a tiny synthetic
`data/capture.pcap` via `scripts/gen_pcap.py` (a DNS lookup to a suspicious domain, an HTTP binary
transfer) so the tooling workflow still runs end to end. The synthetic capture is **not** the real
artifact — prefer the Redline PCAP above when you can fetch it.

> The synthetic fallback is local and contains no real malware. The fetched PCAP is real and is
> analysis-only.

## Scenario

The affected organization's network sensor flagged traffic from `BEACHHEAD-WS01` (the host from
module 08) to infrastructure outside its expected cloud-provider ranges. You have a PCAP pulled from
the perimeter sensor. Your task: identify what was queried, what was transferred, and whether the
session tells a coherent story of compromise — or just looks bad.

The capture is a real **Redline Stealer** infection from Malware-Traffic-Analysis.net (2024-10-23).
Redline is an info-stealer that beacons to its C2 and exfiltrates credentials and browser data — the
same "stealer/loader phones home" pattern seen in the DFIR Report "Lunar Spider" case that anchors
this track. Work the capture as if it were pulled from the beachhead host's segment.

> Only examine network captures you are authorised to possess. In production, PCAP collection
> requires organisational approval and may be subject to privacy regulations.

## Do

1. [ ] **`make demo`** — read the Zeek output. In `dns.log`, find the queries to non-corporate
   domains. Cross-check them against the IOCs file you downloaded
   (`2024-10-23-IOCs-for-Redline-Stealer-infection.txt`): which queried domain(s) match the
   published C2? What IP did it resolve to? Does that IP appear in `conn.log` — what is the
   connection duration and bytes transferred?

2. [ ] **Examine the HTTP session.** From the demo output or by running `zeek -r data/capture.pcap`
   inside `make shell`, find the `http.log` entries to the suspicious IP(s). What URIs were
   requested? What `resp_mime_type` came back? A GET that returns `application/octet-stream` (or a
   POST shipping data) to a host you reached via a suspicious DNS lookup — why does that concern
   you in an info-stealer infection?

3. [ ] **Check `files.log`** for any transferred files. Note the MD5/SHA-256 hash and compare it
   to the file hashes in the IOCs file. In a real investigation you'd submit the hash to VirusTotal —
   do so, and record the detection ratio in your findings.

4. [ ] **Use tshark to follow the HTTP stream.** From inside the shell, build a tshark command
   that reads the PCAP, filters to HTTP, and extracts just the fields you care about as columns —
   source/dest IP, request method and URI, response code. (Which read flag, which display filter,
   and which output mode lets you name individual `-e` fields?) Confirm the HTTP request and
   response line up with what Zeek reported.

5. [ ] **Look at the TLS sessions** in `ssl.log`. Is there any HTTPS traffic to the same IP as
   the HTTP download? What does the SNI say (if present)? A host that serves HTTP on one port and
   HTTPS on another, with a mismatched or missing SNI, is a strong indicator of attacker infrastructure.

6. [ ] **Write a one-paragraph network forensics summary** that covers: what domain was queried,
   what IP it resolved to, what was downloaded (by MIME type and MD5 hash), and your confidence
   level that this is C2 activity vs. a false positive.

## Success criteria — you're done when

- [ ] You have the suspicious IP, domain, and connection duration from `conn.log`.
- [ ] You have the URI, MIME type, and MD5 hash from `http.log` and `files.log`.
- [ ] You have run a `tshark` filter manually and confirmed the HTTP request/response fields.
- [ ] Your one-paragraph summary cites specific log fields and values.

## Deliverables

Commit to your portfolio repo:
- `network-findings.md` — your findings with specific log field citations (field name: value).
- `analysis.sh` — the tshark and zeek commands you ran, as a reproducible script.

Do not commit the PCAP — reference it by filename (`data/capture.pcap`) in your findings.

## Automate & own it

**Required.** Write a Python script `beacon_detect.py` that:
1. Reads a Zeek `conn.log` (TSV format, fields on the first line starting with `#fields`).
2. Groups connections by `id.resp_h` (destination IP).
3. For each destination with more than three connections, computes the mean and standard deviation
   of the inter-connection interval.
4. Flags any destination where the standard deviation is less than 20% of the mean as a potential
   beacon (unusually regular timing).
5. Prints the flagged IPs and their interval statistics.

Have a model draft the script; **test it against the demo `conn.log`** before trusting it on real
data. Beacon detection based on timing alone produces false positives from NTP and health-check
traffic — document one mechanism you'd add to reduce them. Commit `beacon_detect.py`.

## AI acceleration

Feed the Zeek `conn.log` output to a model and ask: "Are there any connections in this log that
suggest beaconing or C2 activity? Explain your reasoning by referencing specific fields." Compare
the model's analysis to your manual step-by-step. Where did it catch something you missed? Where
did it over-flag benign traffic (like the NTP entries)? The ability to critically evaluate model
output on structured security data — and know when it's right — is the differentiating skill.

## Connects forward

Module 10 (Log & Cloud Forensics) continues the investigation into the endpoint event
logs, correlating the network session timestamp with Windows event IDs. Module 12 (Malware
Artifacts) covers what to do with the binary you extracted from the HTTP session.

## Marketable proof

> "I run Zeek over network captures, identify C2 sessions from DNS and HTTP logs, reconstruct
> file transfers with tshark, and produce artifact-cited network forensics reports."

## Stretch

- Modify `beacon_detect.py` to also flag connections where `orig_bytes` (bytes sent) is
  consistently near-zero — a classic pattern for poll-only C2 beacons that only listen.
- Add a second PCAP to the environment using the public [NETRESEC PcapNg samples](https://www.netresec.com/?page=PcapFiles) and run the same analysis; document what the different traffic mix requires you to adjust in your methodology.
