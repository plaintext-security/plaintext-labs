# Module 02 — Building a Safe Lab

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *you need somewhere safe to break things before you break anything for real.*

## Why this matters
Every later lab — and all your own experimentation — needs an isolated, disposable,
reproducible environment. Doing security work on your daily machine, or against systems you
don't own, is how people get hurt or get arrested. This module sets up the sandbox the whole
curriculum runs in, and the snapshot-and-revert habit that lets you break things fearlessly.

## Objective
Stand up an isolated, snapshot-able lab (VM + containers) you can reset to a known-good
state, and understand when to use a VM versus a container.

## The core idea
This module exists for one reason: you need a place to do dangerous things safely, because the
alternative — experimenting on your daily machine or against systems you don't own — is how people
destroy their own data or get arrested. The mental model has two pillars. **Isolation:** the lab must
not be able to reach your real network; host-only/NAT networking walls it off, and "is my *isolated*
lab actually isolated, or did I accidentally leave it bridged?" is the single question that matters
most. **Disposability:** snapshots are your undo button — break the box, revert to known-good, try
again. That fearlessness is the real unlock; you learn far faster when a mistake costs nothing.

The VM-vs-container call is one you'll make constantly. A **VM** is a full, separately-kernelled
machine — a stronger boundary, heavier — so it's what you use for malware, full-OS targets, and
anything you don't trust. A **container** is a packaged process — lighter and reproducible — the
curriculum default for tooling and most labs. The malware track is where "untrusted → VM, never a
container" stops being a preference and becomes a rule (containers share the host kernel — see the
Docker module).

The judgment: the standing **authorization rule** isn't legal boilerplate, it's the line that keeps
this education lawful — only attack what you own or are explicitly permitted to (VulnHub and friends).
A model will happily draft your lab topology, but sanity-check the networking yourself: a lab you
*think* is isolated while it's actually bridged to your home LAN is the classic, expensive mistake.

## Learn (~2 hrs)

**Virtualization & isolation**
- [VirtualBox Manual](https://www.virtualbox.org/manual/) — the free hypervisor. Read specifically the **"Snapshots"** and **"Virtual Networking"** chapters: snapshots are your undo button, and host-only/NAT networking is how you wall the lab off from your home network.

**What to put in it**
- [VulnHub — getting started](https://www.vulnhub.com/) — free intentionally-vulnerable VMs, and the standing rule: only attack targets you own or are explicitly authorised to test.

## Key concepts
- Isolation: host-only vs NAT vs bridged, and why a lab shouldn't touch your LAN
- Snapshots and reverting to known-good
- VM vs container: when each is the right tool
- Disposable by default; reproducible from notes
- The authorization rule, internalised

## AI acceleration
Have a model draft your lab topology and network settings — then sanity-check every
networking choice yourself. A misconfigured "isolated" lab that's actually bridged to your
home network is exactly the mistake that bites.
