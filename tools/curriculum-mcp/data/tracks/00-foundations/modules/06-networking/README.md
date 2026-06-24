# Module 06 — Networking Fundamentals

*Variant D · skill-first, breach as stakes (one light predict). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *you can't attack, defend, or investigate what you can't read on the wire.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules
{ .module-meta }

## The hook

In December 2020, the security firm FireEye found a backdoor buried in a software update millions of
organizations trusted: a tampered SolarWinds Orion plugin, later named **SUNBURST**. Once it woke up
on a victim's network, it needed to phone home to its operators — and it did so over **DNS**. It
generated odd-looking subdomains of `avsvmcloud.com` and *looked them up*, smuggling out the victim's
domain name and a list of running services inside those lookups, and reading its next command back from
the DNS answer. (The full anatomy is in [Mandiant's
write-up](https://cloud.google.com/blog/topics/threat-intelligence/sunburst-additional-technical-details/).)

Why DNS? Because **everyone lets DNS out.** You can lock a firewall down to almost nothing and DNS
still flows — every laptop, every server has to resolve names to work. To a defender, those lookups
looked like ordinary traffic. The whole intrusion hid in the one channel nobody blocks.

You don't need to understand the attack to start. You need to be able to *read the wire* — and once you
can, the beacon stops being invisible. That's this module.

## Objective

Read network traffic at the packet level: explain how a TCP connection is established and how a name
resolves, then capture a real exchange yourself and tell ordinary DNS apart from a beacon hiding in it.

## One prediction before the lab

You'll be handed a small packet capture of otherwise-normal traffic with one beaconing DNS lookup mixed
in. Before you read another line, commit to a guess:

> **If malware is phoning home over DNS — and DNS looks like every other lookup — what about *one*
> lookup could give it away?** (Jot it down. You'll check it in the lab once you can actually read the
> packets.)

The honest answer is "it's hard, on purpose" — which is exactly why DNS C2 works. But it isn't
invisible. Hold your guess; the lab reveals what actually stands out.

## The core idea

A **packet capture is the network's CCTV**: a time-stamped recording of every packet that crossed a
point on the wire. Nothing on the network is private from the capture — it sees what was actually sent,
not what a log says was sent. Reading one is the durable skill under every later track: an attacker maps
the network, a defender watches it, a forensicator reconstructs it from a capture. The unlock is
**layering** — data gets wrapped in headers on the way down the stack (application → TCP/UDP → IP →
frame) and unwrapped on the way up, so a single packet carries nested context: this IP, this port, this
connection state. Reading a capture is just reading those layers off each packet.

Two patterns appear in almost every capture you'll ever open. The first is the **TCP three-way
handshake**, how every TCP connection begins. The client sends a **SYN** ("I'd like to talk" —
*synchronize*); the server replies **SYN-ACK** ("go ahead, and I acknowledge you"); the client sends
**ACK** ("acknowledged — we're connected"). Three packets, and only then does data flow. Learn to spot
those three flags and you can find the start of any connection in a sea of packets — which is also why
port scanners, firewalls, and SYN-flood attacks all manipulate exactly this exchange.

The second is **DNS**, the internet's phone book: it turns a name (`example.com`) into an IP address
your computer can actually connect to. A lookup is usually two small packets over UDP port 53 — a
**query** ("what's the A record for `example.com`?") and an **answer** ("it's 93.184.216.34"). DNS is
everywhere, implicitly trusted, and almost never blocked — which is exactly why attackers abuse it. C2,
tunneling, and exfiltration all hide in DNS, because a lookup leaving your network looks like every
other lookup. SUNBURST is the textbook case: the *query name itself* carried the smuggled data, and the
*answer* steered the malware. **DNS is the phone book attackers use because no one hangs up on it.**

The judgment for the AI era: a model decodes a capture faster than you and explains a baffling `tcpdump`
filter well — but it occasionally invents header fields that aren't there, so verify against the RFC and
the man page. Reading the packets yourself is the skill the model accelerates, not the one it replaces.

## Learn (~3 hrs)

**The model & the protocols**
- [PracticalNetworking — Packet Traveling](https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/) — walks one packet hop by hop through the layers; the clearest mental model of "what's actually in a packet" out there. Read this first.
- [How DNS Works (comic)](https://howdns.works/) — the resolution chain as a short, friendly comic; you'll watch this exact chain happen in the lab (~20 min).
- [Cloudflare — What is DNS? / DNS server types](https://www.cloudflare.com/learning/dns/what-is-dns/) — a clean second source on resolvers and record types; skim so "A record" and "CNAME" aren't jargon (~15 min).

**Reading packets (video first, then hands-on)**
- [Chris Greer — "How TCP Works: The Handshake"](https://www.youtube.com/watch?v=HCHFX5O1IaQ) — a packet analyst walks through SYN / SYN-ACK / ACK and what each step negotiates, the way you'll read it in your own capture.
- [Julia Evans — "tcpdump is amazing"](https://jvns.ca/blog/2016/03/16/tcpdump-is-amazing/) — a short, practical on-ramp to the exact tool the lab uses; copy her filters and go.

**The breach, in primary source**
- [Mandiant — SUNBURST Additional Technical Details](https://cloud.google.com/blog/topics/threat-intelligence/sunburst-additional-technical-details/) — read the **DGA / DNS C2** section: how the subdomain *was* the exfil channel and the answer carried the command. This is what your beacon-spotting step is modeled on (~25 min).

**Reference (skim, return as needed)**
- [RFC 9293 (TCP)](https://www.rfc-editor.org/rfc/rfc9293) §3.4 and [RFC 1035 (DNS)](https://www.rfc-editor.org/rfc/rfc1035) §4 — the source of truth for the handshake and the query/answer format. Skim the message formats; don't read cover to cover.

## Key concepts
- A packet capture is the network's ground truth — it records what was actually sent
- Layering: each packet nests application → TCP/UDP → IP → frame headers
- The TCP three-way handshake (SYN / SYN-ACK / ACK) opens every TCP connection
- A DNS lookup is a query + answer over UDP/53; the A record maps name → IP
- DNS is implicitly trusted and rarely blocked — which is why C2/exfil hide in it (SUNBURST)
- Common ports: 53 (DNS), 80/443 (HTTP/S), 22 (SSH), 25 (SMTP)

## AI acceleration
Paste a confusing `tcpdump` filter or a packet line to a model and it will explain the flags, the
handshake state, and the DNS record types in plain English — a real shortcut to fluency. But verify
against the capture, the RFC, and `man tcpdump`: models occasionally invent fields. Then push it
further — ask it *why* a particular DNS lookup looks anomalous (long random subdomain? high query
rate? a name no human would type?). It drafts the reasoning; **you confirm it against the actual
packets and own the verdict.**
