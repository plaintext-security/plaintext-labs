# Lab 03 — Run, Build, and Inspect a Container

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/03-docker
make demo   # build and run the demo server, inspect the running user
```

Docker must be installed on your host. No compose needed — the demo uses Docker directly.

## Scenario
Get fluent with the container lifecycle you'll use in every later lab — and notice one
security-relevant default.

## Do
1. [ ] Run an interactive throwaway container, look around its filesystem, and exit — confirm
   it's gone afterward.
2. [ ] Run a service container (e.g. a web server), publish a port, and reach it from your
   host.
3. [ ] Write a minimal `Dockerfile` that adds one tool to a base image; build and run it.
4. [ ] Inspect a running container's processes and check what user it runs as. (Is it root?
   Why might that matter?)

## Success criteria — you're done when
- [ ] You can run, list, and remove containers and images by hand.
- [ ] You published a port and reached the service from your host.
- [ ] You built and ran your own image from a Dockerfile.
- [ ] You can say what user your container runs as and why root-by-default is a risk.

## Deliverables
`docker-notes.md`: your Dockerfile, the `docker run` lines you used, and one note on a
security-relevant default you found.

## AI acceleration
Have a model generate a Dockerfile, then review it line by line for a non-root user, a pinned
base image, and no secrets baked in — the things it routinely omits.

## Connects forward
This is the substrate for every lab in the curriculum, and the groundwork for Track 05
(container & Kubernetes security).

## Marketable proof
> "I'm fluent with containers — run, build, inspect, and reason about their isolation model
> — which is how every modern security lab and pipeline runs."

## Automate & own it
**Required.** Commit a small `Dockerfile` you wrote — AI may draft it, but you review it for a
non-root user, a pinned base image, and no baked-in secrets before committing.

## Stretch
- Run a container as a non-root user with a read-only filesystem; note what breaks and what
  that buys you.
