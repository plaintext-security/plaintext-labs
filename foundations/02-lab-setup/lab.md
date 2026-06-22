# Lab 02 — Decide It, Build It, Defend It

*Type 11 · Decision / ADR — build the lab, then defend the choices in an ADR. [← Back to the module concept](README.md)*

## Setup

This lab ships a one-command validator-and-guide in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It confirms your
container tooling works and prints the VM isolation/snapshot walkthrough — it does **not** build the
VM for you, because standing it up by hand *is* the skill.

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/02-lab-setup
make demo    # validate Docker is running + print the VM isolation guide
```

You need Docker installed and a free hypervisor — [VirtualBox](https://www.virtualbox.org/) on
Windows/macOS-Intel/Linux, or [UTM](https://mac.getutm.app/) on Apple Silicon.

## Scenario

You're choosing — and then defending — the sandbox the rest of this curriculum runs in. The
constraints are fixed: you must be able to run **unknown, possibly hostile software** safely, at
**zero cost**, **reproducibly**. Within those, you make real calls: **VM vs. container** for the
untrusted lane, **network mode** (host-only / NAT / bridged), and **snapshot strategy**. The point
isn't just to make it work once — it's to pick deliberately, *prove* the isolation, and write down
*why this setup and not the alternatives*, downsides included, in an ADR.

> Keep the lab network isolated from your home/work network. Only ever attack targets you own or are
> explicitly authorised to test.

## Do

Each step builds on the last; you decide, then build, then defend the decision in writing.

1. [ ] **Create a Linux VM on a network mode you chose deliberately.** Install a fresh Ubuntu (or
   similar) VM. Pick **host-only or NAT — not bridged** for the untrusted lane (the module explains the
   reachability-vs-containment tradeoff), and note *which you picked and why*. *Hint:* in VirtualBox
   this is Settings → Network → Adapter 1.

2. [ ] **Prove the isolation.** From inside the VM, try to reach another device on your real LAN
   (e.g. `ping` your home router's IP). On a properly walled-off lab this should **fail** — verify it,
   don't assume it. This single check is the difference between an isolated lab and a bridged one, and
   it's the evidence behind your ADR's Decision.

3. [ ] **Make a clean snapshot and prove the revert.** Take a snapshot of the clean VM
   ("clean-baseline"), then *break* something — create a junk file, change a config — and **revert**.
   Confirm your change is gone. You now have a one-action undo button — that's your snapshot-strategy
   axis, demonstrated.

4. [ ] **Run a throwaway container.** On the host (or in the VM), run a disposable container that
   prints a message and exits cleanly (`docker run --rm ...`). This is your *tooling* lane — distinct
   from the VM, which is your *untrusted* lane. You've now exercised both options on the VM-vs-container
   axis.

5. [ ] **Write the ADR.** This is the deliverable. Following the Nygard format (see *Deliverables*),
   record: the **Context** (the constraints above), the **Options** you weighed on each axis (e.g.
   container-only vs. VM-for-untrusted; host-only vs. NAT vs. bridged) with their pros/cons, the
   **Decision** you made, and the **Consequences** you accept — including the honest downsides (a VM is
   heavier and slower than a container; host-only blocks the internet you sometimes want; even a VM can
   be escaped — VENOM — which is why you also wall the network). This is the judgment the module is
   really teaching.

6. [ ] **Capture the build as a rebuild-from-zero script.** Write down the exact steps so you — or a
   teammate — could recreate this lab from nothing, then turn those steps into the script in *Automate &
   own it* and commit it beside the ADR.

## Success criteria — you're done when

- [ ] Your VM is on a network mode you chose on purpose, and you've **verified** it can't reach a device
  on your LAN.
- [ ] You can revert to a clean snapshot in one action, and have proven a change disappears on revert.
- [ ] A container runs and exits cleanly.
- [ ] Your ADR has all four sections — **Context, Options, Decision, Consequences** — names the options
  you rejected on each axis, and states at least one **honest downside** you're accepting.
- [ ] Your rebuild script/notes would let someone reproduce the lab with no guesswork.

## Deliverables

`ADR-001-lab-setup.md` — an Architecture Decision Record in Nygard format:

```
# ADR-001: Lab setup for running untrusted software safely
## Context        — constraints: unknown/hostile software, zero cost, reproducible
## Options        — per axis (VM vs. container; host-only/NAT/bridged; snapshot strategy), each pro/con
## Decision       — the setup you chose, in a sentence or two
## Consequences   — what you accept by choosing it (the honest downsides) + how you verified isolation
```

Commit it (plus the rebuild script from below). Do **not** commit VM disk images, snapshots, or any
captured artifacts (they're heavy and may carry secrets — keep them out of git). This is your first
ADR; you'll reuse the construct in later tracks whenever there's a design choice to defend.

## Automate & own it

**Required.** Turn your rebuild notes into a **rebuild-from-zero script** — a small Bash (or Python)
script that does the reproducible parts for you: smoke-tests Docker (`docker run --rm hello-world`),
pulls your base image, and **prints the manual VM/snapshot/network steps that can't be automated** as
a checklist. The VM build stays manual; the script is the part that *can* be one command. Have a model
draft it from your notes, **review every line yourself** (especially that it never assumes the network
is isolated — it must remind you to *check*), run it on a clean machine to prove it reproduces the lab,
and commit it beside `ADR-001-lab-setup.md`.

## AI acceleration

Ask a model to draft the ADR's Options table and to review your Consequences for isolation gaps — then
own the **Decision** and verify its claims against your *actual* VM network settings, not its
assumptions. A model can't see your adapter mode; treat its "looks isolated to me" as a hypothesis you
confirm by re-running step 2. AI scaffolds the record; you sign it.

## Connects forward

Every later lab runs in this sandbox. The snapshot-and-isolate habit is what makes the
[Docker module](../03-docker/README.md) (where you'll see the container boundary up close), and later
the Malware and Offensive tracks, safe to do at all. Your rebuild script is the first piece of the
Phase 1 project — and the **ADR you wrote here is a construct you reuse** every time a later track
(ZTNA, automation, cloud) asks you to choose among real options and defend it.

## Marketable proof

> "I run an isolated, reproducible security lab — snapshot-and-revert VMs on a walled-off network
> plus containers for tooling — so I can detonate and break things safely, rebuild it from zero with
> one script, and **defend the design choices in an ADR** (why a VM and not a container, why host-only,
> and the downsides I accepted)."

## Stretch

- Add a **second VM** and put both on a *private, lab-only* network so they can talk to each other but
  nothing else — the topology you'll need the first time a lab has an attacker box *and* a target box.
