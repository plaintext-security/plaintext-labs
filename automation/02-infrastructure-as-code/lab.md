# Lab 02 — Infrastructure as Code

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate.** You build a reproducible infrastructure definition from zero, run its
full `plan → apply → destroy` lifecycle, and ship it reviewed. The deliverable is the *running,
reviewed config* — proved reproducible — not a writeup. No grader; you verify your own work against
the observable success criteria below.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/02-infrastructure-as-code
make up        # OpenTofu in Docker
make demo      # runs tofu init && tofu plan against data/main.tf
make shell     # drop into the container to run tofu commands
make down
```

`data/main.tf` uses the `local` provider to create files on the container filesystem — **no cloud
credentials, no cost, no billable resources**. `data/aws-example.tf` is a commented cloud reference
config for learners who later want to point these skills at a real account. The container ships with
`opentofu` installed.

> **Authorization note:** `tofu apply` against a *cloud* provider creates real, billable, destroyable
> resources. In this lab only the `local` provider is active, so apply is safe. The moment you point
> any of this at a real account: only ever run it against infrastructure you own, and **read the plan
> diff before you apply.**

## Scenario
A new cloud team needs an IaC baseline they can stand up, tear down, and reproduce on demand — a
versioned, reviewed configuration that replaces the click-ops habit of building things by hand in a
console. You're building that baseline against the local provider first, so the team can practice the
full lifecycle and the plan-review discipline before a single real resource is at stake. Everything
you learn here transfers verbatim to a cloud provider; only the `provider` block changes.

## Do
Build it, operate it, then prove it's reproducible from zero.

**Build & operate the lifecycle**
1. [ ] `make demo` — watch `tofu init` download the provider and `tofu plan` print what it *will*
   create. Read the plan: how many resources are being added, and which lines say `+ create`?
2. [ ] Inside the container (`make shell`), `tofu apply -auto-approve` against `data/main.tf`. Confirm
   the output files appear under `data/output/`.
3. [ ] **Treat state as a credential.** Open `terraform.tfstate`. Find the `id` field for each
   resource and note that the file records resource *attributes* verbatim — in a cloud config this is
   where database passwords and API keys would sit in plaintext. Confirm `terraform.tfstate` is in
   `.gitignore` and understand *why* (it never goes in git; in real use it lives in an encrypted,
   locked backend).

**Read the plan-diff — your safety surface**
4. [ ] Change the `content` of one `local_file` resource in `data/main.tf`. Run `tofu plan` and
   confirm the diff reads `~ update in-place`, **not** `-/+ destroy and then create`. (Goal: see the
   difference between an update and a replacement — the replacement is the line where, in prod, a real
   resource would be destroyed.)
5. [ ] Now force a replacement: change a field Terraform can't update in place (e.g. the `filename`).
   Run `tofu plan` and watch the diff flip to `-/+` (destroy + create). This is exactly the diff you
   must catch before applying to anything real.

**Parameterise so it's reusable and harder to misconfigure**
6. [ ] Confirm/define a variable `env_name` (type `string`, default `"staging"`) and use it in the
   file content. Run `tofu plan -var env_name=production` and confirm the variable flows into the plan.
   (Hint: a value taken as a variable is one a reviewer can see change in the diff — the opposite of a
   value baked in silently.)
7. [ ] Define an `output "config_path"` that prints the path of a created file. `tofu apply` and
   confirm the output prints.

**Prove reproducibility from zero**
8. [ ] `tofu destroy` — confirm every resource is removed and `data/output/` is empty.
9. [ ] Re-run `tofu apply` from the destroyed state. Confirm the same files come back **identically**.
   This is the whole point of IaC: the config *is* the infrastructure, reproducible from zero.

## Success criteria — you're done when
- [ ] `tofu apply` runs cleanly and creates the output files; `tofu destroy` removes them all.
- [ ] You can point at a `~ update in-place` line and a `-/+ replace` line in a plan and explain why
      the replacement is the dangerous one.
- [ ] A variable is defined and visibly flows into the plan; an output is defined and prints.
- [ ] `terraform.tfstate`, `data/output/`, and `.terraform/` are all in `.gitignore`, and you can say
      in one sentence why the state file in particular must never be committed.
- [ ] `destroy` then `apply` reproduces the identical files — the config is reproducible from zero.

## Deliverables
Commit `data/main.tf` (your version with the variable and output) and the extended `Makefile` (below).
Confirm `.gitignore` covers `data/output/`, `terraform.tfstate`, and `.terraform/`. **Reviewed,
reproducible-from-zero infrastructure-as-code, committed** — that's the artifact. Lab *artifacts* (the
generated `output/` files, the `tfstate`) stay out of the commit.

## Automate & own it
**Required — this is the safety surface made into a habit.** Add two `Makefile` targets so the apply
can only ever run the plan you reviewed:
- `make plan` → `tofu plan -out=tfplan` (saves the reviewed plan to a file)
- `make apply` → `tofu apply tfplan` (applies *that saved plan*, not a freshly-recomputed one)

Have a model draft the targets, then **review every line and prove the guarantee holds**: run `make
plan`, change `data/main.tf` *without* re-running `make plan`, then `make apply` — and confirm Tofu
*refuses* because the saved plan is stale. That refusal is the whole point: the apply executes exactly
what was reviewed, or nothing. Commit the extended Makefile alongside the config. (AI drafts; you prove
it's safe and you own it.)

## AI acceleration
Ask a model to generate a Terraform config for a simple local file structure — then refuse to trust
it. Run `tofu plan` and read the diff line by line *before* you apply: does any line read as a
destroy/replace you didn't ask for? Then ask the model: "Where would this fail if moved to a cloud
provider without modification?" and hunt for what it gets wrong — hardcoded values that should be
variables, secrets baked into resource arguments (which would land in state), missing provider config,
and local-only assumptions (relative paths) that don't translate to cloud. The transferable skill is
not prompting for HCL; it's reading the plan and catching the dangerous line.

## Connects forward
Module 03 wires a scanner (`checkov`/`tfsec`) over a config like this one and turns "read the diff
yourself" into an automated gate that blocks `apply` on a misconfiguration. The Click-ops → IaC
*migration* module (Type 12) takes infrastructure that already exists, `import`s it into state, and
refactors it to HCL with zero drift — the brownfield reality. Module 10 hands you an AI-generated
Terraform config and asks you to review it adversarially; the plan-reading and state-awareness you
built here are what catch the dangerous lines.

## Marketable proof
> "I write infrastructure as code with OpenTofu/Terraform — plan before apply, the saved-plan gate so
> the apply runs exactly what I reviewed, variables for reuse, outputs for integration — and I treat
> the state file as the credential it is: never in git, always in an encrypted backend."

## Stretch
- Add a `data "local_file"` data source that reads an existing file and outputs its content —
  demonstrating the difference between a managed resource and a data source (read, don't own).
- Write a second `.tf` that uses `for_each` over a map in `tofu.tfvars` to create N files from one
  block — your first taste of HCL that scales without copy-paste.
- Add a `precondition` (or `validation` on the `env_name` variable) that rejects an unexpected value —
  a tiny guardrail that fails the plan early rather than producing a wrong resource.
