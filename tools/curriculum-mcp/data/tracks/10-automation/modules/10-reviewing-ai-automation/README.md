# Module 10 — Reviewing AI-Generated Automation

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *the automation an AI writes is confident, plausible, and frequently wrong in ways that matter.*

## Why this matters
This is the module the rest of the track was building toward. Every preceding module introduced
a tool — `checkov`, `bandit`, `sigma-cli`, `ansible-lint` — and showed how to use it to catch
errors in human-written code. Now apply those same tools to the output of an AI. AI-generated
Terraform, Ansible playbooks, and CI workflows are increasingly the raw material security teams
work with. The skill is knowing what to check, what to fix, and what to demand the AI explain
before you trust it.

## Objective
Review an AI-generated Terraform configuration using `checkov`, identify the misconfigurations
that the AI confidently but incorrectly produced, fix each one, and document the review process
as a repeatable checklist — so the team can apply it to any future AI-generated automation.

## The core idea
AI-generated infrastructure code has a distinctive failure pattern: it is structurally sound
(the HCL syntax is correct, the resource types are real, the attribute names are valid) but
semantically dangerous (the security settings are often wrong in ways that are undetectable
without running a scanner or knowing what to look for). The most common AI misconfigurations
in Terraform: overly permissive IAM policies (`"Action": "*"`, `"Resource": "*"`), publicly
accessible storage (`acl = "public-read"` on S3, `publicly_accessible = true` on RDS),
unencrypted resources (missing `encrypted = true`, missing KMS key), and overly broad security
groups (`cidr_blocks = ["0.0.0.0/0"]` on management ports).

The pattern is not random — it reflects the training data. Public Terraform examples online
frequently use permissive settings for brevity and clarity ("here's how the resource works,
without the noise of security configuration"). The AI has learned to mimic those examples. A
model asked to "write a Terraform config for an S3 bucket" produces the same config as a Stack
Overflow answer from 2019 — the config that gets the concept across, not the config you'd
put in production.

The review checklist for AI-generated Terraform mirrors the `checkov` rule categories: access
control (IAM least privilege, no wildcard actions), network exposure (no public S3, no public
RDS, security groups scoped to VPC CIDR), encryption (at-rest and in-transit), and logging
(CloudTrail, S3 access logging, VPC flow logs). These four categories cover 90% of cloud
security findings. Running `checkov` is the first pass; reading the HCL yourself is the second
pass for what `checkov` can't see (semantic correctness — does the policy do what the comment
says?).

The meta-skill is knowing when to accept a suppression and when to fix it. AI-generated
suppressions (`#checkov:skip=CKV_AWS_18:no logging needed for this bucket`) require the same
skepticism as AI-generated configurations: is the justification actually correct? Is there a
real technical reason, or did the AI suppress the finding because it didn't know how to fix it?
Suppression comments written by AI without human review are a red flag; suppression comments
reviewed and approved by a human who can articulate the justification are acceptable.

## Learn (~1.5 hrs)

**AI code review patterns (~1 hr)**

**Checkov reference (~30 min)**
- [checkov — CKV_AWS checks reference](https://www.checkov.io/5.Policy%20Index/terraform.html) — skim the checks that fire in this lab so you understand what each one means before you fix it.

## Key concepts
- AI misconfiguration pattern: structurally sound, semantically dangerous
- The four review categories: access control, network exposure, encryption, logging
- `checkov` as first pass; manual HCL read as second pass
- Suppression review: AI suppressions require the same skepticism as AI configurations
- The review checklist as a repeatable artifact — the team's shared standard

## AI acceleration
Use a model to both generate the initial bad config *and* to propose fixes for each `checkov`
finding. For each proposed fix, ask: "Why is this the correct fix? What does the resource do
differently now?" A model that can explain the fix is more trustworthy than one that just changes
a value. The explanation step is where the model's understanding gaps surface — and where you
learn what to check manually on the next review.
