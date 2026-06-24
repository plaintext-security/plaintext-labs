# Module 04 — Network Security Monitoring

*Type 7 · Build-&-Operate — run Zeek over real network traffic, read its protocol logs to find malicious activity, then author and prove a network detection (beaconing, DGA DNS, rare long-lived C2) that fires on the malicious logs and stays quiet on a benign baseline; you commit the Zeek setup plus a verified detection. (Secondary: Reconstruct — reading the attack back off the wire from the logs.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Defensive Operations** — *the network doesn't lie; Zeek turns packets into evidence.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
Endpoints can be blinded, but traffic still crosses the wire. Network Security Monitoring with Zeek
turns raw packets into rich, structured protocol logs — connections, DNS, HTTP, TLS, files — that
reveal C2, exfiltration, and lateral movement an endpoint might miss. It's a cornerstone of real SOC
visibility, and you can practice it on real malicious traffic for free.

## Objective
Run Zeek over real network traffic and read its logs to find malicious activity — then *author* a
network detection for the behaviour you found (beaconing, DGA DNS, rare long-lived C2) and **prove
it** fires on the malicious logs and stays quiet on a benign baseline. Finding it on the wire and
building a verified detection are equal halves.

## The core idea
Endpoints can be blinded — an attacker disables the agent, lives off the land, encrypts the payload
— but traffic still has to cross the wire, and the wire doesn't lie. The catch is that raw packets
are unreadable at scale. **Zeek** is the translator: it watches traffic and emits structured,
protocol-aware logs — one `conn.log` line per connection, plus `dns.log`, `http.log`, `ssl.log`,
`files.log` — turning a capture into something you query like a database. That shift, from packets
to typed protocol records, *is* Network Security Monitoring.

What the network sees that the endpoint can't is the *shape* of behaviour. Beaconing C2 shows up as
suspiciously regular connection timing in `conn.log` even when the payload is encrypted; DNS
tunnelling shows up as absurd query lengths and volumes in `dns.log`; exfiltration shows up as
bytes-out dwarfing bytes-in. You often can't read the content (TLS), but the metadata — JA3
fingerprints, SNI, certificate details, timing, volume — is frequently enough. For the network
engineer this is the familiar instinct of reading flow logs for "who talked to whom, how much, how
often" — now with full protocol context attached.

The judgment: Zeek tells you *what happened on the wire*; it cannot tell you what's *normal for your
wire*. "Rare external destination," "new JA3," "this host is beaconing" all need a baseline you
build — which is why a model summarising a `conn.log` is useful triage but no substitute for knowing
your environment. And there's an architecture tradeoff to make deliberately: Zeek metadata is cheap
and searchable for a long time; full-packet capture (Arkime) is gold for investigations but
expensive to store — most shops keep metadata long and full packets briefly.

## Learn (~4 hrs)

**The NSM tool**
- [A Technical Introduction to Zeek/Bro (video)](https://www.youtube.com/watch?v=R-8WdoP-CtE) — what Zeek is and why its logs beat raw packets.
- [Zeek documentation](https://docs.zeek.org/en/current/) — read "Getting Started" and the logs reference (conn, dns, http, ssl).

**Read real traffic**
- [Malware-Traffic-Analysis.net](https://www.malware-traffic-analysis.net/) — free, real malicious PCAPs with write-ups; your self-contained dataset.

## Key concepts
- Packets → protocol logs (conn, dns, http, ssl, files)
- What NSM catches that endpoints miss (C2, exfil, lateral movement)
- Zeek scripting and signatures (high level)
- Indicators in network logs (JA3, suspicious DNS, beaconing)
- Full-packet capture vs metadata (Arkime)
- Author then verify: write the network detection (Zeek/Sigma) and prove it fires on the C2 logs, quiet on a benign baseline — not just "describe a detection"

## AI acceleration
A model summarises a Zeek `conn.log` or explains a suspicious DNS pattern fast — useful triage. But
it can't see your network's baseline, so it'll flag normal-for-you traffic or miss a subtle beacon.
Confirm against the logs and the known-bad write-up.
