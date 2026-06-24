# Module 03 — Docker & Containers

*Variant D · skill-first, breach as stakes, one light predict. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *every lab here is Docker-first; this is the literacy that assumes — and the one mental model that keeps it from biting you.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules ([02 — Building a Safe Lab](../02-lab-setup/README.md))
{ .module-meta }

## Why this matters
Containers are how modern software ships — and how every lab in this curriculum runs, because
they're reproducible, disposable, and zero-cost. You need to read a `docker run` line, build an
image, and understand the isolation model well enough to use containers now and, later, attack and
defend them. Skip this and every other lab is cargo-culting commands you don't understand. But there's
a second reason, and it's the one that puts people in the news: **most people quietly believe a
container is a tiny, sealed machine.** It isn't, and that gap is exactly what a 2018 attack wave fed on.

## The case (short)
In 2018, researchers started finding the same thing over and over on the internet: **Docker daemons
exposed to the world.** Docker's control socket — the thing that builds and runs containers — was
listening on a public TCP port (2375/2376) with no authentication, often because someone enabled
"remote access" from a tutorial and never locked it down. Anyone who could reach that port could tell
Docker to run *anything*. Attackers wrote scripts to scan for it and, on every hit, launch a container
that mined cryptocurrency on the victim's hardware — **cryptojacking**, at internet scale. Worse, a
crafted run could mount the host's filesystem into the container, turning "I can run a container" into
"I am root on the host." Aqua Security, Trend Micro, and Unit 42 all documented campaigns built on this
exact exposure.
[Trend Micro — infected cryptocurrency-mining containers target Docker hosts with exposed APIs](https://www.trendmicro.com/en_us/research/19/e/infected-cryptocurrency-mining-containers-target-docker-hosts-with-exposed-apis-use-shodan-to-find-additional-victims.html)

The control plane was wide open — but the deeper reason it was *so* bad rests on a fact about what a
container actually is. Before you read on, call it.

## Call it before you read on
Don't scroll. Write down a one-line answer to each — being wrong here is the whole point, because the
correct answers are load-bearing for every lab and the entire container-security track later.

> **Q1.** "A container is basically a lightweight virtual machine — its own little sealed computer."
> True or false?
>
> **Q2.** You run a container with the `--privileged` flag (or you mount the host's root with
> `-v /:/host`). Roughly how much power does that container now have over the machine it's running on?

## The model, revealed
**Q1 — false, and the difference is the whole module.** A virtual machine is a *fake computer*: the
hypervisor gives it its own emulated hardware and its own kernel, and the wall between guest and host
is thick (you met its one crack — VENOM — in module 02). A **container is not a machine at all. It is
an ordinary process running on the host's *own* kernel**, just one whose *view* of the system has been
narrowed. Two Linux kernel features do the narrowing:

- **Namespaces** = *what the process can see.* A namespace gives the process its own private list of
  processes, its own network interfaces, its own filesystem mount tree, its own hostname. From inside,
  `ps` shows only the container's processes and it looks alone on the box — but that's a filtered view,
  not a separate computer.
- **Cgroups** (control groups) = *what the process can use.* Cgroups cap how much CPU and memory the
  process gets, so one container can't starve the others.

That's the entire isolation model: a normal process with a restricted view (namespaces) and a budget
(cgroups), **sharing the host's single kernel.** That shared kernel is the load-bearing fact. A VM that
gets compromised still has a kernel and a hypervisor between it and the host. A container that gets
compromised is already a process *on the host's kernel* — the only thing keeping it boxed in is those
namespace and cgroup restrictions. Weaken them and the box opens.

**Q2 — `--privileged` is, roughly, root on the host.** This is Q1's consequence made concrete.
`--privileged` strips away the restrictions: it hands the container nearly all kernel capabilities and
access to the host's devices. A `-v /:/host` mount drops the host's entire filesystem inside the
container. Either one means a process inside the container can reach out and change the real machine —
read its secrets, write to its disk, load kernel modules. That's why the exposed-daemon wave was so
profitable: telling an open Docker daemon to run a privileged container, or one with the host mounted,
*is* handing over the host. **The mental model to keep for good: a container is a process with a
restricted view of the system, not a machine — and a "container escape" isn't breaking out of a box,
it's removing restrictions on a process that was on the host the whole time.**

This is why "a container is not a security boundary by default" is the sentence that matters. It's an
*isolation* mechanism, a good one for reproducibility and blast-radius — but the moment you add
`--privileged`, a broad volume mount, or expose the daemon, you've punched a hole straight back to the
host. You'll *see* the namespaces and cgroups in the lab, and see exactly where they stop.

## Learn (~3 hrs)

*Lean on purpose. The model above is yours to own. These go deeper on the mechanism and the hands-on
muscle — read them to do the lab, not to relearn the model.*

**Hands-on basics**
- [Docker — Get Started](https://docs.docker.com/get-started/) (~1 hr, do it) — the official, hands-on intro: images vs. containers, volumes, ports, the run/build loop you'll use in every later lab.
- [TechWorld with Nana — Docker Tutorial for Beginners](https://www.youtube.com/watch?v=3c-iBn73dDE) (~3 hrs full; **watch the first ~60 min**) — the clearest beginner-to-working walkthrough; the opening hour (images, containers, ports, volumes) is enough for the lab.
- [Play with Docker](https://labs.play-with-docker.com/) (browser sandbox) — a free in-browser Docker host if you can't or shouldn't install locally.

**The isolation model and its limits**
- [Docker docs — Docker Engine security](https://docs.docker.com/engine/security/) (~25 min) — the primary source on the model: namespaces/cgroups, why `--privileged` is dangerous, why exposing the daemon socket is "effectively granting root." Read the "Docker daemon attack surface" section against the case above.
- [Docker docs — Protect the Docker daemon socket](https://docs.docker.com/engine/security/protect-access/) (~10 min, skim) — the literal fix for the 2018 wave: never expose 2375 unauthenticated. This page is that breach turned into a checklist.

## Key concepts
- A container is a **host process with a restricted view**, sharing the host kernel — *not* a VM, *not* a sealed machine
- **Namespaces** = what a container can *see*; **cgroups** = what it can *use* — together, that's the entire isolation model
- The shared kernel is the limit of that isolation; a container escape just removes restrictions on a host process
- `--privileged` and broad volume mounts (`-v /:/host`) ≈ root on the host — they punch holes straight back through the isolation
- Images (template) vs. containers (running instance) vs. registries (where images live); reading a `docker run` line tells you exactly what a lab exposes
- A container is not a security boundary *by default* — exposing the Docker daemon is handing out root

## AI acceleration
A model writes a `docker run` line or a Dockerfile instantly — and that's exactly where the holes from
this module ride in looking innocent: a stray `--privileged`, an over-broad `-v /:/host`, `EXPOSE`-ing
the daemon, or no non-root `USER`. Have the model draft your Dockerfile, then **review every generated
flag against this module's list** — a capability or mount you didn't intend is a real path back to the
host. The standing posture: AI drafts → you review every line → you own it. Catching the over-broad
default in generated infrastructure is the same reflex that *is* the job in the cloud track.
