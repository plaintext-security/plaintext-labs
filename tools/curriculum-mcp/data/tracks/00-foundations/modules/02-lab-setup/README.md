# Module 02 — Building a Safe Lab

*Type 11 · Decision / ADR — choose your lab setup across the real axes and *defend* the choice. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *the first discipline of this whole field: never detonate on the machine you live on — and be able to say why your setup is the right one.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Module 01 — Security First Principles](../01-security-principles/README.md)
{ .module-meta }

## Why this matters

Every later lab — and all the poking-around you'll do on your own — needs somewhere you can run
hostile, broken, or just-plain-unknown software *without* risking your real files, your accounts, or
your home network. But "build a safe lab" hides a *decision*: there is no single right setup, only a
set of tradeoffs you must choose between and **defend** under real constraints — you have to run
unknown, possibly hostile software, at zero cost, reproducibly. Making that call deliberately — and
writing down *why*, including the honest downsides — is the professional skill here, the thing that
separates someone who can justify their isolation boundary from someone who infects their own laptop
on day one. It also keeps your learning *lawful*: the standing rule of this entire curriculum is that
you only attack targets you own or are explicitly permitted to test.

This module is also where you write your first **ADR** (Architecture Decision Record) — a short,
honest record of *what you chose, what else was on the table, and what you're accepting by choosing
it*. It's a tiny construct, but it's the one later tracks (ZTNA, automation, cloud) lean on every time
there's a real choice to defend, so we seed it here on a decision you can fully reason about.

## Objective

Choose a lab setup across the real axes — **VM vs. container**, **network mode**, **snapshot
strategy** — for running untrusted software safely at zero cost, stand it up, and **defend the choice
in an ADR** that states the options you rejected and the downsides you accepted.

## The core idea — the axes of the decision

There is no one "safe lab." There is a set of tradeoffs, and your job is to pick a point in that space
and justify it. Three axes carry the decision; the first is load-bearing.

**Axis 1 — VM vs. container (the load-bearing one).** Containers are fast, cheap, and reproducible, so
the tempting answer is "just use Docker." For *your tooling* and the curriculum's reproducible labs,
that's right. For *detonating unknown malware, it is not enough* — and this is the call beginners get
wrong. A container is not a separate machine; it is a *process* on your host with a restricted view,
and crucially it **shares your host's kernel.** A VM runs its own kernel on top of a hypervisor — a far
stronger wall. So the decision is rarely "VM *or* container"; it's "VM *for the untrusted lane*,
container *for the tooling lane*," and you must be able to say which goes where and why. (You'll see
exactly where a container's isolation ends — the shared kernel — hands-on in
[Module 03](../03-docker/README.md).)

**Axis 2 — network mode (host-only / NAT / bridged).** Malware is built to spread. In May 2017 the
**WannaCry** ransomware worm encrypted machines across the NHS, Telefónica, and hundreds of thousands
of other hosts in a day — not by being clicked, but by *worming* from machine to machine over the
network (SMB, the EternalBlue exploit). A sample you detonate will try to talk to whatever it can
reach: **bridged** puts the lab directly on your home LAN (it can reach — and infect — your real
devices); **NAT** lets the lab reach *out* to the internet but hides it from your LAN; **host-only**
walls it off from both, talking only to the host. The tradeoff is reachability vs. containment — and
*"is my lab actually isolated, or did I leave it bridged?"* is the one question worth re-checking every
single time.

**Axis 3 — snapshot strategy.** A snapshot is your undo button: capture the clean machine, break things
freely, and roll back to the exact known-good state in one action — that fearlessness is the real
unlock, because you learn far faster when a mistake costs nothing. The choice is *when* to snapshot
(a clean baseline before any detonation, at minimum) and how disposable to make the VM, traded against
the disk space each snapshot costs.

And here is the honesty that turns these three axes into one decision rather than three: **isolation has
limits even for VMs.** A VM's wall is strong, not infinite. **VENOM**
([CVE-2015-3456](https://nvd.nist.gov/vuln/detail/CVE-2015-3456)) was a 2015 bug in the virtual
*floppy-disk controller* shared by QEMU, Xen, and KVM: code running as root *inside* a guest could
write out of bounds and potentially execute code on the **host** — a true guest-to-host escape, from a
device almost no one even uses. The takeaway isn't fear; it's *why you don't bet everything on one
axis.* The VM boundary can fail, so you also wall off the network and keep snapshots — defence in
depth, which is exactly the kind of "consequence I accept and mitigate" an ADR exists to record.

## Learn (~1 hr)

**Virtualization & isolation**
- [VirtualBox: How to Use Snapshots](https://www.youtube.com/watch?v=Qte4X-rdr2Q) — Corey Schafer (video, short). Watch him take a clean baseline and roll back to it in one action. *That* is the undo button that lets you break things fearlessly — and the one thing to do before any detonation.
- [VirtualBox Networking Modes, Explained](https://www.ubuntumint.com/virtualbox-networking/) — UbuntuMint (article, ~10 min, updated 2023). Read the **NAT**, **Host-Only**, and **Bridged** sections holding one question: *can this VM reach my real network?* That answer is the whole difference between a walled-off lab and one quietly sitting on your home LAN.

**VM vs. container — where the wall actually is**
- [Containers vs VMs: What's the difference?](https://www.youtube.com/watch?v=cjXI-yxqGTI) — IBM Technology (video, short). A lightboard walkthrough; watch for the one load-bearing fact — containers **share the host kernel**, while each VM runs *its own*. That single difference is why untrusted code goes in a VM.
- [Containerization vs. Virtualization](https://www.wiz.io/academy/container-security/containerization-vs-virtualization) — Wiz (article, ~6 min). Read it for the security angle the video skips: a kernel bug is a **container-escape blast radius** across every container on the host, whereas a VM gives you hardware-level isolation. (Vendor page with some CTAs, but the isolation framing is exactly right.)

**The ADR — the record you'll write**
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — Michael Nygard (article, ~5 min). The original ADR essay, and the exact **Context · Decision · Status · Consequences** format your lab deliverable uses. Read it for *why* you record the options you rejected and the consequences you accept — that judgment is what this module is really after.
- [Architecture Decision Record](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html) — Martin Fowler (article, ~5 min). A short, current companion to Nygard: when an ADR is worth writing, and how to keep it honest and brief. Clean on mobile.

## Key concepts

- **It's a decision, not a recipe:** pick a point across three axes under real constraints (untrusted software, zero cost, reproducible) and *defend* it in an ADR.
- **Axis — VM vs. container (load-bearing):** a container shares your host kernel (a process with a restricted view); a VM runs its own kernel (a stronger wall). **Untrusted → VM. Your tooling → container.**
- **Axis — network mode:** host-only walls off both LAN and internet; **NAT** reaches out but hides from your LAN; **bridged** puts the lab on your real network — avoid it for anything untrusted. Tradeoff: reachability vs. containment.
- **Axis — snapshot strategy:** a clean baseline before detonation gives one-action undo; traded against disk space.
- **Isolation has limits:** VM escapes are real (VENOM, CVE-2015-3456) — which is *why* you don't bet one axis; you wall the network *and* snapshot too (defence in depth, recorded as accepted consequences).
- **The ADR construct:** Context · Options · Decision · Consequences — the honest record this module seeds for later tracks.
- **The authorization rule, internalised:** only ever attack what you own or are permitted to test.

## AI acceleration

Have a model draft your ADR — the options table and the VirtualBox network settings — from a one-line
description of your constraints, then **own the Decision and Consequences yourself.** A model will
happily fill in tradeoffs it can't verify and confidently call a setup "isolated" without ever seeing
your adapter mode; a lab you *think* is host-only while it's really bridged onto your home LAN is
precisely the expensive mistake this module exists to prevent. AI drafts the scaffold; you verify the
one thing that matters and you sign the decision.
