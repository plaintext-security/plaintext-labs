# Module 02 — Infrastructure as Code

*Type 7 · Build-&-Operate — ship a working, reproducible infrastructure definition and run its full lifecycle; the deliverable is the running, reviewed config, not an essay. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *if you clicked it into existence, you can't prove it's correct, you can't reproduce it, and you can't review it.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3.5–4.5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) (esp. 03 Docker, 11 Version Control)
{ .module-meta }

## Why this matters

Infrastructure built by clicking through a web console is configuration that exists in exactly one
place: the live account. There is no version history, so you can't see who changed what or when; no
peer review, so a wrong rule ships the instant someone saves it; and no way to reproduce it, so the
day the account is gone, the knowledge is gone with it. A security group widened to `0.0.0.0/0` by
hand has no PR to catch it and no prior state to roll back to. This is **click-ops**, and the toil it
generates — re-doing the same setup in three environments, drift between "what we think is deployed"
and "what's actually live," the 2 a.m. archaeology of *why is this port open* — is exactly what
Infrastructure as Code (IaC) eliminates. The config becomes a file, the file lives in git, and every
change is a reviewable diff before it ever touches the account.

But IaC moves the danger as much as it removes it. The same `apply` that builds a hundred resources
from one command can **destroy** a hundred from one command. The stakes here are real and
well-documented:

- **The state file leaks your secrets.** Terraform/OpenTofu record what they built in a state file
  (`terraform.tfstate`), and that file stores resource attributes — including database passwords, API
  keys, and private keys — in **plaintext**. Researchers scanning public sources have repeatedly found
  exposed `terraform.tfstate` files (committed to public GitHub repos, left in open S3 buckets)
  handing over live credentials to anyone who looks — in Sysdig's [SCARLETEEL operation](https://www.sysdig.com/blog/cloud-breach-terraform-data-theft)
  (Feb 2023), attackers pulled cleartext IAM access keys straight from a `terraform.tfstate` file
  in an S3 bucket and used them to pivot into a second AWS account.
- **A destructive plan applied to prod.** Run `terraform apply` (or worse, `terraform destroy`)
  against the wrong workspace, or merge a refactor that the tool reads as "replace this database," and
  the apply will do it — fast, in order, with no human in the loop. In one widely-read [post-mortem](https://alexeyondata.substack.com/p/how-i-dropped-our-production-database)
  (Mar 2026), DataTalks.Club's Alexey Grigorev describes how an agent pointed at a stale state file
  ran `terraform destroy` and wiped 2.5 years of production — RDS database, VPC, ECS cluster, and
  load balancers — in one unreviewed apply.

Both failures share one root cause: **the apply ran without the diff being read.** That is the
judgment this module is built around.

## The core idea

Terraform and its open-source fork **OpenTofu** share the same declarative model and language — HCL
(HashiCorp Configuration Language). You don't write the steps to build infrastructure; you write the
*desired state* — what you want to exist — and the tool computes the *delta* between desired and
current and executes only that. The lifecycle is four verbs: `init` (download providers), `plan`
(show the delta), `apply` (execute it), `destroy` (tear it down).

**The plan-diff is your safety surface — and the whole discipline is: review the diff, never the
apply.** `tofu plan` prints exactly what will be created, changed, or destroyed *before* anything
happens. A change that reads as `~ update in-place` is safe; one that reads as `-/+ destroy and then
create` (a replacement) or `- destroy` is the line where production databases die. Reading that diff
is the review step — the IaC equivalent of reading a PR before merging it. To make that guarantee
hard rather than habitual, you `plan -out=tfplan` to a saved file and `apply tfplan`, so the apply
executes the *exact* plan you reviewed and nothing that drifted in between. This is the same instinct
the whole automation track turns on: **automation makes you faster, including at being wrong — so the
gate (here, the reviewed plan) is the point.**

**State is sensitive, and it's the thing beginners get wrong.** The state file maps your declarations
to real provider IDs (`local_file.config` → an actual path; `aws_instance.web` → `i-0123…`) — without
it the tool can't tell "what I declared" from "what exists." Because it stores resource attributes
verbatim, it routinely contains secrets in plaintext. So: **`terraform.tfstate` never goes in git**,
and in real use it lives in an encrypted, locked backend (S3 + DynamoDB lock, Terraform/Tofu Cloud, a
GitLab/HTTP backend). Treat the state file like a credential, because it often *is* a bundle of them.

The `local` provider is the underused teaching tool that lets you learn all of this with **zero cloud
credentials and zero cost**: it manages real files on your filesystem through the identical
`init→plan→apply→destroy` lifecycle. You practice reading the plan diff, breaking the
update-vs-replace distinction, parameterising with variables, and exposing outputs — the entire
workflow — and only the *provider* changes when you later point the same skills at AWS, Azure, or GCP.
Variables (`variable {}`) and outputs (`output {}`) are what turn a single-use config into a reusable
module: a security group that takes its allowed CIDR as a variable with a sane default is far harder
to accidentally open to the world than one with the CIDR — or the open rule — baked in.

## Learn (~2.5 hrs)

**The lifecycle and language (~1.5 hrs)**
- [OpenTofu — Core Workflow](https://opentofu.org/docs/intro/core-workflow/) (~20 min) — the `init → plan → apply → destroy` loop conceptually, before you run it in the lab. This is the spine of everything below.
- [OpenTofu — Resources, Variables, Outputs, Providers](https://opentofu.org/docs/language/) (~40 min) — read these four language sections only; they cover ~80% of the HCL you'll ever write. Skip the rest for now.

**State — read this part properly, it's where the security is (~30 min)**
- [OpenTofu — State documentation](https://opentofu.org/docs/language/state/) (~20 min) — *why* state exists, what it stores, and why it must live in a backend. Read the "Sensitive Data in State" subsection specifically — that's the secret-leak risk made official.
- [HashiCorp — Backend configuration](https://developer.hashicorp.com/terraform/language/backend) (~10 min) — skim how a remote, encrypted, locked backend replaces a local `tfstate`; you don't need to configure one, just know the shape and why it exists.

**HCL, enough to read it (~20 min)**
- [OpenTofu — Configuration syntax](https://opentofu.org/docs/language/syntax/configuration/) (~20 min) — enough to see HCL is *not* JSON: blocks, expressions, `for_each`, conditionals. You'll read more HCL than you write; this is the reading primer.

## Key concepts
- **Declarative, not imperative:** you write desired state; the tool computes and applies the delta.
- **The plan-diff is the safety surface** — `~ update` is safe, `-/+ replace` and `- destroy` are where prod dies. **Review the diff, never the apply.**
- **`plan -out=tfplan` → `apply tfplan`** so the apply runs the exact plan you reviewed.
- **State is a credential:** `terraform.tfstate` stores secrets in plaintext, never goes in git, lives in an encrypted/locked backend in real use.
- **Variables + outputs** make a config reusable and harder to misconfigure (a CIDR variable beats a hardcoded open rule).
- **The `local` provider** gives the full lifecycle for free — same workflow, only the provider changes when you go to cloud.

## AI acceleration
A model will generate valid HCL in seconds — and that is exactly the risk. AI writes configurations
that are syntactically perfect and security-misconfigured: open security groups, public buckets, no
encryption, secrets hardcoded into resource arguments where they'll land in state. The posture holds:
**AI authors → you review every line → you own it**, and for IaC the review has a concrete shape.
After a model drafts HCL, your *first* action is never `apply` — it's `tofu plan` ("does this do what
I intended, and does any line read as a destroy/replace I didn't ask for?"), and you read the diff
before you trust it. Module 03 wires a scanner (`checkov`/`tfsec`) into this same gate to catch the
misconfigurations automatically. The habit starts here: AI drafts; *you* plan, read the diff, and only
then apply.
