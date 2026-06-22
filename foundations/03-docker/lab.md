# Lab 03 — Run, Build, and Inspect a Container (and See Where Isolation Ends)

*Variant D · skill-first, one light predict. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It builds and runs a
small demo web service and walks the container lifecycle for you, then you redo it by hand.

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/03-docker
make demo    # build + run the sample app, publish a port, inspect the running user
make clean   # remove the demo image when done
```

Docker must be installed on your host (you isolated this in module 02). No compose needed — the demo
uses Docker directly.

> Only run containers and images you trust or built yourself. This lab uses a small sample app shipped
> in the repo and stock public base images — nothing here attacks a remote target.

## Scenario
Get fluent with the container lifecycle you'll use in every later lab — and prove to *yourself*, with
`docker inspect` and `/proc`, the one fact from the module: a container is a host process with a
restricted view, not a sealed machine. You'll watch namespaces and cgroups do the isolating, and watch
the shared kernel set the limit.

## Do

1. [ ] **Throwaway container — run, look, exit.**
   Run an interactive throwaway container from a small base image (e.g. `alpine`), look around its
   filesystem, and exit. Confirm with `docker ps -a` that `--rm` cleaned it up. *Goal: the run/inspect/
   remove loop is reflexive.*

2. [ ] **Service container — build, publish, reach.**
   Build the sample app's image from its `Dockerfile`, run it detached, **publish a port** to your host,
   and `curl` the service. *Goal: read a `docker run -p` line and know exactly what it exposed.*

3. [ ] **Predict, then prove: is this a separate machine?**
   **Predict:** before you look — when you list processes *inside* the container, will you see your
   host's processes? Will the container have its own process IDs? Write your guess.
   **Do:** exec into the running container and run `ps aux` (it sees only its own processes, and your
   app is PID 1 — a namespace). Then, on the **host**, run `ps aux` and find that same container process
   — it's right there in the host's process list with a host PID. **Reveal:** same process, two views.
   The container's "PID 1" is just a normal host process wearing a PID namespace. *Goal: feel that
   "isolated" means filtered-view, not separate-computer.*

4. [ ] **See the isolation, and its limit.**
   Inspect the kernel features doing the work: `docker inspect <container>` (look at the namespaces,
   mounts, and any `Privileged` / capability fields), and `cat /sys/fs/cgroup/...` or
   `docker stats` to see the cgroup limits. Then confirm the shared kernel directly: run
   `uname -r` **inside** the container and **on the host** — *same kernel version*, because it's the
   same kernel. *Goal: name what isolates the container (namespaces + cgroups) and what limits that
   isolation (the shared kernel).*

5. [ ] **Find the security-relevant default.**
   Check what **user** the container runs as: `docker run --rm <image> whoami`. It's `root`. Note why
   that matters — root in the container, on a shared kernel, is one missing restriction away from root on
   the host (the module's case). Then write a tiny `Dockerfile` that fixes it: pin the base image by
   tag, add a non-root user, and `USER` to it before `CMD`. Build, run, and confirm `whoami` now prints
   your user. *Goal: a Dockerfile you wrote and can defend line by line.*

## Success criteria — you're done when
- [ ] You can run, list, and remove containers and images by hand, and published a port you reached with `curl`.
- [ ] You showed the **same container process from two views** (host PID list vs. namespaced `ps` inside) and can say why it's one process, not two machines.
- [ ] You confirmed the **shared kernel** (`uname -r` matches inside and on the host) and can name namespaces and cgroups as what isolates the container.
- [ ] You built and ran your **own** image from a Dockerfile, and it runs as a **non-root** user.
- [ ] You scored your step-3 prediction against what you saw, and can state in one sentence why a container is not a sealed machine.

## Deliverables
`docker-notes.md` — your fixed `Dockerfile`, the `docker run` lines you used, the `uname -r` output from
inside and host side by side, and one paragraph: *what isolates a container, and where that isolation
ends.* Commit the notes and the Dockerfile. Do **not** commit images, container logs, or anything the
containers wrote out.

## Automate & own it
**Required.** Turn your manual `inspect` pass into a small reviewable script — `inspect.py` (or `.sh`)
that takes a container or image name and prints the things you checked by hand: the running **user**,
whether it's **privileged**, its capabilities, its **mounts** (flagging any that mount a host path like
`/` or `/var/run/docker.sock`), and the kernel version. In other words, a tiny "is this container box
leaky?" reporter built on `docker inspect`. Have a model draft it; **review every line** — confirm it
actually flags a privileged container and a host-root mount (test it against one you deliberately run
that way), and that it doesn't shell out unsafely on the name you pass it. Commit it beside your notes.

## AI acceleration
Ask a model to generate a Dockerfile for the sample app. Then audit its output against the module's
list: pinned base image (not `latest`), a non-root `USER`, no secrets baked into layers, no
`--privileged` in any run instructions, no broad volume mounts. Models routinely omit the non-root user
and the pinned tag — catching that is the skill. Then point your `inspect.py` at a container and ask the
model to find a misconfiguration your script *misses*; if it can, widen the script.

## Connects forward
This is the substrate for every later lab in the curriculum, and the direct groundwork for the
container & Kubernetes security track, where "removing restrictions on a host process" becomes a real
container escape. Your `inspect.py` is the seed of a posture check — the same review reflex that, in the
cloud track, audits a generated IAM policy for the over-broad default.

## Marketable proof
> "I'm fluent with containers — I can run, build, publish, and `inspect` them, show the same process
> from the host and from inside its namespaces, and explain why a container shares the host kernel and
> is *not* a security boundary by default. I wrote a small script that flags a privileged or
> host-mounting container."

## Stretch
- Run a container as a non-root user **with a read-only root filesystem** (`--read-only`) and dropped
  capabilities (`--cap-drop ALL`); note what breaks, what you had to add back, and what that buys you.
- Deliberately run one container `--privileged` and one with `-v /:/host`, point `inspect.py` at both,
  and from inside, read a file off the real host to *feel* the hole the module described — on a VM you
  own and can throw away.
