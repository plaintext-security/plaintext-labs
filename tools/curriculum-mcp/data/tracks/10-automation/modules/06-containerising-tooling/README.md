# Module 06 — Containerising Tooling

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *a security tool in a Dockerfile is a tool that runs the same way, everywhere, forever.*

## Why this matters
Security tooling has a dependency problem: `volatility3` needs Python 3.9, the IDS needs
libpcap 1.10, the scanner needs a specific OpenSSL version, and the analyst's laptop has none
of those. Containerising a tool packages it with its exact dependencies — the tool runs
identically on a laptop, a CI runner, and a production server, with no "works on my machine"
debugging. For security tools specifically, container isolation also limits blast radius: a
scanner that runs inside a container cannot touch the analyst's host filesystem unless
explicitly allowed.

## Objective
Write a Dockerfile for a security tool (`trufflehog`) that produces a reproducible, runnable
image; understand the security implications of Dockerfile choices; and apply best practices
that reduce the image attack surface.

## The core idea
A Dockerfile is a recipe for a reproducible environment — layer by layer, from a base image
to a runnable tool. The security implications start with the base image: `FROM ubuntu:latest`
pulls whatever Ubuntu is current on build day, which changes over time and includes everything
Ubuntu ships by default. `FROM ubuntu:22.04` pins the OS version; `FROM
cgr.dev/chainguard/static` (or `FROM scratch`) gives you almost nothing except the binary,
dramatically reducing the attack surface. For security tooling, a smaller base image is almost
always better: less software means fewer CVEs.

Layer ordering matters for both cache efficiency and security. Put instructions that change
rarely near the top (`RUN apt-get install -y ca-certificates`) and instructions that change
often near the bottom (`COPY . /app`). This maximizes Docker's layer cache and minimizes
rebuild time. More importantly, never put secrets in any layer — not even a layer that's later
overridden with `RUN rm`. Docker history preserves all layers; a secret in a `RUN echo "key=x"`
command is visible in `docker history --no-trunc`. Pass secrets at runtime via environment
variables or secret mounts, never at build time in the Dockerfile.

Non-root user is the most important security hardening step for a container: `RUN useradd -m
scanner && USER scanner` before the final `CMD`. A container running as root can, if compromised,
escape to the host in certain configurations. A container running as a non-root user is
significantly harder to escalate. This is a CIS Docker Benchmark requirement and a check that
`checkov` will flag if missing.

`ENTRYPOINT` vs `CMD` is a common point of confusion: `ENTRYPOINT` is the command that always
runs; `CMD` is its default arguments. The pattern for a security tool is
`ENTRYPOINT ["/app/trufflehog"]` with no `CMD`, so the caller always provides the arguments.
This prevents the tool from running with dangerous default arguments if someone `docker run`s
the image without arguments.

## Learn (~2 hrs)

**Dockerfile best practices (~1 hr)**
- [Docker security best practices — Docker docs](https://docs.docker.com/build/building/best-practices/) — read the full page; covers non-root user, secrets, read-only filesystems, and image signing.
- [CIS Docker Benchmark — Center for Internet Security](https://www.cisecurity.org/benchmark/docker) — skim sections 4 (container images) and 5 (container runtime); the benchmark items map to Dockerfile instructions.

**Minimal base images (~1 hr)**
- [Chainguard Images — distroless containers](https://www.chainguard.dev/containers) — understand why minimal base images reduce CVE exposure; read the "Why distroless?" section.
- [trufflehog — GitHub](https://github.com/trufflesecurity/trufflehog) — the tool you're containerising; read the README to understand its CLI and how it's normally installed.

## Key concepts
- Base image pinning: `FROM ubuntu:22.04` not `FROM ubuntu:latest`
- No secrets in Dockerfile layers — ever, including deleted ones
- Non-root user: `RUN useradd && USER` before `CMD` — CIS Docker Benchmark requirement
- `ENTRYPOINT` + no `CMD` for tools; `CMD` for default-argument containers
- Layer ordering: stable layers first, volatile layers last

## AI acceleration
Ask a model to write the Dockerfile. It will usually produce a functional one. Then ask it to
apply the security best practices: non-root user, pinned base image, no secrets in layers, and
minimal package installs. Compare the first draft to the hardened version — the diff is the
list of things the model didn't consider by default. Run `checkov -f Dockerfile` on both and
compare findings.
