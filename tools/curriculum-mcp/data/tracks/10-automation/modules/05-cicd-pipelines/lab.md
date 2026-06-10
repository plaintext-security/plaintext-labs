# Lab 05 — CI/CD Pipelines & Gates

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/05-cicd-pipelines
make demo      # runs gitleaks locally against data/ and the ci-review-checklist
make shell     # gitleaks container
make down
```

No live CI infrastructure — this is a static review lab. `data/.github/workflows/` contains
three deliberately flawed workflow files. `data/ci-review-checklist.md` is the review framework.
`make demo` runs `gitleaks detect` locally against the `data/` directory to demonstrate the
secrets-scanning pattern.

## Scenario
Meridian's new platform team submitted three GitHub Actions workflows in a PR. Before they're
merged, your security team has been asked to review them for CI/CD security issues. Your job:
identify every vulnerability in each workflow, fix the workflows, and document the changes.

> No external targets, no live CI required. Review the workflow YAML files as static documents.

## Do
1. [ ] `make demo` — watch `gitleaks detect` run against `data/`. Note any findings.
2. [ ] Read `data/ci-review-checklist.md` — the review framework. Work through each workflow
   (`gitleaks-scan.yml`, `iac-scan.yml`, `sigma-lint.yml`) line by line against the checklist
   and list every security issue you find. Each file hides at least one. Things to interrogate:
   how the workflow is triggered and whether that trigger exposes secrets to untrusted code;
   whether third-party actions are pinned; whether the `permissions` block follows least
   privilege; and whether any step exposes a secret. Don't fix anything yet — first enumerate.
3. [ ] For each finding, work out the fix and write a one-paragraph entry in `security-review.md`:
   what the vulnerability is, what an attacker could do with it, and how your fix addresses it.
4. [ ] Fix all three workflow files. Run `make demo` again to confirm `gitleaks` finds no secrets.
5. [ ] Compare your findings against the original `data/ci-review-checklist.md`: at least two of
   the issues you found are not yet covered by a checklist item. Add an item for each — extend the
   checklist so the next reviewer catches them.

## Success criteria — you're done when
- [ ] All three workflows are fixed and you can explain each change.
- [ ] `gitleaks detect` on `data/` exits 0.
- [ ] `security-review.md` documents all findings with risk and fix.
- [ ] The checklist is extended with at least two new items.

## Deliverables
Fixed workflow files + `security-review.md` + updated `data/ci-review-checklist.md`. Commit all.

## Automate & own it
**Required.** Write a fourth workflow, `data/.github/workflows/security-gate.yml`, that
combines all three gates: gitleaks secrets scan + checkov IaC scan + sigma lint — running in
parallel using `jobs:`. Have a model draft it; review: Does it use `pull_request`? Are all
action versions pinned? Is the permissions block set correctly? Fix anything wrong. Commit the
new workflow.

## AI acceleration
Ask a model to generate a secure GitHub Actions workflow for running `bandit` on Python code.
Then apply the checklist to its output: Is `pull_request_target` used? Are actions pinned?
Is there a permissions block? This exercise trains you to review AI-generated YAML with the
same skepticism as AI-generated Python code.

## Connects forward
The CI gate pattern from this module is the spine of the Track 10 capstone: a pipeline that
gates IaC misconfigurations + a SOAR playbook that responds to alerts. Module 09 (detection-as-
code pipelines) adds Sigma linting to the same CI framework.

## Marketable proof
> "I review GitHub Actions workflows for security — pull_request_target misuse, unpinned
> actions, excessive permissions, and secret injection — and I can write a secure multi-gate
> pipeline from scratch."

## Stretch
- Use `actionlint` (in Docker) to lint all four workflow files for syntax and security issues
  beyond what the checklist covers.
- Pin all action versions to SHAs using the `gh` CLI: `gh api /repos/<owner>/<repo>/releases/latest`
  to find the latest SHA for each action.
