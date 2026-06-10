# Module 06 — Infrastructure-as-Code Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *scan the blueprint before the building goes up.*

## Why this matters
Terraform, CloudFormation, and Pulumi templates are exactly as dangerous as the infrastructure they
describe — and they live in git, reviewed by people who are reviewing *logic*, not security posture.
A misconfiguration that would take days to find in a running account takes seconds to catch in a
template, and costs nothing to fix before `terraform apply`.

## Objective
Scan a directory of intentionally misconfigured Terraform templates with `checkov`, `tfsec`, and
`trivy config`, compare what each tool surfaces, and integrate a scanner into a sample CI workflow.

## The core idea

Infrastructure-as-code is, among other things, a security forcing function: the configuration that
used to live in a console — ephemeral, undocumented, un-reviewed — is now a file that goes through
a pull request. That's the opportunity. The same thing that makes IaC auditable makes it scannable:
static analysis tools can read a Terraform directory and flag misconfigurations before any resource
is created. The shift from "find it in the running account" to "block it at PR merge" is
**shift-left security** in the most literal sense.

The practical anatomy of an IaC security check is simple: the scanner parses the HCL (or YAML, or
JSON), builds an internal representation of the resource graph, and applies a library of rules —
"is `block_public_acls` set to `true` on this S3 resource?" "does any security group ingress rule
have CIDR `0.0.0.0/0`?" The rules map to CIS benchmarks, MITRE ATT&CK, and the tool's own built-in
library, so you get traceability from a finding back to a published standard. The output is a
graded findings list, plus a suggested fix, before the resource ever exists in the cloud.

Three tools matter here because they each cover different ground. `checkov` (Bridgecrew/Palo Alto)
is policy-as-code with the largest built-in check library and custom check support in Python.
`tfsec` (Aqua) emphasises depth on Terraform specifically, with very human-readable output and
opinionated defaults tuned for common enterprise patterns. `trivy config` (Aqua) is the same
container scanner you already know, extended to Terraform, CloudFormation, Helm, and Kubernetes
manifests — the value is one tool in your pipeline that covers both images and IaC. In practice,
you pick one for CI gating and optionally run all three in a weekly policy review; they overlap
substantially but not perfectly.

The place most teams get this wrong is the suppression pattern. Every tool lets you add a comment
or an annotation to silence a finding on a specific resource. This is legitimate — a security group
rule in a public-facing DMZ load balancer *should* accept traffic from the internet. The
anti-pattern is suppressing by check ID across the whole codebase, or leaving suppressions with no
rationale. The review discipline is: every suppression must have an inline comment stating *why* the
control doesn't apply to this resource and who approved it. That comment is the audit trail.

## Learn (~4 hrs)

**Terraform security fundamentals (~1 hr)**
- [Terraform Registry — AWS provider security resources](https://registry.terraform.io/providers/hashicorp/aws/latest/docs) — browse the `aws_s3_bucket`, `aws_security_group`, and `aws_iam_policy` docs and note every attribute that has a security implication. This is the vocabulary the scanners use.
- [tfsec documentation](https://aquasecurity.github.io/tfsec/latest/) — read the "Getting Started" and browse the built-in AWS checks to understand what each rule actually tests. 30 minutes here pays dividends when you triage findings.

**checkov (~1 hr)**
- [checkov documentation — Bridgecrew/checkov](https://www.checkov.io/1.Welcome/What%20is%20Checkov.html) — the overview and the "Run Checkov" section. Understand the check ID format (CKV_AWS_*), the output options, and how to write a custom check.
- [checkov GitHub — bridgecrewio/checkov](https://github.com/bridgecrewio/checkov) — the built-in check library in `checkov/terraform/checks/resource/aws/` is the fastest way to understand what it is looking for.

**trivy config and supply chain (~1 hr)**
- [trivy documentation — misconfiguration scanning](https://aquasecurity.github.io/trivy/latest/docs/scanner/misconfiguration/) — how `trivy config` works, supported formats (Terraform, CloudFormation, Helm, Kubernetes), and how to add custom policies.

**CI/CD integration (~1 hr)**
- [GitHub Actions — using Checkov in CI](https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html) — the canonical integration pattern. Read this to understand how to fail a PR on a policy violation.
- [MITRE ATT&CK T1562 — Impair Defenses](https://attack.mitre.org/techniques/T1562/) — many IaC misconfigurations (logging disabled, security group too open) enable this technique family; useful framing for why these checks matter.

## Key concepts
- Shift-left: catch misconfigurations in PR review, not post-deploy audit
- HCL static analysis: how scanners parse and evaluate Terraform resources
- Check libraries: CIS benchmark mapping, MITRE ATT&CK coverage
- Suppression with rationale vs. suppression as a workaround
- CI gating: failing the build on policy violations, not just reporting them
- Key check categories: encryption at rest, public access, IAM wildcard, logging, MFA

## AI acceleration
AI is remarkably good at writing Terraform that passes a scanner — and remarkably good at writing
Terraform that looks correct but has subtle IAM over-grants or encryption misses. The workflow that
works: let the model generate a resource block, run `checkov` or `tfsec` on it immediately, and
feed the findings back to the model for a fix. The model is your first-pass engineer; you are the
reviewer who checks that the fix doesn't introduce a new problem (e.g., a too-restrictive S3 policy
that breaks the application) and that every suppression annotation has a real rationale.
