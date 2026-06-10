# Module 02 — Infrastructure as Code

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *if you clicked it into existence, you can't prove it's correct and you can't reproduce it.*

## Why this matters
Infrastructure defined in a web console is configuration that exists in exactly one place, with no
version history, no peer review, and no way to prove it matches what you intended. A cloud security
group configured by clicking is an incident waiting to happen — one accidental "allow all" rule
with no PR and no rollback path. Infrastructure as Code changes the game: the configuration is a
file, the file is in git, and every change is reviewed and reproducible.

## Objective
Write a Terraform / OpenTofu configuration for a simple resource, understand the
plan→apply→destroy lifecycle, and read a cloud infrastructure config for security implications —
without needing a live cloud account.

## The core idea
Terraform and its open-source fork OpenTofu share the same declarative language — HCL (HashiCorp
Configuration Language). The model is: you write the *desired state* (what you want to exist),
and `tofu apply` figures out the *delta* (what needs to be created, changed, or destroyed) and
executes it. The diff between "desired" and "current" is the plan — and reading the plan before
applying it is the discipline that prevents the accidental `terraform apply` that deletes a
production database. Always `plan` before `apply`.

State is the concept that confuses most people starting with Terraform. The state file
(`terraform.tfstate`) is Terraform's record of what it created. It maps resource declarations in
your HCL to real IDs in the provider — `aws_instance.web` → `i-0123456789abcdef`. Without the
state file, Terraform can't match "what I declared" to "what exists." The security implication:
the state file often contains secrets (database passwords, API keys) that Terraform stores in
plain text. Never commit `terraform.tfstate` to git; store it in a backend with encryption (S3 +
DynamoDB, Terraform Cloud, etc.).

The `local` provider is underused as a teaching tool: it creates and manages files on the local
filesystem, with the full plan/apply/destroy lifecycle, no cloud credentials required. This is
how the lab works — you learn the Terraform workflow against local resources before touching
cloud resources. The workflow is identical; only the provider changes.

Module variables (`variable {}`) and outputs (`output {}`) are the interface that makes a
configuration reusable. A hard-coded CIDR block in a security group is a configuration that
must be edited to reuse. A variable with a sensible default is a parameter. This matters for
security: a security group that accepts its allowed CIDR as a variable (with a default of your
VPC CIDR) is much harder to accidentally open to `0.0.0.0/0` than one with the CIDR hardcoded.

## Learn (~2.5 hrs)

**OpenTofu fundamentals (~1.5 hrs)**
- [OpenTofu — Getting Started tutorial](https://opentofu.org/docs/intro/core-workflow/) — walk through the core workflow section; understand `init`, `plan`, `apply`, `destroy` conceptually before the lab.
- [Terraform Tutorial — HashiCorp Learn (local provider)](https://developer.hashicorp.com/terraform/tutorials/configuration-language/locals) — the local provider tutorial; identical workflow to cloud providers, zero credentials needed.

**HCL language (~1 hr)**
- [OpenTofu Language — Configuration Language docs](https://opentofu.org/docs/language/) — read the "Resources", "Variables", "Outputs", and "Providers" sections; these four concepts cover 80% of what you'll write.
- [HCL syntax — GitHub (hashicorp/hcl)](https://github.com/hashicorp/hcl/blob/main/hclsyntax/spec.md) — skim the spec enough to understand that HCL is not JSON; expressions, for-each, and conditional expressions are worth knowing exist.

## Key concepts
- Declarative state: write desired state, Terraform computes the delta
- Plan before apply — always; the diff is your review step
- State file security: never in git, always in an encrypted backend
- Variables and outputs: the interface that makes configs reusable
- The local provider: full Terraform workflow without cloud credentials

## AI acceleration
AI generates valid HCL quickly. The risk is that it will generate configurations that are
syntactically correct but security-misconfigured (open security groups, public S3 buckets, no
encryption). Module 03 addresses scanning for these issues — but the habit starts here: after
AI generates HCL, your first action is `tofu plan` (does it do what I intended?) and then
`checkov .` (does it have obvious misconfigurations?). AI drafts; you plan, scan, and apply.
