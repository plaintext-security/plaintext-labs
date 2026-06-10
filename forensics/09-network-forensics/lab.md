# Lab 09 — Network Forensics: Zeek + tshark on a Meridian Capture

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/09-network-forensics
make up      # builds the Zeek + tshark container and mounts the PCAP
make demo    # runs Zeek over capture.pcap and prints conn.log, dns.log, http.log highlights
make shell   # drops you into the container for hands-on analysis
make down    # stop when done
```

The container ships `zeek` and `tshark` against `data/capture.pcap` — a tiny PCAP (~250KB)
containing a simulated Meridian Financial incident: normal HTTPS traffic, a DNS lookup for a
suspicious domain (`update-cdn82.net`), a brief HTTP session to an unexpected IP, and a small
binary transfer. All traffic is synthetic — no real malware, no real credentials.

> All data is synthetic and local. No external targets involved.

## Scenario

Meridian's network sensor flagged a connection from `WORKSTATION-04` (the host from module 08)
to an IP address outside its expected cloud provider ranges. You have a five-minute PCAP pulled
from the perimeter sensor. Your task: identify what was queried, what was transferred, and
whether the session tells a coherent story of compromise — or just looks bad.

> Only examine network captures you are authorised to possess. In production, PCAP collection
> requires organisational approval and may be subject to privacy regulations.

## Do

1. [ ] **`make demo`** — read the Zeek output. Find the `dns.log` entry for `update-cdn82.net`.
   What IP did it resolve to? Does that IP appear in `conn.log`? What is the connection duration
   and bytes transferred?

2. [ ] **Examine the HTTP session.** From the demo output or by running `zeek -r data/capture.pcap`
   inside `make shell`, find the `http.log` entry for the suspicious IP. What URI was requested?
   What was the `resp_mime_type`? Does a MIME type of `application/octet-stream` on a GET request
   to a host you queried via suspicious DNS concern you? Why?

3. [ ] **Check `files.log`** for any transferred files. What is the MD5 hash? (In this synthetic
   scenario the binary is benign, but in a real investigation you'd submit the hash to VirusTotal.)
   Note the hash in your findings.

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

Module 10 (Log & Cloud Forensics) continues the Meridian investigation into the endpoint event
logs, correlating the network session timestamp with Windows event IDs. Module 12 (Malware
Artifacts) covers what to do with the binary you extracted from the HTTP session.

## Marketable proof

> "I run Zeek over network captures, identify C2 sessions from DNS and HTTP logs, reconstruct
> file transfers with tshark, and produce artifact-cited network forensics reports."

## Stretch

- Modify `beacon_detect.py` to also flag connections where `orig_bytes` (bytes sent) is
  consistently near-zero — a classic pattern for poll-only C2 beacons that only listen.
- Add a second PCAP to the environment using the public [NETRESEC PcapNg samples](https://www.netresec.com/?page=PcapFiles) and run the same analysis; document what the different traffic mix requires you to adjust in your methodology.
