# Lab 08 — Predict the Injection Point, Then Harden the Pipeline

*Variant D · breach-driven, build-first. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. A single container
pins `gitleaks` 8.x and `trivy` 0.52.x; no cloud account is required for the find-half.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/08-cicd-security
make up          # build the lab container + seed the sample repo
make demo        # run both scanners + list the workflow's planted issues
make shell       # drop into the container to work
make down        # stop when done
```

`data/repo/` is a small git repo with planted secrets for gitleaks; `data/workflow.yml` is a GitHub
Actions workflow with deliberate misconfigurations (each tagged `# ISSUE`); `data/images.txt` lists image
references for trivy. The trivy image scan pulls public image metadata, so it needs network; the gitleaks
and workflow work are fully offline.

**What this lab is — and isn't (read this).** You can run the *find-half* for real (gitleaks and trivy
genuinely scan). The *build-half* — provenance/attestation, OIDC — you **author and reason about**: a SLSA
provenance attestation is produced by a real CI platform (GitHub-hosted Actions, a hardened builder), which
this local container is not. So you'll *write* the attesting workflow and verify its **logic** (does it gate
on provenance? does it mint OIDC instead of a standing secret?), marked *assessed from config*, not
*executed in prod*. Honest tool, honest answer.

> Only scan repositories and images you own or have explicit written permission to scan. Everything here
> runs locally against seed data you own.

## Scenario
The target account is wiring its deployment pipeline to the production AWS account and asked for a review
after reading the SolarWinds post-mortem. The existing `data/workflow.yml` builds an image and ships it.
Your deliverable is the **hardened workflow** — pinned actions, OIDC, provenance-gated — plus the audit
that justifies it. You'll predict the injection point first, then harden where the prediction lands.

Each step runs the rhythm: **Predict** → **Do** (run the tool / write the YAML) → **Reveal** → **Record**.

## Do

### Part 1 — Walk the path, predict the injection point

1. [ ] **Map the pipeline as a trust path.** Read `data/workflow.yml` end to end and draw the arrows:
   commit → checkout → build image → push → deploy. **Predict:** mark where a SolarWinds-style attacker
   injects, and which existing step (if any) would catch them. **Record** your call before touching a tool.

2. [ ] **Run the find-half — secrets.** `gitleaks detect --source /lab/data/repo --report-format json
   --report-path /tmp/gl.json --no-banner`. For each finding record Rule ID, file, line, commit SHA. Add a
   custom rule for the target account's token format (`_tok_[a-z0-9]{32}`) in a `.gitleaks.toml` and re-scan.
   **Reveal:** gitleaks guards the *source* arrow — necessary, but it would **not** have caught SUNBURST,
   which never touched the repo. **Record** that gap.

3. [ ] **Run the find-half — image + SBOM.** Scan the first image in `data/images.txt`
   (`trivy image --severity CRITICAL,HIGH <ref>`); note CRITICAL/HIGH counts and the oldest CVE. Generate
   an SBOM (`trivy image --format cyclonedx --output /tmp/sbom.json <ref>`); record base OS and package
   count. Compare an EOL tag (`python:3.8-slim`) against a current one (`python:3.12-slim`). **Reveal:** the
   SBOM tells you *what's in* the artifact; it does **not** attest *how it was built* — the SolarWinds gap.

4. [ ] **Reveal the injection point.** Confirm against the README: the attacker injects at the **build**
   step, *after* checkout and *before* signing — past everything gitleaks and review guard, before the
   signature legitimises it. **Record:** owner = the pipeline's build stage; the find-half scans inputs, not
   the build process; the missing control is **provenance.**

### Part 2 — Harden where the prediction landed

5. [ ] **Audit the workflow's misconfigurations.** Identify each `# ISSUE` in `data/workflow.yml` (expect:
   expression injection via `${{ github.event.head_commit.message }}`, `permissions: write-all`, unpinned
   `actions/checkout@v4`, `pull_request_target` + checkout, workflow-scoped secrets, no image scan, no
   secrets gate). For each: the risk, an ATT&CK technique where it fits, and the fix.

6. [ ] **Write `workflow-hardened.yml`.** This is the deliverable. It must:
   - **Pin every `uses:` to a full commit SHA** with a trailing `# vX.Y.Z` comment (the T23 pattern — a
     mutable tag can be re-pointed at malicious code).
   - Declare **minimal per-job `permissions:`** (e.g. `id-token: write`, `contents: read`) — never
     `write-all`.
   - **Mint OIDC** to assume the deploy role (`aws-actions/configure-aws-credentials` with `role-to-assume`
     + `id-token: write`) instead of long-lived `AWS_ACCESS_KEY_ID`/`SECRET` secrets.
   - **Sanitise** every `${{ }}` flowing into a `run:` step (pass via `env:`, quote, never interpolate
     untrusted input directly into shell).
   - **Gate on the find-half:** gitleaks must block on a secret; trivy must `--exit-code 1
     --severity CRITICAL,HIGH` before push.

7. [ ] **Add the provenance gate (the SolarWinds control).** Extend `workflow-hardened.yml` to **emit a
   build provenance attestation** for the image (`actions/attest-build-provenance`, or document the
   `cosign attest` + SLSA-generator equivalent), and add a deploy-side step that **verifies provenance ties
   the artifact to this source commit + the trusted builder** before deploy. State in a comment why a valid
   *signature* alone would still pass the SolarWinds build but the *attestation* fails it. (Mark this step
   *assessed from config* — the attestation is produced by the real CI platform, not this container.)

8. [ ] **(In-lab stretch) Prove the find-half locally with `pipeline-gate.sh`.** Run a script that chains
   gitleaks + trivy with independent exit codes; confirm it fails on the seeded secret and the EOL image
   and passes on clean inputs. This is the executable slice of the gate; the provenance gate is its CI peer.

## Success criteria — you're done when
- [ ] You recorded a *pre-reveal* prediction of the injection point and scored it against the build-step reveal.
- [ ] gitleaks finds the planted secrets (with your custom rule) and trivy outputs CVE counts + an SBOM for at least one image.
- [ ] You can state in one sentence **what a signature proves and what it doesn't**, and why the SBOM/scan find-half wouldn't have caught SUNBURST.
- [ ] `workflow-hardened.yml` pins all `uses:` to SHAs, uses OIDC (no standing secrets), sets minimal per-job permissions, sanitises expressions, gates on gitleaks + trivy, **and emits + verifies a build-provenance attestation.**

## Deliverables
- `workflow-hardened.yml` — the hardened, provenance-gated Actions workflow (the portfolio artifact).
- `pipeline-audit.md` — the injection-point prediction + reveal, the three-tool findings, and the per-issue workflow audit with ATT&CK mappings.
- `trivy.yaml` — image-scan policy with at least one accepted-risk exception and a rationale comment.
- `pipeline-gate.sh` — the find-half automation from below.

Commit these. Do **not** commit the gitleaks/trivy JSON reports, the SBOM, secrets, or any real credentials.

## Automate & own it
**Required — judgment-as-code, not keystroke scripting.** Your verdict is "signing proves who, not what —
provenance is the gate." Encode it as the **hardened, provenance-signed `workflow-hardened.yml`** that
*fails the SolarWinds-shaped build and passes the clean one*: it must gate deploy on a verified build
provenance attestation tied to the source commit + trusted builder, pin every action to a SHA, mint OIDC
instead of standing secrets, and block on gitleaks/trivy. This is the exact hardening this curriculum's own
repos shipped as **T23** — your workflow is that pattern, made yours. Have a model draft the YAML; review
every line and confirm the provenance step *actually gates* (a valid signature alone must not be enough) and
that no `${{ }}` reaches a shell unsanitised. Back it with `pipeline-gate.sh` for the find-half so the gate
has an executable slice today and a provenance peer in CI.

## AI acceleration
Paste `data/workflow.yml` and ask the model to identify every misconfiguration with its ATT&CK/CWE, risk,
and fix, then to draft `workflow-hardened.yml`. It's fast and usually right on injection and permissions —
but it will (a) call a green signature/scan "secure" and omit **provenance** unless you direct it, and (b)
miss **multi-job data-flow injection**. Direct it to add the attestation gate, then adversarially ask it to
write a commit/build that sneaks past your hardened workflow — if it can, your gate is too narrow.

## Connects forward
The image-scan policy and SBOM here feed Module 10 (Container & Image Security), where signing and
attestation get the full treatment. The OIDC-over-secrets move closes the loop with Module 07 (Secrets
Management) — the pipeline is where "no long-lived creds" becomes concrete. The hardened, provenance-gated
workflow is the **delivery gate of the Phase-1 capstone**: the same workflow that fails the original
breach-shaped config and passes the fixed-as-code system.

## Marketable proof
> "Given a real supply-chain breach (SolarWinds/SUNBURST), I can locate the build-step injection point,
> explain why a valid signature didn't stop it, and deliver a hardened CI/CD workflow that pins actions to
> SHAs, uses OIDC instead of standing secrets, gates on gitleaks + trivy, and **verifies build provenance**
> — the missing control that breaks the chain."

## Stretch
- Wire `actions/attest-build-provenance` in a throwaway public GitHub repo and **verify the attestation**
  with the GitHub CLI on a real build — see the provenance gate fire end to end where the platform actually
  produces it.
- Add a Dependabot config (`package-ecosystem: "github-actions"`) so your SHA pins are bumped via PR and
  don't go stale — the second half of the repo's T23 pattern.
