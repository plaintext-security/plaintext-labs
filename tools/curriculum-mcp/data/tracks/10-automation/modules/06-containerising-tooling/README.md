# Module 06 — Containerising Tooling

*Type 9 · Tool-Build — package a security tool (trufflehog) as a reusable, hardened container image others can run; the deliverable is the published image with a non-root user, minimal base, and a clean ENTRYPOINT. (Secondary: Build-&-Operate.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *package a security tool once, as an image others run, and it runs the same way everywhere — pinned, non-root, with a clear `--help`.*

<!-- module-meta -->
**Type:** Tool-Build (Family II) &nbsp;·&nbsp; **Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

A security tool is only useful if it runs — reliably, the same way, for whoever picks it up next.
Un-containerised tooling fails exactly there. `volatility3` wants one Python, the IDS wants a
specific `libpcap`, the scanner wants an OpenSSL that conflicts with the one your distro shipped,
and the next analyst's laptop has none of it. The result is the most familiar failure in security
engineering: *"works on my machine."* The same tool gives different results on a laptop, a CI
runner, and an incident-response box — or simply won't install — and the time goes into dependency
archaeology instead of the investigation.

There's a sharper edge for security tools specifically: an un-pinned install is a supply-chain
exposure. The `curl | bash` install that grabs "latest" from a CDN, or a `FROM ubuntu:latest`
that resolves to a different image every build, means the thing you ran today is not provably the
thing you ran last month. When the tool's job is to *find* secrets and vulnerabilities, you want it
to be the most boring, reproducible, auditable artifact in your kit — not the one piece you can't
account for.

This is not hypothetical. Between mid-2017 and 2018 an account named **docker123321** published
[17 backdoored images on Docker Hub](https://www.bleepingcomputer.com/news/security/17-backdoored-docker-images-removed-from-docker-hub/),
named to look like ordinary `tomcat`, `mysql`, and `cron` images. They sat on the public registry
for roughly a year and were pulled around **5 million times** — some images over a million each —
quietly running XMRig Monero miners and embedded reverse shells on whoever `docker pull`ed them.
Fortinet and Kromtech traced the campaign back to the single account, and Docker removed the images
in May 2018; the miner alone netted about $90,000. The lesson is the one this module turns on:
`docker pull <something>` is "run arbitrary binary data and hope for the best" unless *you* control
and pin what goes in — which is exactly the discipline you apply when you build the image yourself.

This module's product is that artifact: a security tool packaged as a **reusable image** —
something an engineer pulls and runs without installing Go, resolving versions, or trusting an
unpinned script. The deliverable is judged the way a tool is judged: does it have a clear
entrypoint and usage, does it run safely by default, can someone else build it and get the same
result.

## The core idea

A Dockerfile is the recipe for a tool other people run, so the design judgments are *tool* design
judgments, not just packaging. Four of them carry the weight.

**The base image is a dependency you're choosing — pin it and keep it small.** `FROM ubuntu:latest`
pulls whatever is current on build day and ships everything Ubuntu installs by default; every one
of those packages is attack surface and a potential CVE in *your* tool's image. `FROM ubuntu:22.04`
pins the OS so the build is reproducible. A minimal base — `cgr.dev/chainguard/static`, distroless,
or `FROM scratch` for a static binary — gives you almost nothing but the tool itself: far fewer
packages, far fewer CVEs, a far smaller artifact to push and pull. For a security tool the rule of
thumb is unambiguous: less in the image is better. Pinning isn't only the OS — pin the *tool*
version too (`v3.88.1`, not "latest") and verify its checksum before you install it, so the binary
in the image is provably the one you intended.

**Run as non-root, always.** This is the single most important hardening step and the one a model
most often skips. `RUN useradd -m scanner && USER scanner` before the entrypoint means a
compromised container starts with far less to work with; a root container can, in some
configurations, escape to the host. It's a CIS Docker Benchmark item and a `checkov` check —
which is to say it's the kind of thing a reviewer (human or scanner) will hold the tool to.

**`ENTRYPOINT` is the tool; `CMD` is its default arguments — and the distinction is a usability
decision.** A tool image should set `ENTRYPOINT ["/usr/local/bin/trufflehog"]` and *no* `CMD`, so
`docker run image <args>` behaves exactly like running the tool with those args — and running it
with no args prints the tool's own usage rather than doing something surprising. That's what makes
the image feel like a command, not a black box: the caller's `--help` reaches the real tool, and
there are no dangerous baked-in defaults.

**Never put a secret in a layer — not even one you delete.** Docker keeps every layer; a key in
`RUN echo "key=x"` is visible in `docker history --no-trunc` even if a later layer `rm`s the file.
Secrets are passed at *runtime* (env vars, secret mounts, a read-only volume), never baked at build
time. Layer ordering is the cheaper companion rule: put what changes rarely near the top
(`apt-get install ca-certificates`) and what changes often near the bottom (`COPY . /app`), so the
cache does the work and rebuilds stay fast.

The load-bearing judgment across all four: a tool image is a product with users. What you pin,
what you keep out, what the entrypoint exposes, and what you refuse to bake in are the same kinds
of decisions you'd make designing any reusable tool — they just happen to be written in a
Dockerfile.

## Learn (~2 hrs)

**Dockerfile best practices (~1 hr)**
- [Building best practices — Docker docs](https://docs.docker.com/build/building/best-practices/) — read the full page; covers layer ordering, pinning, multi-stage builds, and keeping images small. The reference for *why* the Dockerfile is shaped the way it is.
- [Docker security — non-root, secrets, read-only — Docker docs](https://docs.docker.com/engine/security/) — read the "Docker daemon attack surface" and run-as-non-root guidance; this is the runtime side of the hardening the lab applies.
- [CIS Docker Benchmark — Center for Internet Security](https://www.cisecurity.org/benchmark/docker) — skim sections 4 (container images) and 5 (container runtime); each benchmark item maps to a concrete Dockerfile instruction, so it doubles as your hardening checklist.

**Minimal base images & the tool (~1 hr)**
- [Chainguard Images — "Why distroless?" — Chainguard](https://www.chainguard.dev/containers) — read the "Why distroless?" framing for the concrete argument that fewer packages means fewer CVEs; this is the case for the minimal-base stretch goal.
- [17 backdoored Docker Hub images removed — BleepingComputer](https://www.bleepingcomputer.com/news/security/17-backdoored-docker-images-removed-from-docker-hub/) (~10 min) — the docker123321 case (Fortinet/Kromtech): legit-looking images, ~5M pulls, cryptominers + reverse shells. Read it for *why* you pin and build, not blindly pull.
- [trufflehog — GitHub README](https://github.com/trufflesecurity/trufflehog) — the tool you're packaging; read the README's usage and the `git`/`filesystem` source sections so your image's entrypoint and `--help` expose the right surface.

## Key concepts

- **`docker pull` is running someone else's binary:** the docker123321 images (17 backdoored, ~5M pulls, miners + reverse shells) are why you pin and build rather than trust a legit-looking name.
- **Pin everything reproducible:** the base image (`ubuntu:22.04`, not `latest`) *and* the tool version (`v3.88.1`) — verify the binary's checksum before install.
- **Minimal base = fewer CVEs:** prefer distroless/`scratch`/Chainguard where the tool allows it; less software is less attack surface.
- **Non-root, always:** `useradd` + `USER` before the entrypoint — CIS Docker Benchmark, a `checkov` HIGH if missing.
- **`ENTRYPOINT` is the tool, no `CMD`:** the image behaves like the command; `--help` reaches the real tool; no surprising default action.
- **No secrets in any layer:** `docker history` keeps deleted layers; pass secrets at runtime, never at build.
- **Order layers stable→volatile:** rare changes up top for cache, frequent changes (`COPY`) at the bottom.

## AI acceleration

Ask a model to write the Dockerfile and it will hand you a *functional* one — and a revealing one,
because the gap between its first draft and a production tool image is the checklist this module
teaches. Then ask it to harden: pin the base *and* the tool version, add the checksum verification,
add a non-root user, drop unneeded packages, fix the entrypoint. The diff between the two drafts is
the list of things the model didn't consider by default; the omission to watch for is the checksum
step — models reliably skip it, and it is exactly the supply-chain control that makes the image
trustworthy. Then close the loop the way a reviewer would: run `checkov -f Dockerfile` on both
versions and confirm the hardened one clears the HIGH findings. **AI drafts → you review every line
→ you own the image that ships.**
