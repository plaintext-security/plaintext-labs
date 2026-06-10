# Module 09 — Network Forensics

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *reconstruct what moved across the wire — sessions, files, and intent — from the packet record.*

## Why this matters

An attacker can delete files from a compromised host, but they cannot reach back in time to erase
the packets that left the network. If you have a capture, you have a record of every byte that
transited the wire: the domains queried, the files transferred, the commands exchanged. Network
forensics turns a PCAP into testimony — it is the one artifact class that is simultaneously
high-fidelity, attacker-unmodifiable (from the victim's perspective), and routinely available at
most organisations that run perimeter logging. A practitioner who can read that testimony fluently
is the person in the room who can actually say what left.

## Objective

Analyse a simulated Meridian Financial PCAP using Zeek and tshark: identify a suspicious DNS
query, reconstruct the HTTP session that followed, and extract the transferred payload, producing
artifact-cited findings.

## The core idea

The first thing most practitioners reach for when given a PCAP is Wireshark — and Wireshark is
the right tool for *interactive* investigation. But the workflow changes at scale. A PCAP from an
enterprise border router might be 50 GB. Opening that in Wireshark and scrolling for suspicious
traffic is not a strategy; it is a prayer. **Zeek solves the scale problem** by consuming a PCAP
(or live interface) and emitting structured logs — one row per connection in `conn.log`, one row
per DNS query in `dns.log`, one row per HTTP transaction in `http.log` — that you can query with
grep, pandas, or a SIEM. Zeek is not a replacement for packet-level inspection; it is a first
pass that narrows the space before you open Wireshark.

The investigation pattern that emerges in practice is: **Zeek for breadth, tshark for depth.**
Start with `conn.log` to find unusual long-duration or high-volume connections, or connections to
unexpected ASNs. Move to `dns.log` to look for queries to newly registered or algorithmically
generated domains (DGA patterns), lookups for known bad domains, or an unusual volume of NXDOMAIN
responses — a command-and-control beacon that can't find its server. Then pivot: take the IP from
the suspicious DNS response, find it in `conn.log`, and pull the matching packets in Wireshark or
via `tshark -r capture.pcap -Y "ip.addr==<suspect>"` for exact-packet inspection.

HTTP forensics adds a layer that many responders underuse: **content reconstruction.** Zeek's
`http.log` records the URI, host, method, and `resp_mime_types` for every transaction, and its
`files.log` records MD5 hashes of every transferred file. If an attacker staged a dropper at
`http://198.51.100.42/update.exe` and your sensor saw the download, `files.log` has the hash —
and you can check that hash against VirusTotal without needing the file. If the session was
unencrypted, tshark's `--export-objects http` pulls the actual transferred bytes out of the PCAP
for direct analysis. Encrypted (HTTPS) sessions require a TLS secrets log or decryption keys; in
most network investigations, you won't have them, so you document what you *can* see: the SNI,
the certificate subject, the timing, and the connection pattern.

The attacker's biggest asset in network forensics is encryption; the defender's biggest asset is
that beacon intervals are hard to randomise perfectly and that most infrastructure reuse persists
for months. A connection to a fresh IP at a regular interval — even over TLS — is detectable by
pattern, even without reading the payload. That pattern is what the SOC should have alerted on,
and it's what you'll reconstruct in post-incident forensics from the flow record.

## Learn (~3 hrs)

**Zeek fundamentals (~1.5 hrs)**
- [Zeek Documentation — Getting Started](https://docs.zeek.org/en/master/quickstart.html) — how Zeek processes a PCAP, what logs it produces, and how the log format works. Read through "Reading Packets from a File" and at least the `conn.log` and `dns.log` reference pages.
- [Zeek — Log Formats Cheat Sheet (GitHub)](https://github.com/corelight/zeek-cheatsheets) — Corelight's community cheat sheets covering every log type; keep the conn.log and http.log pages open during the lab.

**Wireshark / tshark analysis (~1 hr)**
- [Wireshark User's Guide — Chapter 11: Working with Captured Packets](https://www.wireshark.org/docs/wsug_html_chunked/ChapterWork.html) — the display filter syntax, following streams, and exporting objects. Focus on "Following Protocol Streams" and "Export Objects."
- [Chris Greer — Wireshark for Security Professionals (YouTube, ~40 min)](https://www.youtube.com/watch?v=GMNOT1aZmD8) — a senior packet analyst walks through a malware infection PCAP using Wireshark; good for seeing the investigation thought process before doing the lab.

**DNS forensics (~0.5 hrs)**
- [Malware Traffic Analysis — Practice PCAPs](https://www.malware-traffic-analysis.net/training-exercises.html) — free, real-world malware PCAPs with write-ups. Work through one exercise after the lab to calibrate your analysis against a professional write-up.

## Key concepts
- Zeek processes PCAPs into structured logs: `conn.log`, `dns.log`, `http.log`, `files.log`, `ssl.log`
- Investigation flow: breadth (Zeek logs) → depth (tshark / Wireshark) on flagged IPs/sessions
- DNS forensics: DGA patterns, NXDOMAIN storms, beaconing to newly registered domains
- HTTP reconstruction: `files.log` for hashes, `--export-objects` for transferred bytes
- TLS sessions: SNI and certificate data are still visible even without decryption keys
- Beacon pattern detection: regular intervals in `conn.log` across time are detectable by timing even if content is encrypted

## AI acceleration

Zeek conn.log files can have millions of rows. A model can ingest a subset, compute connection
duration histograms, flag outlier long-lived connections, and identify beaconing patterns (regular
inter-connection intervals) far faster than manual review. The caveat: models are poor at reasoning
about raw bytes and packet timing; they work well on the structured log rows that Zeek already
parsed. Use the model for log analysis; use Wireshark for packet-level confirmation. Never take a
model's "that IP looks suspicious" as a finding — trace it to a specific row in the log and
document the field values.
