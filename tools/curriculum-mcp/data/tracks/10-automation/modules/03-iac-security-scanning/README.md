# Module 03 — IaC Security Scanning

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *the misconfiguration that never deploys is the cheapest one to fix.*

## Why this matters
A misconfigured S3 bucket costs nothing to fix in a `.tf` file before it's deployed. After it's
deployed with public read access, discovered by a scanner, added to a breach report, and
communicated to customers — it costs orders of magnitude more. IaC scanners are the security
gate that catches these issues before `tofu apply` runs. Every CI/CD pipeline that deploys
infrastructure should run a scanner as a gate; this module is how you set that up.

## Objective
Run `checkov` and `tfsec` against an intentionally misconfigured Terraform configuration,
understand each finding, fix the most critical ones, and set up the scanner as a CI gate.

## The core idea
IaC scanners work by pattern matching against known-bad configurations: rules like "an S3 bucket
with `acl = public-read` is misconfigured," "a security group with `cidr_blocks = ["0.0.0.0/0"]`
on port 22 is overly permissive," "an RDS instance with `publicly_accessible = true` should fail."
These rules are maintained by the security community, mapped to CIS Benchmarks and cloud provider
security frameworks, and updated regularly. The scanner does not understand your architecture —
it pattern-matches — which is why findings require human review before being flagged as real
issues.

`checkov` (Bridgecrew / Palo Alto Networks) and `tfsec` (Aqua Security) cover overlapping
but not identical rule sets. Running both is a common practice because they each catch things
the other misses. `checkov` is broader across providers and has better Python integration (useful
in custom CI scripts); `tfsec` has more granular rule customization and is faster on large repos.
For a security team, the choice between them is less important than the habit of running one
consistently in CI.

Suppressing a finding is a decision, not a dismissal. The correct workflow: scanner flags an
issue, engineer reads the rule and the code, decides it's a false positive or acceptable risk,
adds a `#checkov:skip=<rule>:reason` comment with an explicit justification. Suppressing findings
silently (without comments) is the same as the analyst who clears alerts without reading them —
it removes the signal without addressing the underlying question. Code review of suppressions
is as important as code review of the configurations themselves.

The CI gate shape is simple: `checkov -d . --soft-fail-on <category>` exits 0 on known-false-
positives and 1 on real findings. A pipeline that fails on `checkov` exit code 1 means the
misconfig never reaches `tofu apply`. The skill is calibrating the rule set: too strict and every
PR fails with false positives; too loose and real misconfigs slip through. Start strict and
suppress with justification; never start permissive and tighten later.

## Learn (~2 hrs)

**checkov (~1 hr)**
- [checkov — Getting Started](https://www.checkov.io/1.Welcome/Quick%20Start.html) — run through the quickstart against a local Terraform directory; understand `--check`, `--skip-check`, and the output format.
- [checkov — Terraform checks reference](https://www.checkov.io/5.Policy%20Index/terraform.html) — skim the check index; CKV_AWS_* rules are the ones that fire most often; know what `CKV_AWS_18` and `CKV_AWS_119` mean before the lab.

**tfsec (~1 hr)**
- [tfsec — Documentation](https://aquasecurity.github.io/tfsec/latest/) — read the "Getting Started" and "Configuration" sections; understand the severity levels and how to suppress findings.

## Key concepts
- Scanner pattern matching vs. architecture understanding — why human review is required
- `checkov` and `tfsec` rule coverage: overlapping but not identical
- Suppression with justification: `#checkov:skip=<rule>:reason` — never silent
- CI gate: scanner exits 1 on real findings, pipeline fails, PR is blocked
- Calibration: start strict, suppress with justification

## AI acceleration
Ask a model to generate a Terraform config for an AWS S3 bucket. Then run `checkov` on it.
Count the findings. Ask the model to fix them. Run `checkov` again. Count the remaining findings.
Ask the model to explain each suppression it added. This loop — generate, scan, fix, scan again —
is the production workflow, and doing it by hand teaches you which misconfigs AI consistently
produces.
