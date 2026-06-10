# Module 02 — Windows & Endpoint Telemetry

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *the endpoint sees what the network can't; Sysmon is how you make it talk.*

## Why this matters
Most attacker activity — process creation, injection, persistence — happens on the endpoint, where
default Windows logging is thin. Sysmon turns a Windows host into a rich detection sensor, and its
event schema underlies a huge share of real-world detections. Learning what to collect and read
here is what makes the later detection and hunting modules possible.

## Objective
Deploy Sysmon with a good config, and read the process/network/persistence events that real
detections are built on — using real attack telemetry.

## The core idea
The endpoint is where the attack actually executes — a process spawns, injects into another,
installs persistence — while the network only ever sees the echoes. The problem is that default
Windows logging is famously thin: it will happily tell you a logon occurred, but not that
`winword.exe` spawned `powershell.exe` which spawned `cmd.exe`. **Sysmon** is the sensor that fills
that gap, writing a rich, consistent event schema — process creation with the full command line and
parent, network connections, image loads, registry and file changes — that a huge fraction of
public detections are written directly against.

The single most valuable thing Sysmon gives you is **process ancestry** — the parent/child chain.
Almost no technique looks malicious as a single event; it looks malicious as a *lineage*.
`powershell.exe` alone is benign; `winword.exe → powershell.exe -enc <base64>` is a macro dropper.
(That is literally the event the [detection-as-code](../08-detection-as-code/) lab fires on.)
Learning to read the tree — with command lines attached — is the core endpoint skill, and it's why
Event ID 1 is the workhorse of endpoint detection.

The judgment call: Sysmon's power is also its trap. Log everything and you drown in volume and cost
while burying the very signal you're after — so **the config *is* the detection strategy.** The
community baseline (SwiftOnSecurity's config) encodes years of "what's worth collecting and what's
just noise"; you start from it and tune, not from a blank file. And every exclusion is a security
decision, not just noise reduction — each path you stop logging is a place an attacker can choose to
live.

## Learn (~4 hrs)

**The endpoint sensor**
- [What is Sysmon — How to Install and Set Up Sysmon (video)](https://www.youtube.com/watch?v=PY1v_mZnjks) — install and configure the endpoint sensor.
- [SwiftOnSecurity sysmon-config](https://github.com/SwiftOnSecurity/sysmon-config) — the community baseline config; read it to learn what's worth collecting and why.

**Reading the events**
- [MITRE ATT&CK — Data Source: Process](https://attack.mitre.org/datasources/DS0009/) — how Sysmon events map to techniques.

## Key concepts
- Why default Windows logging isn't enough
- Key Sysmon Event IDs (1 process-create, 3 network, 11 file, 13 registry)
- Process ancestry and command-line logging
- Endpoint agents (Sysmon → Wazuh / EDR)
- Tuning: signal vs volume

## AI acceleration
A model explains a Sysmon Event ID or a suspicious command line instantly — a genuine accelerator
when triaging. But it'll also rationalise a benign-looking event that's actually malicious (or
vice-versa); confirm against the process ancestry and the real data, not the model's vibe.
