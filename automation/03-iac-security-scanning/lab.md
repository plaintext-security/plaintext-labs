# Lab 03 — IaC Security Scanning

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/03-iac-security-scanning
make up        # checkov + tfsec in Docker
make demo      # runs both scanners over data/misconfig.tf sequentially
make shell
make down
```

`data/misconfig.tf` is an intentionally misconfigured Terraform configuration representing
Meridian's first cloud deployment attempt — an S3 bucket (public access, no versioning, no
encryption), an EC2 instance (SSH open to the world), and an IAM role with `*` actions. The
container has `checkov` and `tfsec` installed.

## Scenario
Meridian's developer submitted a pull request to create the company's first S3 bucket via
Terraform. The PR description says "just a quick bucket for file sharing." Before it reaches
`tofu apply`, you've been asked to scan it and list every security finding with a severity and
a fix recommendation.

## Do
1. [ ] `make demo` — watch both scanners run over `data/misconfig.tf`. Count the total findings
   from each tool. Are there any findings that appear in one tool but not the other?
2. [ ] For each HIGH/CRITICAL finding, write down:
   - The rule ID (e.g., `CKV_AWS_18`).
   - What the rule checks for.
   - Why it matters (what's the real risk?).
   - The one-line fix in HCL.
3. [ ] Copy `data/misconfig.tf` to `data/fixed.tf` and apply fixes for all HIGH/CRITICAL findings.
   Run `checkov -f data/fixed.tf` and `tfsec data/fixed.tf` and confirm finding counts drop.
4. [ ] One finding in `data/misconfig.tf` is a legitimate false positive for Meridian's use case
   (a logging bucket that doesn't need access logging on itself). Add the correct checkov skip
   comment with a justification, and confirm `checkov` no longer flags it.
5. [ ] Write `ci-gate.sh`: a three-line script that runs `checkov -d data/ --soft-fail-on LOW`
   and exits 1 if any MEDIUM or higher findings remain. Test it against both `misconfig.tf`
   (should exit 1) and `fixed.tf` (should exit 0).

## Success criteria — you're done when
- [ ] All HIGH/CRITICAL findings are fixed or suppressed with justification in `data/fixed.tf`.
- [ ] The false positive is suppressed with a `#checkov:skip=` comment that explains why.
- [ ] `checkov` run against `data/fixed.tf` exits 0 with the soft-fail setting.
- [ ] `ci-gate.sh` exits 1 on `misconfig.tf` and 0 on `fixed.tf`.

## Deliverables
`data/fixed.tf` + `ci-gate.sh` + a `findings.md` that lists every finding, its risk, and its
fix (or suppression justification). Commit all three.

## Automate & own it
**Required.** Write a GitHub Actions workflow (`.github/workflows/iac-scan.yml`) that runs
`checkov` on pull requests touching `*.tf` files. Have a model draft the workflow YAML; review:
Does it pin the checkov action version? Does it fail the PR on HIGH findings? Does it upload
the SARIF report as a PR artifact? Fix anything it got wrong. Commit the workflow.

## AI acceleration
Ask a model to review `data/misconfig.tf` for security issues before running the scanners.
Compare its findings to `checkov`'s output. Which did it miss? Which did it correctly identify?
This comparison tells you when to trust AI code review for IaC and when the scanner is still
the more reliable gate.

## Connects forward
The scanner setup in this module is the template for the CI/CD pipeline gate in module 05. In
module 10, you run `checkov` on AI-generated Terraform — the same workflow, but the source of
the misconfigs is the AI rather than a human developer.

## Marketable proof
> "I gate Terraform deployments with checkov and tfsec in CI — I can explain every finding,
> suppress false positives with justification, and set up the pipeline gate that prevents
> misconfigs from reaching apply."

## Stretch
- Write a custom `checkov` policy in Python that flags any `aws_s3_bucket` resource without a
  `tags = { Environment = ... }` tag — demonstrating that the scanner is extensible for
  organization-specific policy.
