# Lab 06 — Infrastructure-as-Code Security

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/06-iac-security
make up
make demo
make shell
make down
```

The environment is a single container with `checkov`, `tfsec`, and `trivy` pinned to specific
versions. `data/terraform/` contains a directory of intentionally misconfigured Terraform templates
covering real Meridian Financial resources: an S3 bucket without encryption, a security group with
`0.0.0.0/0` ingress, an IAM policy with wildcard actions, an RDS instance without storage
encryption, and an EBS volume without encryption. No cloud account or Terraform state is needed —
all scanning is purely static. `make demo` runs all three tools against the directory.

## Scenario

Meridian Financial's platform team has been writing Terraform to automate infrastructure deployment.
A security review was never built into the pipeline. You have been handed the `data/terraform/`
directory — a snapshot of their module library — and asked to identify every misconfiguration that
would fail a CIS AWS benchmark review. Your deliverable: a consolidated finding list across all
three tools, a ranked remediation backlog, and a sample GitHub Actions workflow that gates
pull requests on scanner output.

## Do

1. [ ] **Run `checkov` first.**
   Scan `data/terraform/` and output results in JSON. Count the number of FAILED checks.
   *Hint:* `checkov -d data/terraform --output json > /tmp/checkov.json`
   Note: checkov outputs a summary at the end — look for the `FAILED` count per check and the
   overall `passed/failed` ratio.

2. [ ] **Run `tfsec`.**
   Scan the same directory and output in JSON.
   *Hint:* `tfsec data/terraform --format json > /tmp/tfsec.json`
   Compare the finding count to checkov. Are there findings in one but not the other?

3. [ ] **Run `trivy config`.**
   *Hint:* `trivy config data/terraform --format json -o /tmp/trivy.json`
   Note which resources each tool scans (Terraform resource types vs. files).

4. [ ] **Build a consolidated finding matrix.**
   Create a Markdown table: Resource | Misconfiguration | Detected By | CIS Control | Severity.
   Fill in one row per unique misconfiguration. Where a finding appears in multiple tools, mark all
   of them. This cross-tool view is what you'd present to an engineering team.

5. [ ] **Read and understand two findings in depth.**
   Pick one HIGH finding from checkov and one from tfsec. For each:
   - Read the check source code (checkov: look up the check ID at github.com/bridgecrewio/checkov;
     tfsec: see aquasecurity.github.io/tfsec). What field does it actually test?
   - Verify the misconfiguration in the Terraform file — confirm the flag makes sense.
   - Write the correct Terraform attribute to fix it.

6. [ ] **Apply a fix and re-scan.**
   Fix one misconfiguration in the Terraform (e.g., enable S3 bucket encryption). Re-run the
   relevant scanner and confirm the check now passes. This is the red→green cycle you would gate
   in CI.
   *Hint:* Make the fix in `data/terraform/`, re-run `checkov --check <CHECK_ID> -d data/terraform`.

7. [ ] **Add a justified suppression.**
   The security group in `data/terraform/sg.tf` has `0.0.0.0/0` on port 443. This is intentional
   for a public-facing load balancer. Add the appropriate checkov `#checkov:skip` comment with a
   rationale, and confirm the check is suppressed on re-scan.
   *Hint:* `# checkov:skip=CKV_AWS_24: Public HTTPS ingress is required for internet-facing ALB`

8. [ ] **Write a CI workflow.**
   Write `ci-iac-scan.yml` — a GitHub Actions workflow that runs `checkov -d terraform/ --soft-fail-on MEDIUM`
   and fails the PR on any HIGH or CRITICAL finding. Use the template in `data/workflow-template.yml`
   as a starting point.

## Success criteria — you're done when

- [ ] All three scanners run successfully against `data/terraform/`
- [ ] Consolidated finding matrix covers every misconfigured resource with correct CIS mapping
- [ ] At least one fix applied and verified green on re-scan
- [ ] At least one suppression added with an inline rationale comment
- [ ] `ci-iac-scan.yml` is written and syntactically valid (you can validate with `actionlint` or GitHub's validator)

## Deliverables

Commit to your portfolio repo:
- `finding-matrix.md` — consolidated table across all three tools
- `ci-iac-scan.yml` — GitHub Actions workflow for PR gating
- `scan-all.sh` — the automation script from **Automate & own it** below

Do **not** commit: `/tmp/*.json` scanner output files, any Terraform state (`*.tfstate`), or the
`data/terraform/` directory itself (it's seeded in the lab repo, not yours).

## Automate & own it

**Required.** Write `scan-all.sh` — a script that:
1. Runs all three scanners against a directory passed as `$1` (default: `terraform/`)
2. Exits 0 only if all three pass with no HIGH or CRITICAL findings
3. Outputs a unified summary: tool name, pass/fail counts, and any HIGH+ finding IDs
4. Writes a machine-readable `scan-report.json` combining output from all three

AI drafts the loops, the jq filters, and the exit-code logic. You verify:
- that the exit-code logic correctly catches all critical paths (a scanner error ≠ a clean scan)
- that the JSON merge is structurally correct and not silently swallowing parse errors
- that the script handles a directory with no `.tf` files gracefully

```bash
#!/usr/bin/env bash
# Starter scaffold
TARGET="${1:-terraform/}"
FAIL=0
# YOU: run checkov, tfsec, trivy; capture exit codes
# YOU: merge summaries into scan-report.json
# YOU: exit $FAIL
```

## AI acceleration

Paste a misconfigured Terraform block into a model and ask for the minimum set of attributes to
make it pass checkov's CKV_AWS_* checks. This is fast for known patterns (S3 encryption, EBS
encryption, logging). Where the model earns scrutiny: IAM policy remediation — wildcard fixes
often over-correct into policies that break the application, or under-correct by moving the
wildcard from `Action` to `Resource`. You must trace the fix through the actual permission model,
not just the scanner output.

## Connects forward

The CI workflow you write here gates Meridian's deployment pipeline. In Module 08 (CI/CD Security)
you will extend that pipeline's *security posture* — looking at secrets in the workflow YAML, image
scanning, and supply-chain integrity, rather than just IaC policy.

## Marketable proof

> "I scanned a Terraform codebase with checkov, tfsec, and trivy; consolidated cross-tool findings
> into a prioritised remediation backlog; and built the CI workflow that now gates every pull
> request on IaC policy."

## Stretch

- Write a custom `checkov` check in Python that enforces Meridian's tagging policy: every resource
  must have `Owner`, `Environment`, and `CostCenter` tags. Test it against `data/terraform/`.
- Set up a pre-commit hook using `pre-commit` + the `checkov` hook so that developers catch IaC
  misconfigs before they even push.
