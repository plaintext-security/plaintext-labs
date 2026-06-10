# Module 06 — Networking Fundamentals

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *you can't attack, defend, or investigate what you can't read on the wire.*

## Why this matters
Every security discipline rides on the network. An attacker maps it, a defender watches
it, a forensicator reconstructs it from what was captured. If you can't read a packet
capture and explain a TCP handshake or a DNS lookup, every later track is built on sand.
This module makes traffic legible — so `tcpdump` and Wireshark become tools you reason
with, not noise you stare at.

## Objective
Read network traffic at the packet level: explain how a connection is established and how
names resolve, then capture and dissect a real exchange yourself.

## The core idea
Every security discipline rides on the network — an attacker maps it, a defender watches it, a
forensicator reconstructs it — so if you can't read a packet, every later track is built on sand. The
model that unlocks everything is **layering**: data gets wrapped in headers on the way down the stack
(application → TCP/UDP → IP → frame) and unwrapped on the way up, so one packet carries nested context
— this IP, this port, this connection state. Reading a capture is just reading those layers. The
**TCP three-way handshake** (SYN / SYN-ACK / ACK) is worth genuinely understanding because it's both
how every connection begins *and* the thing scanning, firewalls, and SYN-floods all manipulate — see
it once and half of offensive/defensive networking clicks into place.

**DNS** is the other essential model: the resolution chain that turns a name into an IP through a
hierarchy of resolvers. It matters because it's everywhere, implicitly trusted, and therefore abused —
C2, tunnelling, and exfiltration all hide in DNS, which is exactly what the defensive hunting modules
chase. Common ports and protocols (HTTP/S, SSH, DNS, SMTP) are the vocabulary you'll read every scan
and capture with.

The judgment: AI decodes a capture faster than you can and explains a baffling `tcpdump` filter well —
but it occasionally invents fields, so verify against the RFC and the man page. Reading the packets
yourself is the durable skill; the model is a faster route to fluency, not a replacement for it.

## Learn (~3–4 hrs)

**The model & the protocols**
- [OSI Model Explained — Practical Networking](https://www.practicalnetworking.net/series/osi-model/) — the layered model in plain language with practical examples; understand each layer before diving deeper.
- [PracticalNetworking — Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) — walks a packet hop by hop, TCP/IP and all; the clearest mental model out there.
- [How DNS Works (comic)](https://howdns.works/) — the resolution chain you'll watch in the lab, told as a friendly comic.

**Reading packets (video first, then hands-on)**
- [Chris Greer — TCP and the Three-Way Handshake (follow-along lab, ~15 min)](https://www.youtube.com/watch?v=wMc0H22nyA4) — he reads a real capture the way you will in the lab.
- [Julia Evans — "tcpdump is amazing"](https://jvns.ca/blog/2016/03/16/tcpdump-is-amazing/) — a short, practical on-ramp to the exact tool the lab uses.
- [Wireshark — Sample Captures](https://wiki.wireshark.org/SampleCaptures) — open a few and practice "Follow TCP Stream" before you make your own.

**Reference (skim, return as needed)**
- RFC 9293 (TCP) and RFC 791 (IP) — the source of truth; skim the headers, don't read cover to cover.

## Key concepts
- IP addressing and subnetting (IPv4/IPv6)
- The TCP three-way handshake (SYN / SYN-ACK / ACK)
- UDP and when it's used
- The DNS resolution chain
- Common ports and protocols (HTTP/S, SSH, DNS, SMTP)

## AI acceleration
AI can decode a capture faster than you can — paste a confusing `tcpdump` filter and it
will explain the flags and the handshake. Verify against the RFC and the man page; models
occasionally invent fields. Reading the packets yourself is still the skill.
