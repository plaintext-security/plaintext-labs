# Lab 02 — Infrastructure as Code

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/02-infrastructure-as-code
make up        # OpenTofu in Docker
make demo      # runs tofu init && tofu plan against data/main.tf
make shell     # drop into the container to run tofu commands
make down
```

`data/main.tf` uses the `local` provider to create two files — no cloud credentials required.
`data/aws-example.tf` is a commented cloud reference example for learners with AWS access.
The container has `opentofu` installed.

> **Authorization note:** `tofu apply` against a cloud provider creates real, billable resources.
> In this lab, only the `local` provider is active. Review any cloud configuration before running
> `tofu apply` against a real account.

## Scenario
Meridian's new cloud team has asked you to write the IaC baseline for a simple asset — a
configuration file that records the environment name and timestamp — so the team can practice
the plan/apply/destroy lifecycle before touching real cloud resources.

## Do
1. [ ] `make demo` — watch `tofu init` download the provider and `tofu plan` show what it
   will create. Read the plan output: which resources are being added?
2. [ ] Inside the container (`make shell`), run `tofu apply -auto-approve` against `data/main.tf`.
   Confirm the two files were created in `data/output/`.
3. [ ] Inspect `terraform.tfstate` — what information does it contain? Find the `id` field for
   each resource. Note: this file would contain secrets in a cloud config; confirm it's in
   `.gitignore`.
4. [ ] Modify `data/main.tf`: change the `content` of one file resource. Run `tofu plan` again —
   confirm the plan shows the change (UPDATE) rather than a full replacement (REPLACE).
5. [ ] Add a variable `env_name` (type `string`, default `"staging"`) and use it in the file
   content. Run `tofu plan -var env_name=production` — confirm the variable appears in the plan.
6. [ ] Add an `output "config_path"` that prints the path of the created file. Run `tofu apply`
   and confirm the output is printed.
7. [ ] `tofu destroy` — confirm all resources are removed.

## Success criteria — you're done when
- [ ] `tofu apply` runs cleanly and creates the output files.
- [ ] The plan correctly shows UPDATE (not REPLACE) for a content change.
- [ ] A variable is defined and passes through to the resource content.
- [ ] An output is defined and printed after apply.
- [ ] `tofu destroy` removes all resources.

## Deliverables
`data/main.tf` (your updated version with variable and output). Commit it. Add `data/output/`,
`terraform.tfstate`, `.terraform/` to `.gitignore`.

## Automate & own it
**Required.** Write a `Makefile` target `plan` that runs `tofu plan -out=tfplan` and a target
`apply` that runs `tofu apply tfplan` (using the saved plan file — this prevents the apply from
executing a different plan than what was reviewed). Have a model generate the Makefile targets;
verify that `make plan && make apply` is safe (does it actually use the saved plan?). Commit the
extended Makefile.

## AI acceleration
Ask a model to generate a Terraform configuration for a simple local file structure. Then ask:
"Where would this fail if moved to a cloud provider without modification?" Look for hardcoded
values that should be variables, missing required provider configuration, and resources that
assume local semantics (relative paths) that don't translate to cloud.

## Connects forward
Module 03 runs security scanners over the cloud example config from this module. Module 10
reviews an AI-generated Terraform config for security misconfigurations — the scanning skills
from 03 and the HCL-reading skills from this module both apply.

## Marketable proof
> "I write infrastructure as code — plan before apply, variables for reuse, outputs for
> integration — and I know what the state file contains and why it never goes in git."

## Stretch
- Add a `data "local_file"` data source that reads an existing file and outputs its content —
  demonstrating the difference between managed resources and data sources.
- Write a second `.tf` file that uses `for_each` to create N files from a `tofu.tfvars` map.
