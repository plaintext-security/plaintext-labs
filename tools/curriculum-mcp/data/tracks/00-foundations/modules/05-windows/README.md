# Module 05 — Windows for Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *the enterprise runs on Windows, and so do most attacks; you can't stay Linux-only.*

## Why this matters
Most organisations are Windows shops, Active Directory is the crown jewel attackers chase,
and the AD, Endpoint, and Forensics tracks all assume you can navigate Windows. If your
comfort stops at the Linux shell, half the job is invisible to you. This module builds the
Windows literacy — filesystem, registry, processes, event logs, PowerShell — those tracks
depend on.

## Objective
Navigate Windows for security work: the filesystem and registry, processes and services,
event logs, and basic PowerShell.

## The core idea
It's tempting to stay Linux-only, but the enterprise runs on Windows and so do most attacks —
Active Directory is the crown jewel attackers chase, and the AD, endpoint, and forensics tracks all
assume you can navigate Windows. The mental shift for the Linux-comfortable: **Windows centralises
where Linux scatters.** The **registry** is the big one — a single hierarchical database of
configuration and runtime state — and because so much persistence and config lives there, it's both an
attacker's favourite hiding spot and a forensic goldmine. **Event logs** (with their Event IDs) are
the Windows answer to `/var/log`, and they're the raw material the entire defensive track reads.

The literacy to build: the filesystem and its key paths, the registry (hives/keys and why they matter
for persistence *and* forensics), processes/services/Task Scheduler (where persistence and privesc
live), event logs, and enough **PowerShell** to inspect and automate. PowerShell is the through-line —
it's simultaneously the native admin language, the attacker's tool of choice (signed, everywhere,
often fileless), and the defender's — which is why it shows up again in the offensive, defensive, and
AD tracks.

The judgment: PowerShell runs with real privilege and is the exact surface attackers abuse, so read
every generated command before running it — especially anything touching the registry, services, or
`Invoke-*`. "I ran the AI's PowerShell" on a live system is how you damage a host or trip the very
telemetry the blue team is watching for.

## Learn (~3 hrs)

**Fundamentals, hands-on**
- [TryHackMe — Windows Fundamentals (free rooms)](https://tryhackme.com/) — click-through coverage of the filesystem, users, the registry, and built-in tooling.
- [13Cubed — Introduction to Windows Forensics](https://www.youtube.com/watch?v=VYROU-ZwZX8) — a single intro episode (not the playlist); a defender's tour of the Windows artifacts (registry, event logs, execution) you'll be inspecting.

**The native automation language**
- [Microsoft Learn — PowerShell 101](https://learn.microsoft.com/en-us/powershell/scripting/learn/ps101/00-introduction) — enough PowerShell to inspect a system and automate the boring parts.

## Key concepts
- The Windows filesystem and important paths
- The registry: hives, keys, and why it matters for persistence and forensics
- Processes, services, and the Task Scheduler
- Windows event logs and Event IDs
- PowerShell basics for inspection and automation

## AI acceleration
A model is a fast PowerShell tutor and one-liner generator — but PowerShell runs with real
privilege. Read every generated command before running it, especially anything that touches
the registry, services, or `Invoke-` anything.
