# Lab 06 — Containerising Tooling

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/06-containerising-tooling
make demo      # builds the trufflehog image and runs it against data/seed-repo/
make shell     # shell inside the built container
make down      # remove the image
```

`data/seed-repo/` is a small git repository with three files: one that's clean, one with a
hardcoded AWS key (for demo purposes — use a revoked test key format), and one with a
high-entropy string that looks like a secret. Your Dockerfile builds a minimal `trufflehog`
container. No pre-built image is provided — you write the Dockerfile from scratch.

> **Authorization note:** `trufflehog` scans git history. Run it only against repositories you
> own or have explicit written authorization to scan.

## Scenario
Meridian wants a standardized `trufflehog` container that any engineer can pull and run
against a repository without installing Go or managing version conflicts. Your task: write the
Dockerfile, verify it runs cleanly, and apply the security hardening practices from the module.

## Do
1. [ ] `make demo` first — it will fail (no Dockerfile yet). Read the error to confirm what's
   missing.
2. [ ] Write `Dockerfile`:
   - `FROM ubuntu:22.04` (pinned).
   - Install `curl` and `ca-certificates` to fetch the `trufflehog` binary.
   - Download the `trufflehog` binary from its GitHub releases page (pin the version:
     `v3.88.1`); verify its SHA256 checksum before installing.
   - Create a non-root user `scanner` and `USER scanner`.
   - `ENTRYPOINT ["/usr/local/bin/trufflehog"]`.
3. [ ] Run `make demo` — confirm it builds and `trufflehog` finds the AWS key in the seed repo.
4. [ ] Run `checkov -f Dockerfile` — read every finding. Fix any HIGH findings.
5. [ ] Run `docker history plaintext/trufflehog --no-trunc` — confirm no secrets appear in any
   layer. (The download URL is not a secret; the tool binary is not a secret.)
6. [ ] Test the kill-switch: confirm `docker stop` terminates the container cleanly (the
   `trufflehog` binary handles SIGTERM).

## Success criteria — you're done when
- [ ] `make demo` builds the image and runs `trufflehog` cleanly.
- [ ] `trufflehog` correctly identifies the hardcoded key in `data/seed-repo/`.
- [ ] The container runs as the non-root `scanner` user.
- [ ] `checkov -f Dockerfile` shows no HIGH findings.
- [ ] No secrets appear in `docker history`.

## Deliverables
`Dockerfile` + `Makefile` (with `up`, `down`, `reset`, `demo`, `shell` targets). Commit both.

## Automate & own it
**Required.** Add a `make scan` target that runs the container against a directory passed as
`DIR=/path/to/repo make scan`. Have a model draft the Makefile target with the correct `docker
run -v` mount syntax; verify that the mount is read-only (`-v /path:/scan:ro`) so the container
cannot modify the target repository. Commit the updated Makefile.

## AI acceleration
Ask a model to write the Dockerfile for `trufflehog`. Then apply the security checklist: is the
base image pinned? Is there a non-root user? Is the binary checksum verified before install?
Does the model include the checksum verification step, or does it just `curl | sh`? The
checksum step is the model's most common omission — and the supply-chain attack it prevents is
real.

## Connects forward
The Dockerfile pattern from this module is used in every subsequent lab that ships a containerised
tool. Module 07 uses a multi-container compose pattern built on the same Dockerfile skills.

## Marketable proof
> "I containerise security tools with minimal, pinned base images, non-root users, and checksum-
> verified binary installs — so every engineer runs the same version of the tool, safely."

## Stretch
- Rebuild the image with a `cgr.dev/chainguard/static` base (using a pre-compiled binary) —
  compare the final image size and the `checkov` finding count between the two base images.
- Add a `docker scout` or `trivy` scan step to the Makefile that reports CVEs in the built image.
