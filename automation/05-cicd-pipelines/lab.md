# Lab 05 — Build and Operate a Pipeline Gate That Blocks a Bad Change

*Type 7 · Build-&-Operate (secondary: Gate). [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It runs a **local CI
harness** so you build and *operate* a real pipeline gate without needing GitHub-hosted Actions: the
same gate logic (gitleaks + checkov + syft) wired to a "merge" step that fails closed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/automation/05-cicd-pipelines
make up          # build the gate-runner container (gitleaks, checkov, syft)
make demo        # run the full gate against a clean change — it PASSES (green)
make demo-bad    # run the same gate against a planted bad change — it BLOCKS (red, exit non-zero)
make down
```

`make demo` proves the gate passes a good change; `make demo-bad` proves it **blocks** a bad one —
that red, non-zero result is the deliverable, not a failure. The harness runs the identical checks a
GitHub Actions workflow would; you also author the real `.github/workflows/` YAML so the gate is
portable to a hosted runner.

> No external targets and no live cloud. The pipeline authenticates to "cloud" via a mocked OIDC step
> so you wire the *pattern* (short-lived token, no stored key) without a real account. Where the local
> harness can't enforce what hosted Actions does (branch protection, real OIDC), the lab labels it
> **assessed from config**, not demonstrated — see Success criteria.

## Scenario
Your team ships infrastructure from a Git repo and, today, runs its security tools by hand — so they
run inconsistently and the misconfiguration that ships is "the one we forgot to check." Your job is to
**build the gate**: a pipeline that runs a secret scan, an IaC scan, and an SBOM step on every change,
fails closed on a finding, and is itself hardened so it can't become the next Codecov. Then you
**operate it** — run it against a clean change and watch it pass, run it against a bad change and watch
it block the merge.

## Do

1. [ ] **Stand up the gate-runner and run it green.**
   `make up`, then `make demo`. Watch gitleaks, checkov, and syft run against a clean sample change
   and the pipeline exit 0. Read the harness so you can see the wiring: each gate is a step that
   **exits non-zero on a finding**, and the "merge" step only proceeds if all gates passed. *Goal:
   know what "a gate" actually is — an exit code wired to a merge decision.*

2. [ ] **Operate it against a bad change — make it block.**
   `make demo-bad`. The planted change adds a hardcoded secret *and* an unencrypted bucket. Watch
   gitleaks and checkov fire, the pipeline exit non-zero, and the merge step refuse. **This red,
   blocking run is the core deliverable** — capture its output. *Goal: feel the difference between a
   tool that *reports* and a gate that *blocks*.*

3. [ ] **Add the SBOM gate and prove it produces a bill of materials.**
   Wire a `syft` step that emits a CycloneDX (or SPDX) SBOM for the built artifact and fails the run
   if it can't generate one. Confirm the SBOM lists the artifact's real components. *Goal: "what's
   actually in what I ship" is now part of the gate, not an afterthought.*

4. [ ] **Author the portable workflows — and get the trust boundary right.**
   Write the real `.github/workflows/security-gate.yml` (and a deploy workflow) that mirror the
   harness. As you write, make every trust-boundary call deliberately:
   - Trigger the scan on **`pull_request`**, never `pull_request_target` running PR code — state in a
     comment why (untrusted code + secrets = the Codecov shape).
   - Add a **job-level `permissions:` block** scoped to the minimum (`contents: read` for scans;
     elevate only the job that needs it). No `write-all`.
   - **Pin every `uses:` to a full commit SHA** with the version in a trailing comment
     (`actions/checkout@<40-hex>  # v4.2.2`) — verify each SHA against the tag with
     `git ls-remote --tags <repo> <tag>`. This is the literal control that would have caught Codecov.
   - The deploy job authenticates to the cloud via **OIDC** (`permissions: id-token: write`, an
     `aws-actions/configure-aws-credentials` role-assume) — **no `AWS_ACCESS_KEY_ID` in repo
     secrets.** A secret you don't store can't be exfiltrated.
   *Goal: a pipeline that holds the keys to your infra and can't be turned into an exfiltration
   channel.*

5. [ ] **Make the gate binding, and assess what the local harness can't enforce.**
   Document the **branch-protection** config that makes these checks *required* (the setting that turns
   a pipeline into a gate) and note honestly that the local harness can't enforce branch protection or
   real OIDC token exchange — those are **assessed from your workflow config**, not demonstrated
   locally. Re-run `make demo` and `make demo-bad` and confirm green-on-good, red-on-bad still holds
   after your edits.

## Success criteria — you're done when
- [ ] `make demo` is **green** on a clean change and `make demo-bad` is **red and non-zero**, blocking the merge — and you captured both runs.
- [ ] The gate runs **three** fail-closed checks: gitleaks (no secrets), checkov (no IaC misconfig), syft (an SBOM is produced).
- [ ] Your `.github/workflows/` YAML uses `pull_request` (not `pull_request_target`), a job-level least-privilege `permissions:` block, **every action pinned to a SHA** (each verified against its tag), and **OIDC** for cloud auth with no long-lived key in secrets.
- [ ] You documented the branch-protection / required-checks config that makes the gate binding, and labeled what is **assessed from config** vs demonstrated locally.

## Deliverables
The hardened, operating pipeline: the local-harness config, `.github/workflows/security-gate.yml` (+
deploy workflow), the captured **blocking** run (`demo-bad` output), the generated SBOM, and a short
`PIPELINE.md` — what each gate catches, the trust-boundary choices (trigger, permissions, pinned
SHAs, OIDC) and why, and which controls are assessed-from-config. Commit all. Do **not** commit
secrets, the runner's environment, or generated artifacts beyond the SBOM.

## Automate & own it
**Required.** Write `verify-pins.py` (or `.sh`): a small reviewable tool that parses every workflow in
`.github/workflows/`, flags any `uses:` **not** pinned to a full 40-hex SHA, any
`pull_request_target`, any `permissions: write-all`, and any long-lived cloud key in `env:`/secrets —
then `git ls-remote`-verifies that each pinned SHA actually corresponds to its trailing-comment tag.
This is your supply-chain pin auditor, the Codecov control turned into a script you run on every repo.
Have a model draft it; **review every line** — confirm it actually flags an unpinned action and a
mismatched SHA (test it against a deliberately broken workflow), and that it doesn't shell out unsafely
on the action name. Wire it as a step in the gate so the pipeline audits *its own* pins. Commit it
beside the workflows.

## AI acceleration
Ask a model to generate a "secure" GitHub Actions deploy workflow that builds an image and pushes to a
cloud registry. Then operate the review: which trigger? Is there a job-level `permissions:` block? Is
every `uses:` pinned to a SHA? Where do the cloud credentials come from — a stored key or OIDC?
Models routinely emit unpinned actions and a long-lived `AWS_ACCESS_KEY_ID`; catching that is the
skill. Then run your `verify-pins.py` over the model's output and confirm it flags exactly what your
eye did — if it misses one, widen the script.

## Connects forward
This pipeline is the spine of the Track 10 capstone: the gate that gates IaC misconfigurations feeding
a SOAR playbook that responds to alerts. Module 09 (detection-as-code) plugs a *scored* Sigma
regression gate into this same CI framework, and the SBOM step here is the input to dependency- and
container-scanning later.

## Marketable proof
> "I build and operate CI/CD security gates — secret-scan, IaC-scan, and SBOM from commit to deploy —
> and harden the pipeline itself: `pull_request` not `pull_request_target`, least-privilege job tokens,
> every action pinned to a commit SHA, and short-lived OIDC instead of stored cloud keys. I can show
> the gate blocking a bad change, and I wrote a tool that audits a repo's action pins."

## Stretch
- Add a **third-party-action allowlist** + a Dependabot `github-actions` config so pins are bumped via
  reviewed PRs (the T23 pattern this repo applied to itself) — then watch a pin go stale and get a PR.
- Run `actionlint` (in Docker) over your workflows for security issues beyond the gate, and add any new
  finding class to `verify-pins.py`.
- Sign the built artifact with `cosign` (keyless, via the same OIDC identity) and add a verify step —
  the supply-chain control that turns "trust the build" into "verify the build."
