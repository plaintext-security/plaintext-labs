# Lab 10 — Scan and Fix a Vulnerable Container Image

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/10-container-image-security
make up        # pull scanner images (trivy + grype); no build required
make demo      # run both scanners against the known-vulnerable image and Dockerfile.bad
make shell     # drop into a scanner shell to run your own commands
make down      # stop when done
```

The environment provides:
- `trivy` and `grype` pre-pulled and aliased in a scanner container
- `data/Dockerfile.bad` — a deliberately misconfigured Dockerfile with seven common hygiene failures
- `data/Dockerfile.fixed` — the corrected version for comparison
- `make demo` runs a full scan pipeline and exits 0 — deterministic output, no network required after `make up`

> Everything runs locally. No external targets, no authorization required.

## Scenario
Meridian Financial's platform engineering team pushed three images to production six months ago without automated scanning. A compliance review just flagged them. You're brought in to: (1) assess the CVE exposure in the current base images, (2) audit the Dockerfile for hygiene failures, and (3) produce a gated CI pipeline so this can't ship again.

## Do

1. [ ] Run `trivy image python:3.8-slim` inside the scanner container.
   How many CVEs at CRITICAL and HIGH? How many are fixable (i.e., have a patched version)?
   *Hint: use `--severity HIGH,CRITICAL` to focus the output; use `--exit-code 1` to confirm the gate logic.*

2. [ ] Run `grype python:3.8-slim` and compare to trivy's output.
   Do both tools agree on the count? Where do they differ? What does that tell you about trusting a single scanner?

3. [ ] Scan `node:14` — another of Meridian's base images.
   Which image has more fixable CVEs? Which would you prioritize for a rebuild?

4. [ ] Run `trivy config data/Dockerfile.bad`.
   List every finding and map each one to the risk it represents.
   *Hint: look for `USER`, `FROM`, `ENV`, `ARG`, and `--privileged` issues.*

5. [ ] Open `data/Dockerfile.bad` and `data/Dockerfile.fixed` side by side.
   Confirm that each fix in `Dockerfile.fixed` closes a finding from step 4.

6. [ ] Generate an SBOM for `python:3.8-slim` in CycloneDX format:
   `trivy image --format cyclonedx --output sbom.json python:3.8-slim`
   Open `sbom.json` — what does the SBOM let you do that the CVE report alone doesn't?

7. [ ] **Remediation decision.** Produce a short prioritization list: top-three CVEs to fix first,
   which base image to upgrade first, and what `FROM` pin you'd write in the updated Dockerfile.

## Success criteria — you're done when
- [ ] You have trivy and grype CVE counts for both `python:3.8-slim` and `node:14`, with fixable vs. unfixable breakdown.
- [ ] You have a list of every `trivy config` finding in `Dockerfile.bad` with a one-line risk explanation for each.
- [ ] You have an SBOM JSON on disk.
- [ ] You have a prioritization list with the top-three CVEs and a recommended base image upgrade.

## Deliverables
- `scan-report.md` — your findings: CVE counts, severity breakdown, fixability, and your remediation priority list.
- `Dockerfile.fixed` — a corrected version of `Dockerfile.bad` that passes `trivy config` clean.
- `sbom.json` — the CycloneDX SBOM.

Commit these three files. Lab artifacts (`*.tar`, image layers) stay out of the commit.

## Automate & own it
**Required.** Write a GitHub Actions workflow (`ci-image-scan.yml`) that:
1. Builds a Docker image from a `Dockerfile` in the repo.
2. Runs `trivy image --exit-code 1 --severity HIGH,CRITICAL` on it.
3. Fails the PR if the gate is triggered.

Have a model draft the workflow YAML. **You read every line** — check the `trivy-action` version pin, confirm the `exit-code` logic, and add an `on: pull_request` trigger. Run it against a branch that has `Dockerfile.bad` to confirm the gate fires, then switch to `Dockerfile.fixed` and confirm it passes. Commit the working workflow.

## AI acceleration
Point a model at your `trivy` JSON output (`trivy image --format json python:3.8-slim`) and ask it to rank the findings by "exploitability for an internet-facing Python API running as non-root." It will produce a useful triage ranking — but verify each CVE's NVD page before treating the rank as final. The model cannot assess whether the vulnerable code path is actually reachable in your application.

## Connects forward
- Module 11 shows what happens when the runtime protections that scanning can't enforce — privilege, capabilities, host mounts — are actually exploited.
- Module 13 adds an admission webhook (Kyverno) that enforces the `trivy`-gate results as a cluster policy: images that don't pass the scanner can't even start.

## Marketable proof
> "I build container image scanning into CI with trivy and grype — CVE gates, Dockerfile hygiene checks, and SBOM generation — so vulnerable images never reach our registry."

## Stretch
- Pin `python:3.8-slim` to its current digest (`@sha256:...`) in `Dockerfile.fixed` and confirm `trivy` still resolves the CVE list correctly against the pinned digest.
- Add `hadolint` to the CI workflow alongside `trivy config` — it catches additional Dockerfile best-practice violations.
- Generate an SPDX-format SBOM and compare its structure to the CycloneDX one.
