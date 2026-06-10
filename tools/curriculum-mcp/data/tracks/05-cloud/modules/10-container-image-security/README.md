# Module 10 — Container & Image Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *the image is your artifact: if you ship a vulnerable image, you ship a vulnerable workload.*

## Why this matters
Container supply-chain attacks are no longer theoretical. The 2020 SolarWinds compromise made the pipeline itself the attack surface; the 2021 CodeCov supply-chain breach showed that a build script you curl-pipe is an unsigned trust extension. In Kubernetes clusters, a single vulnerable base image can be the foothold that lets an attacker move from one pod to the entire node. Meridian Financial's security team discovered, during a routine audit, that three production images were running a base OS with a critical CVE patched six months earlier — no one had rebuilt the images since the initial push.

## Objective
Scan real container images and a deliberately misconfigured `Dockerfile` with `trivy` and `grype`, interpret severity and fixability, and produce an image-hygiene report — the kind of artefact that gates a pull request before a flawed image reaches the registry.

## The core idea
Container images are layered archives: a base OS layer, one or more package layers, and your application layer. The supply-chain risk lives primarily in the base and package layers, not in your code. An image tagged `python:3.8-slim` is a snapshot of a Debian root filesystem at the time someone built it. Time passes; CVEs accumulate in `curl`, `libssl`, `glibc`. But because the image tag is static and the registry cached the old digest, every container you start from that tag is running the old bits. **Tags are mutable; digests are immutable.** Pinning `python:3.8-slim@sha256:...` and rebuilding on a schedule is the discipline that closes this gap — not a one-shot scan at build time.

Vulnerability scanners like `trivy` and `grype` work by extracting the software bill of materials (SBOM) from an image — every OS package and its version — and matching it against CVE databases (NVD, GitHub Advisory, OS-vendor advisories). The result is a list of CVEs, their CVSS scores, and whether a patched version exists in the distro's repositories. The critical judgment call is **fixability**: a Critical CVE with no fix available is noise until the upstream patches; a High CVE with a fix means rebuild now. Tools let you set a `--severity` threshold and `--exit-code 1` so a CI step fails on severity-or-above-with-fix, which is the right gate.

Dockerfile hygiene catches a different class of risk: configuration mistakes that images introduce deliberately. Running as root (`USER root`, or no `USER` directive at all) means every process in the container is UID 0 — and if a container escape succeeds, the attacker lands as root on the host too. Pinning `FROM python:3.8-slim` not `FROM python:latest` ensures the build is reproducible and auditable. Embedding secrets in `ENV` or `ARG` lines bakes them into the image manifest, where anyone with registry access can extract them with `docker inspect` or `docker history`. The `--privileged` flag in a compose file gives the container every Linux capability and drops most kernel namespace protections — effectively a root shell on the host. Trivy's `--scanners config` mode and `hadolint` catch these before a human does.

The practitioner move is to treat scanning as a pipeline gate, not a periodic audit. Image scanning at build time (`trivy image --exit-code 1 --severity HIGH,CRITICAL`) means a vulnerable image never reaches the registry. Base-image update automation (Dependabot for Docker base images, or a weekly rebuild CI job) keeps the baseline fresh. SBOM generation as a build artefact — `trivy sbom --format cyclonedx` — means you can retrospectively ask "was Log4Shell in anything we shipped in November 2021?" without rebuilding the old images. Meridian Financial's team now requires all images pass the scanner gate before promotion to their ECR production repository, and a nightly job rescans everything in production against the latest CVE feed.

## Learn (~3 hrs)

**Container image structure & supply chain (~1 hr)**
- [Docker's "Overview of best practices for writing Dockerfiles"](https://docs.docker.com/build/building/best-practices/) — the canonical reference for image hygiene; pay particular attention to the multi-stage build and least-privilege sections.
- [SLSA Supply-chain Levels for Software Artifacts — Introduction](https://slsa.dev/spec/v1.0/about) — a 10-minute read on the framework that formalises supply-chain security levels; the vocabulary shows up in job descriptions.

**Trivy & Grype (~1 hr)**
- [Trivy documentation — Container image scanning](https://aquasecurity.github.io/trivy/latest/docs/target/container_image/) — official docs; read the "Scanning" and "Filter" pages to understand fixable vs. unfixable and severity thresholds.
- [Anchore Grype README](https://github.com/anchore/grype) — scan the README and the "Supported ecosystems" table; note how it compares to trivy's database sources.

**CVE severity & CVSS (~0.5 hr)**
- [NVD — CVSS v3.1 Scoring Guide](https://nvd.nist.gov/vuln-metrics/cvss) — the source of CVSS scores that trivy/grype surface; understand Base Score components (AV, AC, PR, UI) so you can assess "Critical in theory, unexploitable in this context."

**Container security posture (~0.5 hr)**
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html) — quick reference; maps directly to the Dockerfile.bad findings in the lab.

## Key concepts
- Container images are layered SBOM snapshots — tags are mutable, digests are immutable
- Fixable vs. unfixable CVEs: the difference between "rebuild now" and "track and wait"
- Dockerfile hygiene: non-root `USER`, pinned base tag, no secrets in `ENV`/`ARG`, no `--privileged`
- CVSS score ≠ exploitability in your context — filter by fixability and attack surface
- `--exit-code 1 --severity HIGH,CRITICAL` as the CI gate pattern
- SBOM generation for historical CVE queries (CycloneDX / SPDX formats)
- MITRE ATT&CK T1195.002 — Supply Chain Compromise: Compromise Software Supply Chain

## AI acceleration
Paste `docker history <image>` output and your `trivy` JSON report into a model and ask it to identify the highest-priority findings given Meridian's attack surface (internet-facing Python API, no privileged containers). It's good at ranking by fixability and suggesting the minimum base-image upgrade to close the most CVEs. What it cannot assess is whether a CVE is reachable from the actual execution path — that requires knowing what the code does. Treat its ranking as a first-pass triage; you own the exploitability judgement before filing a remediation ticket.
