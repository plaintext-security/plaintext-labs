# Lab 11 — Click-ops → IaC Migration: Import a Running Resource to Zero Drift

*Type 12 · Migration / Brownfield. [← Back to the module concept](README.md)*

**Type 12 · Migration / Brownfield.** You take a resource that already exists — created by hand, not by
Terraform — and adopt it under IaC *incrementally, without breaking it*: `import` it into state, write
the matching HCL, reconcile the post-import diff to **zero drift**, and prove the resource served
throughout with a rollback available at every step. The deliverable is the *migration runbook + the
zero-drift `plan` proof + a rollback note* — not a writeup. No grader; you verify your own work against
the observable success criteria below.

## Setup

> **Lab env to be built at promotion** — this module is the curriculum's first Type 12 and has no
> existing `plaintext-labs` directory yet. The shape below is the spec (see the **Lab-env spec** at the
> end of this file); it matches the OpenTofu + `local`-provider pattern of Modules 02/03, so it stands up
> with **zero cloud credentials and zero cost**. Until the env exists, you can run the entire lab against
> the local provider yourself by following the steps — every command below is real and runs on a laptop
> with `opentofu` installed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/<NN>-clickops-iac-migration
make up         # OpenTofu in Docker
make setup      # creates the "click-ops" resources OUT OF BAND (no Terraform) — the brownfield baseline
make plan       # the zero-drift check: passes (exit 0) only once import + reconcile is complete
make shell      # drop into the container to run tofu commands
make down
```

`make setup` is the stand-in for "someone clicked this into existence": a small script writes real files
on the container filesystem (and registers a `local`-provider-managed artifact) **without** any
Terraform — so when you start, the resource is *running* and the Terraform state is *empty*. That gap is
the whole lab. (A cloud variant of the same shape — a security group / bucket created via the AWS CLI,
then imported — ships commented as a reference; the local provider teaches the identical mechanics for
free.)

> **Authorization note:** importing and reconciling against a *cloud* account reads and rebinds real,
> billable resources. In this lab only the `local` provider is active, so nothing is billable and the
> "live resource" is a file. The moment you point any of this at a real account: only ever import
> infrastructure you own or have written permission to manage, and **read every post-import `plan` diff
> before you reconcile** — and never `apply` a change *to* the resource you're trying to leave untouched.

## Scenario
An estate was built by hand in a console before anyone on the team wrote IaC: a couple of resources that
are live, serving, and reproducible by exactly nobody. You've been told to "put it under Terraform" —
and the one rule is **no outage**. You cannot tear it down and rebuild it from clean HCL; it has to keep
serving while you adopt it. So you migrate the strangler-fig way: import one resource at a time, write
the code to match the reality that's already running, prove `plan` shows zero drift, and keep a one-line
rollback at every step. The old path serves the entire time; you're wrapping it in code, not replacing
it.

The rhythm of each slice: **describe → import (state only) → `plan` (read the drift) → reconcile the
code to match → `plan` again → `No changes`.**

## Do
Migrate the brownfield estate under IaC, one resource at a time, proving no outage and zero drift.

**Establish the brownfield baseline (the resource exists; the code does not)**
1. [ ] `make setup` — create the click-ops resources out of band, then confirm they're *live* (the files
   exist, the artifact is serving) **and** that `tofu plan` against your empty config shows Terraform
   knows nothing about them. Record this starting state: *running resource, empty state* — that gap is
   what you're closing.
2. [ ] **Prove the trap before you avoid it** (predict, then confirm). What happens if you "just write
   the IaC"? Write a fresh resource block describing the existing resource and run `tofu plan` *without
   importing*. Read the diff: Terraform plans to **`+ create`** it — i.e. produce a *duplicate* or, on a
   name collision, a destroy-and-recreate. **Do not apply this.** This is the outage the big-bang move
   causes; seeing it on the plan (not in production) is the point.

**Migrate slice 1 — import, reconcile to zero drift**
3. [ ] **Write the matching resource block first.** For the first resource, author the HCL `resource`
   block (correct type + a label you choose) — or declare an `import {}` block and draft a first pass
   with `tofu plan -generate-config-out=generated.tf`, then **review and correct every line** (it's a
   starting point, not trusted output).
4. [ ] **Import — state only.** Bind the real resource to your code's address: `tofu import
   <type>.<label> <real-id>` (or `apply` the `import {}` block). Confirm the resource is **untouched** —
   it's still serving, byte-for-byte identical; only the state file changed (`tofu state list` now shows
   the address).
5. [ ] **Read the post-import drift.** Run `tofu plan`. It will almost certainly show a diff — attributes
   the real resource has that your HCL doesn't yet name. Each line is a *gap between code and reality*.
6. [ ] **Reconcile by editing the CODE, never the resource.** Close every diff line by adding/adjusting
   attributes in your HCL to match what the resource actually has — **not** by applying changes to the
   resource. Re-run `tofu plan`. Iterate until it reports **`No changes. Your infrastructure matches the
   configuration.`** That line is slice 1's done signal: zero drift.
7. [ ] **Confirm no outage + capture the rollback.** Confirm the resource served continuously (it was
   never destroyed/recreated — import touches only state). Write the one-line rollback for this slice and
   *verify it*: `tofu state rm <type>.<label>` forgets the resource without touching it; confirm the
   resource is still live and `plan` is back to "Terraform knows nothing." Then re-import to restore.

**Migrate slice 2 — same loop, prove the rest still works**
8. [ ] Repeat steps 3–7 for the second resource. The strangler-fig constraint: while you migrate slice 2,
   **prove slice 1 is still under management and still serving** (its `plan` stays `No changes`) and the
   un-migrated remainder is still live. You shift one slice at a time; nothing else moves.

**Prove the whole estate is migrated with zero drift**
9. [ ] With every resource imported and reconciled, run `tofu plan` over the full config and confirm a
   single **`No changes`** across the whole estate. The click-ops estate is now governed code: the
   imported reality *equals* the HCL, end to end. Save this plan output — it's your proof.

## Success criteria — you're done when
- [ ] You can show the starting gap: the resource was **live with an empty Terraform state**, and a
      no-import `plan` proves Terraform would have *created a duplicate* (the trap you avoided).
- [ ] Every resource is bound to code via `import` (state changed; the resource was **never**
      destroyed/recreated — verified, not assumed).
- [ ] The post-import diff was closed by **editing the HCL to match reality**, and you can point to at
      least one attribute you added because the real resource had it and your first draft didn't.
- [ ] `tofu plan` over the full migrated estate reports **`No changes. Your infrastructure matches the
      configuration.`** — zero drift, captured as output.
- [ ] You have a **per-slice rollback** (`tofu state rm`) that you *ran* at least once and proved leaves
      the resource serving — the old path never went down.

## Deliverables
Commit to your portfolio repo:
- `migration-runbook.md` — the ordered, strangler-fig runbook: per slice, the resource, the `import`
  command/`import {}` block used, the attributes you had to add to reconcile, and the order you migrated
  in (and *why* that order — least-risky first).
- `*.tf` — your final, reconciled HCL for the whole estate (the code that now equals reality).
- `zero-drift-proof.md` — the terminal capture of the full-estate `tofu plan` showing `No changes`, plus
  the before state (no-import `plan` showing a `+ create` for the same resource) so the migration is
  visible as a transition.
- `rollback-note.md` — the per-slice `tofu state rm` rollback, with the one capture proving the resource
  stayed live after a rollback.

Do **not** commit: `terraform.tfstate` (it now contains the real resource bindings — treat it as the
credential Module 02 taught it is), `.terraform/`, `generated.tf` scratch output, or the seeded
`make setup` artifacts (they live in the lab repo, not yours).

## Automate & own it
**Required — this is the migration's safety surface made into a habit.** The zero-drift `plan` is only
useful if it can't silently regress. Build `make plan` into a **drift gate**: a small script
(`drift-check.sh`) that runs `tofu plan -detailed-exitcode` over the migrated estate and asserts the
**exit code is `0`** (no changes) — failing loudly on exit `2` (drift present) and distinguishing it
from exit `1` (a *tooling error*, which is not a clean pass). Wire it as the `make plan` target so
"prove the imported reality still equals the code" is one command anyone can run after the migration.
**Have a model draft the exit-code logic; review every line** — confirm a crashed plan (`1`) can never
read as zero-drift (`0`), and that the gate fails on real drift, not on noise. This is the same
detailed-exitcode pattern Module 03's gate uses, pointed at drift instead of misconfig. (AI drafts; you
prove the signal is honest and you own it.)

## AI acceleration
Ask a model to write the matching HCL for a resource you describe — then refuse to trust it: `import`,
`plan`, and read the diff line by line, because the model guessed at attributes the real resource may or
may not have. The transferable skill is reconciling that diff by *editing the code*, and catching the
model's most dangerous instinct: when you say "make the plan clean," it will suggest `apply`-ing its
guesses **onto** the live resource — the exact move that mutates the thing you're migrating. Make it
draft; you decide, per diff line, "edit the code to match" versus "never apply this to the resource."
Then ask it: "what attributes does this resource type usually have that my config is missing?" — and
verify each against the actual `plan`, not the model's claim.

## Connects forward
This closes the loop opened in Module 02 (build greenfield IaC) and Module 03 (gate it): now that a
brownfield resource is imported and at zero drift, it is finally *governed code* — and therefore
*scannable* by the Module 03 checkov/tfsec gate, which could see nothing while the resource lived only
in the console. The same import→reconcile→zero-drift loop is the foundation for **Module 04's drift
detection** (Type 16): once everything is under management, `tofu plan` (or a config-management
`--check`) becomes the steady-state drift meter, and reconciliation is the loop you run on a schedule.
Brownfield adoption is the *one-time* migration; drift detection is the *ongoing* version of the same
zero-drift discipline.

## Marketable proof
> "I migrate brownfield infrastructure under IaC without downtime — strangler-fig, one resource at a
> time: `terraform import` to adopt the running resource into state, write the matching HCL, and
> reconcile the post-import diff by editing the code until `plan` reports zero drift. The resource serves
> throughout, every slice has a `state rm` rollback, and once imported it's finally under the same
> security-scan gate as everything else. I can explain why an empty state makes Terraform try to *create
> a duplicate*, and why you reconcile the code to the resource, never the resource to the code."

## Stretch
- **Prefer the `import {}` block** over the CLI command for the whole migration, so each import is a
  reviewable line in `plan` (the modern, code-reviewable form) — and discuss why that's better for a team
  migration than ad-hoc `tofu import` runs.
- **Reconcile a deliberately-wrong draft:** have a model generate HCL with a couple of *wrong* attribute
  values, import, and use the `plan` diff to find and fix them — proving the diff (not the draft) is the
  source of truth.
- **Order-of-operations under dependencies:** add a second resource that *depends on* the first (a file
  referencing another's path) and migrate them in the correct order, showing why strangler-fig sequencing
  matters when resources reference each other.

---

## Lab-env spec (to be built at promotion)

*This module has no `plaintext-labs` directory yet; build it at promotion under
`plaintext-labs/automation/<NN>-clickops-iac-migration/` (final `<NN>` per the placement decision —
insert-after-03-and-renumber, or append-as-11). Match the OpenTofu + `local`-provider shape of Modules
02/03 so it runs with zero cloud cost. It must contain:*

- **`setup.sh` (driven by `make setup`)** — creates the **brownfield baseline out of band, with no
  Terraform**: writes 2–3 real files on the container filesystem (and, where the `local` provider is the
  managed type, a `local_file`-style artifact created directly so it exists *before* any state does).
  Idempotent; re-runnable. This is the "someone clicked it into existence" stand-in — the resources must
  be **live with an empty Terraform state** at lab start.
- **A starter HCL skeleton** — `provider "local"` configured and an *empty* (or commented) resource area,
  so step 2's "just write the IaC" no-import `plan` demonstrably shows a `+ create` for an
  already-existing resource (the trap). The full reconciled `*.tf` is the learner's deliverable, not
  shipped.
- **An import target reference** — the real resource ID/path for each baseline resource (so the learner
  can run `tofu import <addr> <id>`), documented in the lab README, plus an `import {}`-block example for
  the stretch.
- **`make plan` → the zero-drift gate** — runs `tofu plan -detailed-exitcode` over the migrated estate
  and asserts **exit 0 == zero drift**, distinguishing exit `2` (drift) from exit `1` (error). This is
  the env's `demo` equivalent and the success signal; it should *fail* before migration and *pass* after.
- **`Makefile`** — `up` / `setup` / `shell` / `plan` / `down` (+ a `reset` that re-runs `setup` from
  clean). The container ships `opentofu` installed, matching Modules 02/03.
- **A commented cloud reference** — the same migration against a real AWS resource (e.g. a security group
  or S3 bucket created via the CLI, then `tofu import`-ed), shipped commented as the bridge to real
  accounts — never run in CI (no `.ci-demo`; it needs credentials and is a learner/cloud exercise).
- **CI note:** the local-provider path is CI-runnable — add `.ci-demo` only once `make up && make setup
  && make plan` (fail-before / pass-after the learner completes the import) is green on a Linux runner;
  since `make plan` is *expected to fail until the learner finishes*, the marker likely stays off (it's a
  learner-exercise lab, like Module 03's gate).
