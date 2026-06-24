# Module 11 — Container Escape & Runtime

*Variant D · build-first ("reproduce the escape, then detect it"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *a container is a process in a jail, not a VM. Prove the wall is the kernel by going through it — then write the detection that catches the next one.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md), [Module 10 — Container & Image Security](../10-container-image-security/README.md)
{ .module-meta }


## The exploit

In February 2019, Adam Iwaniuk and Borys Popławski disclosed **CVE-2019-5736**: a way for a process
inside a container to **overwrite the host's `runc` binary** — and thereby get code execution as root
on the host the moment any other container is started or `exec`'d into. `runc` is the low-level OCI
runtime that Docker, containerd, Podman, and Kubernetes all shell out to in order to actually *create*
a container. It runs as root on the host. The bug: when `runc` `exec`s into a running container, the
attacker (controlling the container's filesystem) can race a `/proc/self/exe` symlink so that the
host's own `runc` binary is opened for writing from inside the container, and replaced with attacker
code. The next container operation runs that code — on the host, as root.

It rated **CVSS 8.6**, landed on the CISA KEV-class watchlist of "patch this now" runtime bugs, and
forced an emergency coordinated release across every container platform at once. It is the canonical
container escape, and — crucially for you — it is **reproducible**: Vulhub ships a pinned vulnerable
runc environment for it, so you exploit the *real* CVE, not a hand-rolled stand-in.

## The mental model: the wall is the kernel

Here is the one idea that makes every container escape legible. **A container is not a small VM. It is
an ordinary host process wearing a costume** — Linux namespaces give it a private view (its own PID 1,
its own network, its own mount table), cgroups cap its resources, and capabilities trim its powers.
But underneath that costume, *it is sharing the host's kernel.* There is no hypervisor, no second
operating system, no hardware boundary. A syscall from inside the container is executed by the **same
kernel** the host runs on.

So "escape" is not breaking out of a box — there is no box. Escape is **abusing a resource the
container and host both touch**: a shared kernel interface, a host path mounted in, a privileged
device, a host-side helper binary the runtime invokes on your behalf. CVE-2019-5736 abuses the last
one: `runc` is a host binary that *reaches into* the container, and the attacker turns that reach
around. `--privileged` abuses devices: it hands the container `CAP_SYS_ADMIN` and visibility of
`/dev/sda1`, so it can just `mount` the host disk and `chroot` in — no CVE required. A mounted
`docker.sock` abuses the control plane: any process that can talk to the Docker API can ask the host
daemon to launch a new privileged container for it. Different doors, same hallway: **the boundary you
are trusting is the kernel, and the kernel is shared.**

This is why the defenses layer the way they do. You cannot make the kernel un-shared, so you (1)
**reduce what the container is allowed to ask the kernel** (drop capabilities, no `--privileged`,
seccomp/AppArmor, non-root UID — the image-hardening of module 10 and the admission policy of module
13), and (2) **watch what it actually asks at runtime.** That second layer is the subject of this lab.

## The gap that runtime detection fills

Static scanning (module 10) reads the image; admission control (module 13) reads the spec. Neither sees
*behavior*. CVE-2019-5736 is invisible to both — the image is clean, the spec is legal; the attack is a
sequence of **syscalls** at runtime. **Falco** closes that gap: it instruments the kernel's syscall
stream (modern eBPF probe) and evaluates each event against a rule set. "A process in a container wrote
to a host binary path." "A `mount(2)` happened inside a container." These fire because the syscall
happened, not because anything was scanned — so they catch both this CVE and the next novel one that
follows the same shape.

The practitioner skill is **signal-vs-noise tuning.** Out of the box, broad rules alert on benign work
— a database writing its data dir, a log shipper opening arbitrary files. A tuned rule fires on the
escape and stays *silent* on the legitimate workload. That tuned rule is an artifact you version: it is
detection-as-code, the runtime sibling of the policy-as-code you've written all phase. In this module
you'll reproduce the escape, deploy Falco, watch it fire, then **tune away one real false positive** —
the difference between a noisy demo and something a SOC would actually keep enabled.

> **One light prediction, before the lab.** When the escape runs, which single syscall do you think
> most cleanly betrays it — the one you'd build the detection around? Most people say "the `mount`."
> Hold that thought; in the lab you'll see why the *write to the host binary* is the sharper,
> lower-noise signal, and `mount` is the one that generates the false positive you'll have to tune out.

## Learn (~3 hrs)

**Container isolation internals (~45 min)**
- [Julia Evans — "How containers work" (blog post)](https://jvns.ca/blog/2020/04/27/new-zine-how-containers-work/) (~15 min) — the clearest short read on namespaces + cgroups composing into "a process in a jail." Internalize this before the lab; the whole module rests on it.
- [Linux `capabilities(7)` man page](https://man7.org/linux/man-pages/man7/capabilities.7.html) (~15 min, skim) — skim the list and read `CAP_SYS_ADMIN`. This is the vocabulary behind what `--privileged` actually grants.

**The CVE itself (~1 hr)**
- [The original disclosure — "CVE-2019-5736: Escape from Docker and Kubernetes containers to root on host" (Adam Iwaniuk / Dragon Sector)](https://blog.dragonsector.pl/2019/02/cve-2019-5736-escape-from-docker-and.html) (~30 min) — the discoverers' own writeup, with the `/proc/self/exe` mechanism. Primary source; read it slowly.
- [NVD — CVE-2019-5736](https://nvd.nist.gov/vuln/detail/CVE-2019-5736) (~10 min) — the record and CVSS 8.6 vector; note the affected runc versions you'll pin in the lab.
- [MITRE ATT&CK T1611 — Escape to Host](https://attack.mitre.org/techniques/T1611/) (~15 min) — the technique your detection maps to; read the detection guidance and note T1610 (Deploy Container).

**Falco runtime detection (~1 hr)**
- [Falco docs — Rules](https://falco.org/docs/rules/) (~30 min) — the rule language: read **Conditions**, **Output**, **Macros**, and **Exceptions**. This is exactly the vocabulary you tune with.
- [Falco docs — Event sources / how Falco works](https://falco.org/docs/concepts/event-sources/) (~15 min) — how it taps syscalls via eBPF; builds the mental model before you watch it fire.

## Key concepts
- A container is a host process with namespaces/cgroups/capabilities — **not** a VM; there is no hypervisor boundary
- The boundary you trust is the **shared kernel**; escape = abusing a resource both sides touch (host binary, device, socket, host path)
- CVE-2019-5736: overwrite the host `runc` binary from inside the container via a `/proc/self/exe` symlink → root on host
- `--privileged` and `docker.sock` mounts are *configuration* escapes that need no CVE — same shared-kernel hallway, different door
- Defenses layer because the kernel can't be un-shared: reduce what's *allowed* (caps, seccomp, non-root, admission) **and** watch what's *done* (Falco)
- Runtime detection catches behavior that static scan + admission can't see — it reads syscalls, not images
- Signal-vs-noise tuning: a rule that fires on the escape and stays silent on benign work; the tuned rule is detection-as-code

## AI acceleration
Paste a Falco rule's YAML into a model and ask it to (a) explain in plain English what syscall pattern it catches, (b) name a benign workload that would trip it, and (c) draft the `exception` that suppresses that workload without blinding the rule to the attack. It is genuinely good at rule *syntax* and at imagining edge cases — but it **cannot** tell you whether the rule is noisy in *your* environment, because that depends on what your containers actually do. So treat its draft as a hypothesis: you validate every variant against real Falco output from `make demo` before you keep it. AI drafts the rule; you own whether it fires on the right thing.
