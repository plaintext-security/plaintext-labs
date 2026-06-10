# Lab 10 — Reviewing AI-Generated Automation

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/10-reviewing-ai-automation
make up        # checkov in Docker
make demo      # runs checkov on data/ai_generated_terraform.tf (before) and data/fixed.tf (after)
make shell
make down
```

`data/ai_generated_terraform.tf` is a Terraform configuration an AI assistant generated in
response to "Create a Terraform config for Meridian's S3 data bucket and an EC2 instance with
admin access." The config is plausible-looking HCL that contains five common AI-generated
misconfigurations. Your task: find every finding, understand each one, fix them, and document the
review as a checklist your team can reuse.

## Scenario
Meridian's cloud team asked an AI assistant to scaffold the initial Terraform for a new data
pipeline. The engineer who prompted it has a deadline and is ready to run `tofu apply`. Your
lead asks you to do a 30-minute security review before it goes anywhere near the cloud account.

> Review the configuration against the local checkov container. Do not run `tofu apply` against
> a real cloud account during this lab.

## Do
1. [ ] `make demo` — watch `checkov` run over `data/ai_generated_terraform.tf`. Count the
   findings. Note the severity of each.
2. [ ] For each CRITICAL and HIGH finding, write an entry in `review.md`:
   - Finding ID and what it checks.
   - The specific misconfiguration in `ai_generated_terraform.tf` (quote the offending line).
   - The real risk: what could an attacker do if this config deployed as-is?
   - The fix: the corrected HCL.
3. [ ] Copy `data/ai_generated_terraform.tf` to `data/fixed.tf`. Apply all fixes.
   Run `checkov -f data/fixed.tf` — confirm finding count drops to 0 (or the remaining
   findings are suppressed with explicit justifications).
4. [ ] One finding is a genuine false positive for Meridian's architecture (the S3 access-logging
   bucket doesn't need access logging on itself). Add the correct `#checkov:skip=` comment
   with a written justification and confirm checkov passes.
5. [ ] Write `ai-review-checklist.md` — a reusable checklist for reviewing AI-generated
   Terraform, organized by category: access control, network exposure, encryption, logging.
   Minimum 12 items; each item should be a yes/no question (`Is the S3 bucket ACL
   explicitly set to `private`?`).
6. [ ] Run `make demo` again — confirm `checkov` exits 0 on `data/fixed.tf`.

## Success criteria — you're done when
- [ ] `checkov` exits 0 on `data/fixed.tf`.
- [ ] `review.md` documents every CRITICAL and HIGH finding with risk and fix.
- [ ] The false-positive suppression has a written justification.
- [ ] `ai-review-checklist.md` has at least 12 items across all four categories.
- [ ] You can articulate what AI got wrong and why — what training data pattern produced each
  misconfiguration.

## Deliverables
`data/fixed.tf` + `review.md` + `ai-review-checklist.md`. Commit all three. Do not commit
`data/ai_generated_terraform.tf` changes.

## Automate & own it
**Required.** Write a `review.sh` script that runs `checkov` against a directory argument
(`./review.sh data/`) and prints a summary: total findings, CRITICAL count, HIGH count, and
a PASS/FAIL line. Have a model generate the shell script using `checkov --output json | jq`;
verify the jq expression is correct (test it against both the before and after configs). Commit
`review.sh`.

## AI acceleration
After completing the manual review, ask a model to review `data/ai_generated_terraform.tf`
for security issues. Compare its findings to `checkov`'s output and your manual review. Three
questions: What did the model catch that checkov missed? What did checkov catch that the model
missed? What did the model get wrong in its proposed fixes? Document the comparison in `review.md`
— this three-way analysis is the evidence base for deciding when to trust AI security review.

## Connects forward
This module completes the track and closes the loop: you've used AI to generate infrastructure
code and automation, and you've used the scanners and review skills from every preceding module
to validate it. The `ai-review-checklist.md` is the deliverable you carry forward — it is the
team standard for reviewing AI-generated automation.

## Marketable proof
> "I review AI-generated Terraform with checkov, I can explain every finding in plain English,
> and I have a documented checklist my team uses to review AI-generated IaC before it touches
> a cloud account."

## Stretch
- Ask a model to generate an Ansible playbook for the same task (EC2 admin access + S3 bucket
  management) and apply `ansible-lint` + a manual review — does AI make the same category of
  mistakes in YAML as in HCL?
- Contribute your `ai-review-checklist.md` to the SigmaHQ or checkov documentation as a
  community resource — open source the lesson.
