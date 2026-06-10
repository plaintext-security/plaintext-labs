# Module 02 — Scanning & Enumeration

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *turn a list of hosts into a map of services, versions, and ways in.*

## Why this matters
Once you know what exists, you need to know what it's running. Scanning and enumeration turn
IPs into a detailed picture — open ports, service versions, and the misconfigurations that
become footholds. Nmap is the field's standard, and reading its output fluently is a daily
skill for attackers and defenders alike.

## Objective
Discover live hosts, identify open ports and service versions, and enumerate a service
deeply enough to find an attack path.

## The core idea
Recon told you what *exists*; scanning tells you what's *running* and reachable — turning a list of
hosts into a map of services, versions, and the misconfigurations that become footholds. The mental
model is a funnel: host discovery (what's alive) → port scan (what's listening) → service/version
detection (what software, which version) → deep enumeration (what that service will tell you). Each
stage narrows toward an attack path. Nmap is the field standard not because it sends packets but
because it does all four, and its output is the lingua franca attackers and defenders both read.

The thing to internalise: **a port number is a hypothesis, not an answer.** 443 doesn't mean HTTPS;
it means "something is listening here" — version detection and the Nmap Scripting Engine turn that
guess into ground truth (and NSE quietly does a lot of the enumeration that finds the actual way in).
The SYN-vs-connect choice everyone frets over is really one knob on a single dial: stealth vs. speed
vs. reliability — the same packets, a different footprint.

The judgment, and the bridge to the other side of the house: **scanning is the loudest thing you'll
do.** It is exactly the T1595 telemetry the defensive track's NSM and IDS modules exist to catch — so
"scan aggressively" is an engagement decision with consequences. Too fast and you crash fragile
services or trip every alert; too slow and you burn the clock. A model will explain an unfamiliar flag
or summarise a huge scan instantly, but it cannot tell you whether your scan was appropriate for *this*
target on *this* engagement — that judgment stays yours, verified against the actual output.

## Learn (~3 hrs)

**The standard tool**
- [Nmap Reference Guide (the official book)](https://nmap.org/book/toc.html) — read the **"Port Scanning Techniques"** and **"Service and Version Detection"** chapters; the authoritative source, by Nmap's author.
- [Nmap for Beginners: A Complete Guide (video)](https://www.youtube.com/watch?v=z14HC3bJQpQ) — a visual walkthrough to pair with the book chapters.

**Where it sits**
- [MITRE ATT&CK — Active Scanning (T1595)](https://attack.mitre.org/techniques/T1595/) — scanning from the attacker-technique view (and how defenders detect it).

## Key concepts
- Host discovery
- TCP scan types (SYN vs connect) and when each applies
- Service and version detection
- The Nmap Scripting Engine (NSE) for enumeration
- Reading and recording scan output

## AI acceleration
A model will explain an unfamiliar Nmap flag or NSE script and summarise a big scan
instantly. But it can't tell you whether a result is real or whether your scan was too
aggressive for the engagement — that judgment stays yours. Verify against the actual output.
