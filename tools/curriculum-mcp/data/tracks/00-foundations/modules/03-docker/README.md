# Module 03 — Docker & Containers

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *every lab here is Docker-first; this is the literacy that assumes.*

## Why this matters
Containers are how modern software ships — and how every lab here runs, because they're
reproducible, disposable, and zero-cost. You need to read a `docker run` line, build an
image, and understand the isolation model well enough to both use containers and, later,
attack and defend them (Track 05). Skip this and every other lab is cargo-culting.

## Objective
Run, build, and inspect containers, and explain the isolation model well enough to use them
safely.

## The core idea
Containers are how modern software ships and how every lab here runs, so this is literacy you can't
skip — but the security-relevant insight beginners miss is the one to anchor on: **a container is not
a security boundary by default.** A container is just an ordinary Linux process whose *view* of the
world is narrowed by kernel features — namespaces isolate what it can see, cgroups limit what it can
use — while it still shares the host kernel. That's isolation, not the hard wall a VM gives you. That
single fact explains why `--privileged` and over-broad volume mounts are dangerous (they punch holes
straight back to the host) and why "container escape" in Track 05 is even a thing.

The practical literacy is small and high-leverage: **images** (the template) vs. **containers** (a
running instance) vs. **registries** (where images live); reading a `docker run` line — ports,
volumes, env, lifecycle — so you know exactly what a lab exposes; and building an image from a
**Dockerfile** so an environment is reproducible from text alone (which is what makes `plaintext-labs`
work).

The judgment: this is exactly where AI-generated infrastructure hides holes. A model writes a
`docker run` line or a Dockerfile instantly, and an over-broad `-v /:/host` mount or a stray
`--privileged` rides along looking perfectly innocent. Read every generated flag — and note that in
the cloud track this same reflex (review the generated config for the over-permissioned default) *is*
the job.

## Learn (~3 hrs)

**Hands-on basics**
- [Docker — Get Started](https://docs.docker.com/get-started/) — the official, hands-on intro: images, containers, volumes, ports.
- [TechWorld with Nana — Docker Tutorial for Beginners (full course, ~3 hrs)](https://www.youtube.com/watch?v=3c-iBn73dDE) — the clearest beginner-to-working walkthrough; the first hour (images, containers, ports, volumes) is enough for the lab.
- [Play with Docker](https://labs.play-with-docker.com/) — a free in-browser Docker host if you can't install locally.

**The security angle**
- [Docker docs — Engine security](https://docs.docker.com/engine/security/) — the isolation model, why `--privileged` is dangerous, and running as non-root.

## Key concepts
- Images vs containers vs registries
- `docker run` anatomy: ports, volumes, env, lifecycle
- Building an image with a Dockerfile
- The isolation model (namespaces/cgroups) — and its limits
- Why a container is not a security boundary by default

## AI acceleration
A model writes your Dockerfile or `docker run` line instantly — and that's exactly where
over-broad mounts and `--privileged` sneak in. Read every generated flag: a volume mount or
capability you didn't intend is a real hole.
