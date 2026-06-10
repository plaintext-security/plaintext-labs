# Lab 08 — CI/CD Pipeline Security

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/08-cicd-security
make up
make demo
make shell
make down
```

The environment provides a single lab container with `gitleaks` 8.x and `trivy` 0.52.x pinned.
`data/repo/` is a small git repository with planted secrets (a fake AWS key and a private key
placeholder) for `gitleaks` to find. `data/workflow.yml` is a GitHub Actions workflow file with
deliberate misconfigurations for manual review. `data/images.txt` lists container image references
for `trivy` scanning. No cloud credentials or Docker registry access needed for the gitleaks work;
the trivy scan pulls public image metadata.

> This lab scans intentionally misconfigured repositories and images. Never run gitleaks or trivy
> against repositories or images you do not own or have explicit written permission to scan.

## Scenario

Meridian Financial is hardening its deployment pipeline before connecting to the production AWS
account. A security review of the existing CI configuration has been requested. You are auditing
three surfaces: (1) the application repository for committed secrets, (2) the base container image
for known vulnerabilities, and (3) the GitHub Actions workflow for misconfiguration. Your
deliverable is a hardened `workflow-hardened.yml` and a pipeline policy document.

## Do

### Part 1: Secrets scanning with gitleaks

1. [ ] **Run gitleaks against the repository.**
   *Hint:* `gitleaks detect --source /lab/data/repo --report-format json --report-path /tmp/gl-report.json`
   How many findings are there? What patterns were matched? (gitleaks names the rule that fired.)

2. [ ] **Identify the planted secrets.**
   Read `/tmp/gl-report.json`. For each finding, note: Rule ID, file, line number, commit SHA,
   and the secret type. Can you find the commit where each was introduced?
   *Hint:* `jq '.[].RuleID' /tmp/gl-report.json`

3. [ ] **Run gitleaks in protect mode** (simulating a pre-commit hook).
   `gitleaks protect --staged --source /lab/data/repo`
   Understand the difference between `detect` (scans history) and `protect` (checks staged changes
   before commit). This is the pre-commit hook integration pattern.

4. [ ] **Add a custom gitleaks rule.**
   Meridian has an internal API token format: `meridian_tok_[a-z0-9]{32}`. Create a `.gitleaks.toml`
   in `/tmp/` that extends the default rules and adds this custom pattern.
   *Hint:* The `[[rules]]` section takes `id`, `description`, and `regex` fields.
   Test it: `gitleaks detect --source /lab/data/repo --config /tmp/.gitleaks.toml`

### Part 2: Container image scanning with trivy

5. [ ] **Scan the first image reference in `data/images.txt`.**
   `trivy image <image-ref>` — this pulls the image metadata and scans for known CVEs.
   How many CRITICAL and HIGH CVEs does it find? What is the oldest CVE present?

6. [ ] **Generate an SBOM for the image.**
   *Hint:* `trivy image --format cyclonedx --output /tmp/sbom.json <image-ref>`
   Inspect the SBOM: how many OS packages are listed? What is the base OS and version?

7. [ ] **Apply a severity threshold.**
   Run trivy with `--severity CRITICAL,HIGH` and `--exit-code 1`. Confirm it exits non-zero.
   Now create a `trivy.yaml` that marks one specific CVE as an accepted exception (with a note)
   using the `ignorelist` feature.
   *Hint:* `trivy.yaml` uses the `ignore` key with a list of CVE IDs and optional `reason` fields.

8. [ ] **Compare two image tags.**
   Scan two different tags of the same image (e.g., `python:3.8-slim` vs `python:3.12-slim`).
   Build a two-column comparison: CVE count, most severe CVE, base OS version. This is the
   argument you'd make to an engineering team for "we need to update the base image."

### Part 3: Workflow review

9. [ ] **Review `data/workflow.yml` for misconfigurations.**
   Open the file and identify at least three security issues. For each, note:
   - What the issue is (injection, excessive permission, unpinned action, etc.)
   - What an attacker could do with it
   - The fix
   *Hint:* Look for `${{ github.event.* }}` in `run:` steps, `permissions: write-all`,
   `pull_request_target` with `actions/checkout`, and action references without SHA pins.

10. [ ] **Write `workflow-hardened.yml`.**
    Apply all the fixes from your review. The hardened workflow must:
    - Pin all `uses:` references to a specific commit SHA
    - Declare minimal `permissions:` at the job level (not `write-all`)
    - Sanitise all `${{ }}` expressions before passing to shell steps
    - Use a step to scan the built image with trivy before pushing
    - Use gitleaks in the workflow to block secrets from being committed

## Success criteria — you're done when

- [ ] gitleaks finds the planted secrets and outputs the finding JSON with rule ID, file, and SHA
- [ ] trivy scan completes against at least one real image reference and outputs CVE counts
- [ ] `trivy.yaml` with at least one accepted-risk exception is written with a rationale comment
- [ ] At least three workflow misconfigurations identified and documented
- [ ] `workflow-hardened.yml` passes a manual review against the hardening checklist

## Deliverables

Commit to your portfolio repo:
- `pipeline-audit.md` — findings from all three tools, with severity and fix
- `workflow-hardened.yml` — the hardened Actions workflow
- `trivy.yaml` — the image scan policy with accepted exceptions
- `pipeline-gate.sh` — the automation script from **Automate & own it** below

## Automate & own it

**Required.** Write `pipeline-gate.sh` — a script that simulates a CI pipeline gate:
1. Runs `gitleaks detect` against `$1` (the repo path); fails if any finding
2. Runs `trivy image` against `$2` (an image ref) with `--exit-code 1 --severity CRITICAL,HIGH`
3. Outputs a pass/fail summary with finding counts for each tool
4. Exits 0 only if both tools pass

AI drafts the logic; you verify:
- that a gitleaks finding is not swallowed if trivy passes (independent exit codes)
- that the script handles "image not found" gracefully (trivy returns a non-zero that is not a policy failure)
- that the summary output is human-readable for a CI log

## AI acceleration

Paste the `data/workflow.yml` file to a model and ask: "Identify all GitHub Actions security
misconfigurations and for each provide the CWE or ATT&CK technique, the risk, and the fix."
The model is fast and usually correct on the well-known patterns (injection, permissions). Your
review must catch: any fix the model suggested that breaks the workflow's intended function, and
any pattern the model missed (multi-step data-flow injection is commonly missed). Always apply
fixes in a branch and test that the workflow still does what it's supposed to do.

## Connects forward

The image scanning policy you set here (which CVE severities block deploy) feeds directly into
Module 10 (Container & Image Security), where you will build a full supply-chain pipeline with
SBOM attestation and image signing. The secrets-in-pipeline finding connects back to Module 07
(Secrets Management) — specifically, the OIDC token pattern that eliminates static credentials
from CI entirely.

## Marketable proof

> "I audited a CI/CD pipeline: found secrets in git history, scanned the container image for known
> CVEs, identified GitHub Actions misconfigurations including expression injection, and delivered a
> hardened workflow and an automated pipeline-gate script."

## Stretch

- Enable `trivy` SBOM attestation: generate a CycloneDX SBOM and sign it with `cosign` (see
  Module 10 for the full treatment). The goal here is to see the output format and understand
  the chain of custody model.
- Set up the `gitleaks` pre-commit hook in a test repository and verify it blocks a commit that
  contains a pattern matching your custom Meridian token rule.
