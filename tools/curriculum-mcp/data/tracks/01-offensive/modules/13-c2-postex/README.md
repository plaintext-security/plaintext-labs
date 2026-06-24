# Module 13 — Command & Control and Post-Exploitation

*Type 5 · Detonate & Detect — stand up OSS C2 (Sliver), beacon and run post-exploitation, then characterise the telemetry you generate (beacon timing, JA3) as the thing the blue team hunts. (Secondary: Build-&-Operate — the stand-up-and-operate half.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Offensive Security** — *what a real operator does after the shell: persist, collect, and control — quietly.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
A raw shell is fragile and loud. Real operations run over a command-and-control (C2) framework
that gives reliable, encrypted, resilient control — and post-exploitation is the tradecraft of
doing useful work without getting caught. Open-source C2 like Sliver is used by real red teams
*and* real threat actors, so understanding it is essential for both attacking and detecting.

## Objective
Stand up an open-source C2, get a managed session on a lab host, and perform post-exploitation
(enumeration, persistence) while understanding the telemetry it generates.

## The core idea
The shell you got from exploitation is fragile and loud: one dropped connection and you're out, and
every command crosses the wire in the clear. A **C2 framework** is the upgrade — a managed, encrypted,
resilient session, where an implant beacons back on a schedule, reconnects, and survives a reboot.
**Post-exploitation** is the tradecraft of doing useful work through that channel — enumerate, collect,
persist, move — *without getting caught*. Open-source C2 like Sliver is used by real red teams and real
threat actors alike, which is exactly why understanding it serves attack and detection equally.

The mental model is a constant tradeoff between **control and noise.** Everything you do leaves
telemetry: the beacon has a timing signature (the entire premise of the defensive network-hunting
module), commands spawn child processes the endpoint records, collection touches files. The craft of
post-ex is minimising that footprint — which is why "beaconing" here is the same word the defenders are
hunting on. You are, deliberately, the thing the blue team is looking for.

The judgment, and why this is tradecraft rather than tooling: C2 is largely about *what not to do* — the
noisy command that burns your access, the persistence mechanism that trips an alert. A model accelerates
building post-ex commands and parsing what you collect, but it won't weigh operational risk for you;
that judgment is yours. And studying C2 closely is the only way to detect it well, which is why this
sits directly opposite the defensive track's C2-detection content.

## Learn (~4 hrs)

**The framework**
- [Sliver C2 — Complete Guide from Installation to Post-Exploitation (video)](https://www.youtube.com/watch?v=i_rPATPFi4M) — a full walk through the modern OSS C2.
- [Sliver Wiki](https://github.com/BishopFox/sliver/wiki) — the official reference for implants, listeners, and commands.

**Where it sits**
- [MITRE ATT&CK — Command and Control (TA0011)](https://attack.mitre.org/tactics/TA0011/) — C2 techniques and how defenders detect beaconing.

## Key concepts
- Why C2 beats a raw shell (resilience, encryption, sessions)
- Implants, listeners, and beaconing
- Post-exploitation: enumeration, collection, persistence
- C2 detection (beacon timing, JA3, network artifacts) — the defender's view
- Operating quietly vs the noise you actually make

## AI acceleration
A model accelerates building post-ex commands and parsing collected data — but C2 tradecraft is
largely about *what not to do* (noisy commands that burn your access), which the model won't
weigh. You own the operational judgment.
