# Module 08 — CI/CD Pipeline Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *the build pipeline is the highest-trust path in your environment — and frequently the least scrutinised.*

## Why this matters
A compromised CI/CD pipeline has production access by design. When an attacker can modify a GitHub
Actions workflow or inject into a build step, they don't need to exploit your application — the
build system will package and deploy their payload for them. Supply-chain attacks (SolarWinds,
3CX, XZ Utils) all share this pattern: the compromise happened in the build, not the runtime.

## Objective
Scan a sample repository for secrets with `gitleaks`, scan a container image with `trivy` for
known CVEs, review a GitHub Actions workflow for pipeline misconfigurations, and build a hardened
CI workflow that gates on all three checks.

## The core idea

CI/CD security lives at the intersection of three concerns that practitioners usually treat
separately: secrets hygiene (are credentials in the pipeline?), supply chain (are the dependencies
and images you build from safe?), and pipeline configuration (does the workflow itself have
excessive permissions or injection points?). The supply-chain attack playbook connects all three:
plant a secret in the pipeline, compromise a dependency or base image, leverage a misconfigured
workflow to execute arbitrary code in the build environment with production credentials attached.

The container image surface is where `trivy` earns its place in a pipeline. Every base image
carries OS packages, and those packages accumulate CVEs over time. `python:3.8`, `node:14`, and
`ubuntu:20.04` are all past end-of-life, carrying dozens of known exploitable vulnerabilities —
yet they are still common in enterprise Dockerfiles because nobody ever updated the `FROM` line.
A `trivy image` scan against a registry tag before deployment costs seconds and catches this
pattern cold. The policy decision is the hard part: which CVE severities block the deploy, and
which are accepted-risk because a fix isn't available yet? That policy is a `trivy.yaml` or an
OPA/Rego policy file, not an afterthought.

The GitHub Actions misconfiguration surface is distinct and underappreciated. Every `${{
github.event.head_commit.message }}` passed unsanitised to a `run:` step is an injection point.
Every workflow with `permissions: write-all` is a blast-radius amplifier. Every `actions/checkout`
on a forked PR with `pull_request_target` is a classic "pwn-requests" pattern that has bitten
major open-source projects repeatedly. The CIS GitHub Actions benchmark and the StepSecurity
hardener are the tooling; understanding the threat model — untrusted input + shell execution =
code injection — is the mental model. MITRE ATT&CK for CI/CD (ATLAS and the DevSecOps community's
ATT&CK extension) maps these to technique families, but the practitioner summary is simple: treat
the YAML like application code, because it runs in your most privileged environment.

One operational note on `gitleaks` vs. `trufflehog`: they cover the same problem space with
different trade-offs. `trufflehog` verifies credentials live (makes API calls); `gitleaks` is
faster, fully offline, and config-file-driven (you can add custom patterns in a TOML file). For CI
gates, `gitleaks` is the standard choice — fast, no network dependency, predictable exit codes.
`trufflehog` belongs in an incident response or a deep scan where live-verification matters.

## Learn (~4 hrs)

**Container supply chain (~1.5 hrs)**
- [trivy documentation — vulnerability scanning](https://aquasecurity.github.io/trivy/latest/docs/scanner/vulnerability/) — how trivy scans images, the SBOM it generates, the database it queries (Aqua's Trivy DB + NVD), and how to configure severity thresholds. Read the "Container Image" and "Filtering" sections.
- [Docker Official Images — security and currency](https://docs.docker.com/docker-hub/image-library/trusted-content/) — why pinning a specific digest (`FROM python:3.12-slim@sha256:...`) is more secure than a tag, which is mutable.

**gitleaks (~1 hr)**
- [gitleaks — gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) — the README covers scan modes (detect, protect, git), the `.gitleaks.toml` config format for custom rules, and the CI integration pattern. Read all sections.
- [MITRE ATT&CK T1552.004 — Private Keys](https://attack.mitre.org/techniques/T1552/004/) — the technique gitleaks catches most often in practice.

**GitHub Actions security (~1.5 hrs)**
- [GitHub — Security hardening for GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use) — the authoritative GitHub guide: expression injection, `pull_request_target`, OIDC tokens, minimal permissions. Read the entire page.
- [StepSecurity — GitHub Actions hardening](https://app.stepsecurity.io/) — the free tool that audits a workflow YAML and suggests hardening. Useful for calibration even if you apply the fixes manually.

## Key concepts
- Image vulnerability scanning: OS packages + application dependencies, SBOM generation
- CVE severity policy: which severities block deploy, which are accepted-risk
- gitleaks: offline credential detection, custom rule patterns, CI integration
- GitHub Actions injection: `${{ }}` in `run:` steps, untrusted input sources
- `pull_request_target`: elevated permissions on forked PRs — the "pwn-requests" pattern
- OIDC tokens in CI: eliminating long-lived cloud credentials from pipeline configuration
- MITRE ATT&CK T1195 (Supply Chain Compromise), T1552 (Unsecured Credentials)

## AI acceleration
GitHub Actions YAML is an excellent target for AI-assisted review: paste a workflow file and ask
the model to find injection points, excessive permissions, and non-pinned action references. The
model is good at this pattern-matching. What it misses: subtle logic in multi-job dependencies
where a compromised step can pass data to a later privileged step. For image scanning policy,
the model can draft a `trivy.yaml` ignore file for accepted-risk CVEs — you must verify that each
accepted CVE has a documented rationale and that it is not exploitable given your specific threat
model (a CVE in a library your application never calls is different from one in a library on the
hot path).
