# Module 05 — CI/CD Pipelines & Gates

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *the security check that runs before the merge is the one that can't be bypassed.*

## Why this matters
Every security tool you've used in this track — `checkov`, `bandit`, `gitleaks`, `sigma-cli` —
can run in a CI pipeline. When they run in CI on every pull request, they become gates: a
misconfigured Terraform file, a hardcoded secret, or a broken Sigma rule cannot merge until
the gate passes. The alternative is running these tools manually, which means they run
inconsistently, and the misconfiguration that ships is always "the one we forgot to check."

## Objective
Read, analyze, and fix three GitHub Actions workflow files for security vulnerabilities — secret
injection, `pull_request_target` misuse, and excessive permissions — without running any live
CI infrastructure.

## The core idea
GitHub Actions is YAML that runs shell commands on GitHub-managed (or self-hosted) runners. The
security model has two distinct boundaries: **what the workflow can read** (repo contents,
secrets, environment variables) and **what the workflow can write** (to the repo, to the PR, to
external systems). These boundaries are controlled by `permissions:` blocks and the event trigger
type — and they are the source of most CI/CD security vulnerabilities.

`pull_request_target` is the first major footgun. It runs in the context of the *base branch*
rather than the PR branch, which means it has access to repository secrets — including
`GITHUB_TOKEN` with write permissions. A workflow that checks out the PR code and runs it under
`pull_request_target` allows a malicious PR to exfiltrate secrets. The safe pattern: use
`pull_request` (not `pull_request_target`) for PR code scanning, and restrict secret access
explicitly. `pull_request_target` has legitimate uses (e.g., posting PR comments as a bot with
write access), but it must never execute untrusted PR code.

Least-privilege permissions in GitHub Actions means setting `permissions:` at the job level to
the minimum required: `contents: read` for checkout, `pull-requests: write` only for the job
that needs to comment, `security-events: write` only for the job that uploads SARIF. Default
permissions in new repos are `read` for everything; older repos often have `write` for everything
by default. Read the permissions block of every workflow you adopt — especially community
workflows from the GitHub Marketplace.

Secret injection is the failure mode where a secret value ends up in the workflow YAML or in
a log line: `echo "token=${{ secrets.API_KEY }}"` in a `run:` block prints the token to the
build log (GitHub masks known secrets in logs, but only if they're declared as secrets — values
computed from secrets may not be masked). The rule: never `echo` a secret; pass it as an
environment variable to a command that reads it from its environment, not as a CLI argument
(CLI arguments appear in `ps` output and shell history).

## Learn (~2 hrs)

**GitHub Actions security (~1.5 hrs)**
- [GitHub Actions security hardening — GitHub docs](https://docs.github.com/en/actions/reference/security/secure-use) — the canonical reference; read the "Understanding the risk of script injections", "Good practices for mitigating script injection attacks", and "Using third-party actions" sections in full.

**gitleaks (~30 min)**
- [gitleaks — GitHub](https://github.com/gitleaks/gitleaks) — the primary open-source secret scanner; read the README through the "Usage" section; understand the difference between `protect` (pre-commit) and `detect` (CI scan).

## Key concepts
- `pull_request` vs. `pull_request_target`: the trust boundary and why it matters
- `permissions:` blocks: set at job level, use minimum required
- Secret injection: never `echo` a secret; pass via env to the command
- Pinning action versions to a SHA (`uses: actions/checkout@<sha>`): prevents supply-chain attacks
- `gitleaks` as the secrets-in-code gate: runs on every PR and fails on new secrets

## AI acceleration
AI generates functional GitHub Actions workflows that are often insecure: missing permissions
blocks, unpinned action versions, and `pull_request_target` used where `pull_request` would
work. Ask a model to generate a Checkov scan workflow; then ask it to add least-privilege
permissions, pin all action versions to SHAs, and explain why `pull_request` is used instead
of `pull_request_target`. The explanation step forces the model to reason about the security
model, and you verify the reasoning is correct.
