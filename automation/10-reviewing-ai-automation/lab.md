# Lab 10 — Adversarial Review: Catch What the Model Got Wrong, Codify When to Trust It

*Variant D · adversarial review. [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Everything is **static
review**: no cloud account, no Terraform state, no workflow ever runs. You are reviewing artifacts a model
produced, exactly as they'd land in a pull request.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/10-reviewing-ai-automation
make up          # build the container (checkov, tfsec, gitleaks, actionlint pinned)
make demo        # run the scanners over the AI-generated artifacts (before), and over data/fixed/* if present (after)
make shell       # drop in to work
make down        # stop when done
```

You are handed three artifacts a model generated, each plausible, each linting or applying cleanly, and each
seeded with planted, realistic defects:

- `data/ai_generated_terraform.tf` — a Terraform config for "a data bucket and an instance with admin access."
- `data/ai_generated_workflow.yml` — a GitHub Actions workflow for "a CI job that comments on pull requests and
  deploys on merge."
- `data/ai_generated_destroy.tf` — a Terraform snippet a model produced for "clean up the old staging bucket,"
  which would silently delete a stateful resource on `apply`.

> Static-review lab — nothing here touches a real account or runs a real workflow. The authorization rule still
> stands as a habit: only scan, deploy, or run automation you own or have written permission to change. Do **not**
> run `tofu apply` or trigger any workflow in this lab.


## Scenario

A platform team is shipping fast and leaning on an AI assistant to scaffold its automation. Three pull requests
are open — the Terraform for a new data pipeline, the CI workflow that gates it, and a "cleanup" change — all
AI-drafted, all green in the author's local linter, all with a teammate ready to click merge. Your lead asks for a
**30-minute adversarial review before any of it merges**, and — because this keeps happening — for the artifact
that makes the review repeatable: a checklist and a *trust policy* the team can apply to the next ten AI-drafted
PRs without you in the loop.

The rhythm of each finding: **read the artifact → spot the tell → verify against the primary source → fix or
suppress → record the tell so the checklist captures it.**

## Do

### Part 1 — Find every planted defect, and say how you knew

1. [ ] **Scan first, but don't trust the green.** `make demo` runs `checkov`/`tfsec` over the `.tf`, `actionlint`
   over the `.yml`, and `gitleaks` over `data/`. Record what each tool flagged — *and* note that the workflow
   passes `actionlint` clean while still being dangerous. The scan is your first pass; it is not the review.

2. [ ] **Review the Terraform by hand.** In `data/ai_generated_terraform.tf`, find every security-relevant defect
   (public ACL, wildcard `Action`/`Resource` IAM on the instance profile, no IMDSv2, unencrypted EBS, SSH open to
   `0.0.0.0/0`). For each, write a finding row (format below) — the column that matters is **Tell**: the one thing
   in the line that tipped you off (`a wildcard where a specific value belongs`).

3. [ ] **Review the workflow by hand — this is where the linter is blind.** In `data/ai_generated_workflow.yml`,
   find the defects `actionlint` *cannot* see because they are semantic, not syntactic:
   - the `pull_request_target` trigger that checks out and runs the PR's code (a **pwn request** — a stranger's code
     runs with your secrets and write token),
   - the third-party action pinned to a **mutable tag** (`@v44` / `@main`) instead of a 40-char commit SHA (the
     `tj-actions/changed-files` / CVE-2025-30066 shape),
   - the **over-broad token** (`permissions: write-all` or a missing top-level `permissions:` block),
   - the `run:` step interpolating attacker-controlled `${{ github.event.* }}` into the shell (**script injection**),
   - the hardcoded credential in `env:` (the one thing `gitleaks` *should* have caught — confirm it did).

4. [ ] **Review the "cleanup" change.** In `data/ai_generated_destroy.tf`, determine what `terraform plan` would do
   on `apply`: it **destroys a stateful resource** (`force_destroy = true` on a bucket, or a removed resource block
   that plans a delete). State plainly whether you *demonstrated* this with a local `terraform plan` or *assessed it
   from the config* — and label it honestly either way. A model asked to "clean up" will happily write data loss.

5. [ ] **For every finding, verify against the primary source — not your gut.** Beside each finding row, cite the
   *exact* authority that proves it: the [GitHub hardening docs](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)
   section, the [pwn-requests writeup](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/),
   the [checkov check](https://www.checkov.io/5.Policy%20Index/terraform.html) and the CIS control, the provider
   docs for the destructive attribute. A finding you can't trace to a source is a finding you can't defend in
   review — and "the AI said so" is not a source.

### Part 2 — Catch the model's *plausible-but-false* justification

6. [ ] **Audit the comments and suppressions, not just the code.** The artifacts include at least one model-written
   justification that is confident and wrong — a comment like `# public-read is fine, this data isn't sensitive`,
   or an inline `#checkov:skip=...` with a rationale the model invented. For each, decide: **true false-positive**
   (defensible — keep the suppression, with a *human-authored* rationale you can stand behind) or **the model
   talking itself out of a real defect** (a planted trap — fix the underlying line, delete the bogus skip).

7. [ ] **The one legitimate suppression.** Exactly one finding is a *true* false-positive (the dedicated
   access-logging bucket need not log to itself — a self-logging loop). Suppress it correctly, with a rationale a
   human owns: `#checkov:skip=CKV_AWS_18: Dedicated access-log bucket; self-logging is a loop — approved <name/date>`.
   Then **prove you didn't over-mute**: confirm the real findings (public ACL, wildcard IAM, open SSH) still fire.

### Part 3 — Fix it and prove the fixes hold

8. [ ] **Produce the corrected artifacts.** Write the fixed versions into `data/fixed/`:
   `terraform.tf` (encryption + versioning on, no `public-read`, least-privilege IAM, IMDSv2 required, SG scoped off
   `0.0.0.0/0`), `workflow.yml` (drop `pull_request_target` for untrusted checkout or remove the untrusted checkout;
   **pin every action to a full commit SHA**; set least-privilege `permissions:`; move interpolation into an
   intermediate `env:` var; remove the hardcoded secret in favour of a referenced secret), and `destroy.tf` (guard
   or remove the destructive operation). Re-run `make demo` against `data/fixed/` and confirm the scanners are green
   *and* that your by-hand findings are addressed (the scanners won't confirm the pwn-request fix — you must).

### Part 4 — Codify the verdict: checklist + a *measured* trust policy (the deliverable)

9. [ ] **Write `ai-review-checklist.md`** — a reusable, domain-grouped checklist drawn from the tells you recorded.
   Group by failure mode (authorization · untrusted-input execution · supply-chain pinning · disabled safety
   controls · justification audit), minimum **15 yes/no items**, each phrased as a check a reviewer answers in
   seconds (e.g. *"Is every third-party action pinned to a 40-character commit SHA, not a tag?"*; *"Does any
   `run:` step interpolate `${{ github.event.* }}` directly into the shell?"*).

10. [ ] **Write `trust-policy.md` with a *measured* threshold — this is the module's whole point.** Count it, don't
    vibe it: across the planted defects, record **how many you caught versus how many were planted** (your
    catch rate), and on which domains you missed more. Then state the operable policy:
    - the **threshold** below which an AI-drafted PR may merge with light review and above which it requires full
      human re-derivation (e.g. *"any wildcard, any `pull_request_target`, or any unpinned third-party action ⇒
      full review; otherwise checklist-pass + one reviewer"*),
    - the **never-auto-suppress list** — finding classes that *always* block regardless of any AI justification
      (wildcard IAM, untrusted-input execution, mutable supply-chain refs, destructive ops),
    - the **prompt-side control** — the up-front security instructions you'd prepend to the next generation (from
      the [OpenSSF AI-code-assistant guide](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions.html))
      so the model drafts the safer version first.

## Success criteria — you're done when

- [ ] Your `review.md` finding table covers **every planted defect across all three artifacts**, each with a
  **Tell** and a **primary-source citation** (not "the AI said so", not intuition).
- [ ] You found the defects the linter *cannot* see (the pwn request, the unpinned action, the script-injection
  interpolation) and can name *why* a clean `actionlint` run did not catch them.
- [ ] The destructive-`apply` finding is recorded and **honestly labelled** demonstrated (`terraform plan`) vs.
  assessed-from-config.
- [ ] The true false-positive is suppressed with a *human-authored* rationale, **and** you proved the real findings
  still fire (you over-ruled the junior on one decision without muting the others).
- [ ] `make demo` is green over `data/fixed/` for the scanner-visible findings, and your notes show the
  scanner-*invisible* fixes (pwn request, IMDSv2 reasoning, destructive op) are addressed by hand.
- [ ] `ai-review-checklist.md` has ≥15 grouped yes/no items; `trust-policy.md` states a **measured** catch rate, a
  threshold, a never-auto-suppress list, and the prompt-side control.

## Deliverables

Commit to your portfolio repo:
- `review.md` — the finding table (`Artifact | Line | Defect | Tell | Primary source | Risk | Fix-or-suppress`),
  the destructive-op finding with its honest demonstrated/assessed label, and the AI-vs-scanner comparison from
  *AI acceleration* below.
- `data/fixed/` — the corrected `terraform.tf`, `workflow.yml`, and `destroy.tf`.
- `ai-review-checklist.md` — the reusable, grouped review checklist.
- `trust-policy.md` — the measured trust policy (catch rate · threshold · never-auto-suppress list · prompt-side
  control).

Do **not** commit: scanner JSON output, any `*.tfstate`, raw model transcripts, or the seeded
`data/ai_generated_*` files (they live in the lab repo, not yours).

## Automate & own it

**Required.** Turn the review into a repeatable gate, then a reviewable script — *AI drafts it, you review every
line.* Write `ai-review.sh <dir>` that runs all four scanners (`checkov`, `tfsec` over `*.tf`; `actionlint` over
`*.yml`; `gitleaks` over the tree) and prints one consolidated summary with a **PASS/FAIL** line and the blocking
finding IDs. Then add the move scanners can't make: a small `grep`/`yq` check that **fails on the structural tells
the linters miss** — any third-party `uses:` line not pinned to a 40-char SHA, any `pull_request_target` paired
with a checkout of untrusted code, any `permissions: write-all`. Have a model draft both the `jq`/`yq` filters and
the exit-code logic, then **review every line**: confirm a *scanner crash* doesn't read as a *clean pass* (a
non-zero from an error is not the non-zero from a finding), and test the script against both `data/` (must FAIL)
and `data/fixed/` (must PASS) to prove the flip. Commit `ai-review.sh`. This is your trust policy, made
mechanical — the part of the verdict you no longer have to remember.

## AI acceleration

After your manual review, ask a model to review the same three artifacts for security issues. Do the three-way
comparison and write it into `review.md`: **what did the model catch that the scanners missed? what did the
scanners catch that the model missed? what did the model get *wrong* in its proposed fixes?** Watch especially for
the model "fixing" the wildcard IAM by moving the `*` from `Action` to `Resource` (still broken), "pinning" the
action by adding a version comment instead of a SHA, or confidently declaring the pwn-request workflow safe. That
comparison is the evidence base behind the *number* in your trust policy — it is precisely how you decide when AI
security review is a real second pair of eyes and when it is one more artifact you have to review.

## Connects forward

This module closes the track. You generated infrastructure (02), gated it (03), built the migration (04), operated
the CI/CD pipeline (05), containerised tooling (06), built enrichment (07) and SOAR (08), and shipped
detections-as-code with a scored regression gate (09) — and now you review the AI-drafted versions of all of it
with a measured trust policy instead of a vibe. The checklist and `trust-policy.md` are the artifacts you carry
into any team adopting AI-assisted automation. The `ai-review.sh` gate slots directly into the hardened pipeline
from module 05: the same machine that blocks a human's misconfig now blocks the model's.

## Marketable proof

> "I run adversarial review on AI-generated automation across Terraform and GitHub Actions — I catch the
> structurally-sound, semantically-dangerous defects scanners and linters miss (pwn-request `pull_request_target`,
> unpinned third-party actions in the `tj-actions` class, wildcard IAM, destructive `apply`), I verify each finding
> against the primary source rather than the model's own justification, and I ship a measured trust policy and a
> mechanical gate so my team merges AI-drafted PRs on a number, not a vibe."

## Stretch

- Ask a model to generate an **Ansible playbook** for the same task and review it with `ansible-lint` + a manual
  pass — does AI make the same *category* of mistake (over-broad `become`, `validate_certs: no`, a hardcoded vault
  password) in YAML config as in HCL and workflow YAML? Add the new tells to your checklist.
- **Red-team your own gate:** ask the model to write automation that re-introduces a real exposure *while passing
  `ai-review.sh`*. If it can, your policy or your structural checks are too loose — tighten and re-prove the flip.
- Contribute your `ai-review-checklist.md` upstream (e.g. as an example in the OpenSSF AI-code-assistant guide
  discussion or a checkov/community doc) — open-source the lesson.
