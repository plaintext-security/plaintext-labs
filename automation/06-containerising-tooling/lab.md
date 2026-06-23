# Lab 06 — Containerising Tooling

*Hands-on lab · [← Back to the module concept](README.md)*

**Type:** Tool-Build — you ship a reusable, documented tool image others run, not a one-off `docker run`.

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/06-containerising-tooling
make demo      # builds the trufflehog image and runs it against data/seed-repo/
make shell     # shell inside the built container
make scan DIR=/path/to/repo   # run the packaged tool against any local repo
make down      # remove the image
```

`data/seed-repo/` is reconstituted from a committed bundle (`make seed`): a small git repository
with three files — one clean, one with a hardcoded AWS-key-shaped string (a revoked/test-format
key, never a live credential), and one with a high-entropy string that looks like a secret. No
pre-built image is provided — **the point of the lab is that you build the tool image yourself**:
the starter `Dockerfile` is a placeholder that fails `make demo` until you write the real one.

> **Authorization note:** `trufflehog` scans git history for secrets. Run it only against
> repositories you own or have explicit written authorization to scan.

## Scenario

Your team keeps re-installing `trufflehog` by hand — different Go versions, different binary
versions, "works on my machine" results that don't reproduce in CI. The fix is to ship it **once,
as a tool image**: any engineer pulls and runs it against a repository without installing Go or
chasing version conflicts, and everyone gets the same result. Your job is to build that image to a
tool standard — clear entrypoint and usage, non-root by default, a pinned and checksum-verified
binary on a pinned minimal base, and a short README so the next person can run it without reading
the Dockerfile.

This is a **Tool-Build**: the deliverable is a reusable product, judged on whether someone *else*
can build it and run it safely — not just on whether it ran once for you.

## Do

1. [ ] **Confirm the starting state.** Run `make demo` — it fails (the placeholder Dockerfile exits
   with a clear message). Read it; that's your spec to fill.
2. [ ] **Build the tool image** in `Dockerfile`:
   - `FROM ubuntu:22.04` — base **pinned**, not `latest`.
   - Install only what's needed to fetch the binary (`curl`, `ca-certificates`) and clean
     `/var/lib/apt/lists` in the same layer.
   - Download the `trufflehog` binary from its GitHub releases, **version-pinned** (`v3.88.1`), and
     **verify its SHA256 checksum before installing** — fail the build if it doesn't match.
   - Create a non-root user `scanner` and `USER scanner` before the entrypoint.
   - `ENTRYPOINT ["/usr/local/bin/trufflehog"]` and **no `CMD`** — so the image behaves like the
     command and `docker run image --help` reaches the real tool.
3. [ ] **Prove it works.** `make demo` builds and `trufflehog` flags the hardcoded key in
   `data/seed-repo/`. Then `docker run --rm plaintext/trufflehog:1.0 --help` — confirm the tool's
   own usage prints (the image is a tool, not a black box).
4. [ ] **Run it as a tool against arbitrary input:** `make scan DIR=$(pwd)` on some repo you own —
   confirm the mount is read-only (`-v …:/scan:ro`) so the tool cannot modify what it scans.
5. [ ] **Hold it to the reviewer's bar.** `checkov -f Dockerfile` — read every finding, fix the
   HIGH ones (non-root and pinning are the usual hits).
6. [ ] **Prove no secret leaked into a layer:** `docker history plaintext/trufflehog:1.0
   --no-trunc` — confirm nothing sensitive appears (the download URL and the tool binary are not
   secrets).
7. [ ] **Confirm the kill-switch:** `docker stop` terminates the container cleanly (the binary
   handles SIGTERM).
8. [ ] **Write the README** (below) so the tool is usable without reading the Dockerfile.

## Success criteria — you're done when

- [ ] `make demo` builds the image and runs `trufflehog` cleanly against `data/seed-repo/`.
- [ ] `trufflehog` correctly identifies the hardcoded key in the seed repo.
- [ ] `docker run plaintext/trufflehog:1.0 --help` prints the tool's usage (clear entrypoint, no surprising default action).
- [ ] The container runs as the non-root `scanner` user (`docker run --rm --entrypoint id plaintext/trufflehog:1.0` shows a non-zero uid).
- [ ] `checkov -f Dockerfile` shows no HIGH findings.
- [ ] No secret appears in `docker history --no-trunc`.
- [ ] The base image and the tool version are both pinned, and the binary's checksum is verified in the build.
- [ ] A short `README.md` documents build + usage; another engineer could run the tool from it alone.

*Honor system: these are observable on your own machine — run the commands and check your own work. No grader.*

## Deliverables

The packaged tool, as a build-anyone-can-reproduce:

- `Dockerfile` — the hardened, pinned, non-root, checksum-verified image.
- `Makefile` — `up`/`down`/`reset`/`demo`/`shell` plus the `scan` target.
- `README.md` — the **tool's usage doc**: one-line what-it-is, how to build, how to run
  (`make scan DIR=…` and the raw `docker run …` line), the version it pins, and the
  authorization note. This is part of the deliverable, not an afterthought — a tool without a
  README isn't a tool someone else can run.

Lab *artifacts* (scan output, the seed repo, any captured findings) stay out of commits.

## Automate & own it

**Required.** Make the image genuinely reusable by another person, not just runnable by you:

- Add/confirm the `make scan` target that runs the container against `DIR=/path/to/repo make
  scan`. Have a model draft the `docker run -v` line, then **verify every part yourself**: the
  mount is **read-only** (`-v "$(DIR):/scan:ro"`) so the tool can't modify the target, and the
  args after the image reach the entrypoint correctly.
- Write the `README.md` usage doc above. Let a model draft it from your Dockerfile + Makefile, then
  review every claim against what the image actually does (the pinned version, the entrypoint
  behaviour, the read-only mount) — a usage doc that lies is worse than none.

Commit the Makefile target and the README alongside the Dockerfile. **AI drafts → you review every
line → you own the tool.**

## AI acceleration

Ask a model to write the Dockerfile for `trufflehog`, then run it through the tool checklist: is
the base image pinned? the tool version pinned? a non-root user? is the binary checksum verified
before install, or does it `curl | sh`? The checksum step is the model's most common omission —
and the supply-chain attack it prevents (a tampered binary swapped at the CDN) is real. Diff the
first draft against your hardened version; that diff is the module's lesson made concrete.

## Connects forward

The tool-image pattern here — pinned minimal base, non-root, clear entrypoint, checksum-verified
binary — is reused by every later lab that ships a containerised tool. Module 07 builds a
multi-container enrichment pipeline directly on these Dockerfile skills, and the CI/CD module
operates a pipeline that builds and scans images like this one.

## Marketable proof

> "I package security tools as pinned, non-root, minimal-base images with checksum-verified
> binaries, a clear entrypoint, and a usage README — so any engineer runs the same version of the
> tool, safely, without a local install."

## Stretch

- Rebuild on a `cgr.dev/chainguard/static` (or distroless) base using a pre-compiled static binary
  — compare final image size and `checkov` finding count between the two bases; note the CVE-surface
  difference in your README.
- Add a `make image-scan` target that runs `trivy` (or `docker scout`) against the built image and
  reports CVEs — your tool image should pass its own kind of scan.
