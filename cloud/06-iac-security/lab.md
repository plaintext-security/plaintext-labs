# Lab 06 — Encode the Verdict as a Gate: Scan, Fix, Suppress, Block the Merge

*Variant D · build-first, judgment-as-code. [← Back to the module concept](README.md)*

> **Hands-on lab.** Environment: `plaintext-labs/cloud/06-iac-security` (one container: **checkov +
> tfsec + trivy**, pinned — pure static analysis, no cloud account, nothing ever deployed). Objective:
> **scan a real misconfigured Terraform module library, triage pattern vs. decision, then leave behind a
> CI gate that fails the bad config and passes the fix.** Target: **~90 min**, one finish line — the gate
> flips by exit code.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The misconfig ships first as a line of Terraform.** | Catch it in the PR diff — before `apply`, not in a prod audit months later. Shift-left, literally. |
| 2 | **A scanner is a fast junior reviewer with no context.** | It catches the *pattern* instantly across ten thousand files; it can't tell the intended open port from the catastrophic one. |
| 3 | **Split every finding: pattern → fix, decision → you.** | Known-bad pattern is throughput (the junior is right). The bad *decision* is where you add value the tool can't. |
| 4 | **A suppression is an audit trail, not a mute button.** | Inline `checkov:skip=CKV_… : <rationale>` on a *true* false-positive is senior. A blanket `--skip-check` across the codebase ships the real exposure. |
| 5 | **The three scanners overlap but don't match.** | checkov / tfsec / trivy each miss things the others catch — coverage is a triage input, not a given. |
| 6 | **The deliverable is the gate, proven by exit code.** | Non-zero on the original tree, zero on the fix. A check that doesn't change its exit code isn't a gate — it's a report. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [mental model](README.md#the-mental-model-a-scanner-is-a-fast-junior-reviewer-with-no-context) and the
> [scan-before-deploy gate diagram](README.md#where-the-breaches-actually-start).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A scanner flags **two** `0.0.0.0/0` security-group rules with **identical** findings — one on port 443,
   one on port 5432. Why can it never tell you which to fix, and what does that tell you about where your
   value lives?
2. Your scan passes the fixed Terraform. Why is that *not* the deliverable — what must the gate also do?

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/06-iac-security
make up            # build the container (checkov, tfsec, trivy pinned)
make demo          # run all three scanners over data/terraform/
make checkov       # or run one at a time:
make tfsec
make trivy-config
make shell         # drop in to work interactively
make down          # stop when done
```

`data/terraform/` is a snapshot of the target account's module library — the same shapes behind the real
breaches: an unencrypted S3 bucket with no public-access block (`s3.tf`), `0.0.0.0/0` ingress on SSH/RDP/
PostgreSQL plus an *intentional* public-HTTPS rule (`sg.tf`), wildcard `s3:*`/`ec2:*` and `iam:PassRole`
IAM with an `AdministratorAccess`-attached Lambda role and a `Principal: "*"` trust (`iam.tf`), a public,
unencrypted RDS instance with a **literal password** (`rds.tf`), and an unencrypted EBS volume with IMDSv2
not enforced (`ebs.tf`). `data/workflow-template.yml` is your CI starting point.

> **▸ On track if:** `make demo` prints three scanner reports and checkov's summary line reads
> `Passed checks: … , Failed checks: N` with **N in the double digits** — the seeded library is live and
> the tooling works.

> **Static-analysis lab — nothing here touches a real account.** The authorization rule still stands as a
> habit: only scan and deploy infrastructure you own or have written permission to change.

---

## Scenario

The target account's platform team writes Terraform; nobody built security into the pipeline. You have the
module library and one job that matters more than the scan: **leave behind a gate** that blocks any future
PR re-introducing these misconfigurations, while letting the genuinely-intended ones through. The scan
finds the bad patterns; *you* render the verdict on the decisions; the gate makes the verdict permanent.

Each step runs the same rhythm: **scan → triage (pattern vs. decision) → fix or suppress → prove the gate
flips.**

---

## Build it — read a little, do a little

### Step 1 — Predict, then scan

**Concept (30 sec):** Flight-card #1–2. The scanner catches the visible *pattern* fast; the teaching event
is the **miss** — the dangerous line it structurally can't decide.

**Predict, then do:** before running anything, read `s3.tf`, `sg.tf`, `iam.tf`, `rds.tf`, `ebs.tf` and
write two lists — lines a scanner will **FAIL**, and dangerous lines it will **MISS**. Then
`make demo` (or the three `make checkov` / `make tfsec` / `make trivy-config` targets), and grade the
prediction. For the matrix later, grab JSON inside `make shell`:
`checkov -d data/terraform --output json`, `tfsec data/terraform --format json`,
`trivy config data/terraform --format json`.

> **▸ On track if:** checkov shows **double-digit FAILED checks** and you can point at real IDs —
> `CKV_AWS_24` (SSH `0.0.0.0/0`), `CKV_AWS_25` (RDP), the RDS and EBS encryption checks. Then confirm the
> **misses**: no tool flags `password = "changeme-before-deploy"` in `rds.tf` as a *secret*
> (that's `gitleaks`/module 07's job), and **no tool** knows the port-443 rule is intended while port-5432
> is a real exposure — same pattern, opposite verdict. **Record** one line: *what the scanner saw vs. what
> it couldn't decide.*

### Step 2 — Triage: pattern vs. decision

**Concept (30 sec):** Flight-card #3. Every finding sorts into `fix` (the junior is right) or `decide`
(needs your context). That verdict column is what you'd hand an engineering team.

**Do it:** build the consolidated finding matrix — one row per unique misconfiguration:
`Resource | Misconfiguration | Detected By (checkov/tfsec/trivy) | CIS Control | Severity | Verdict`. Then
**read two checks to the source**: pick one HIGH from checkov and one from tfsec, look up the *exact field*
each tests (`github.com/bridgecrewio/checkov`; `aquasecurity.github.io/tfsec`), confirm it against the
`.tf`, and write the corrective attribute.

> **▸ On track if:** every misconfigured resource has a row, a CIS mapping, and a `fix`/`decide` verdict —
> and at least one finding appears in one tool but **not** another (coverage is not identical). A finding
> you can't trace to a field is one you can't defend in review.

### Step 3 — Fix a known-bad pattern, prove green

**Concept (30 sec):** Flight-card #3, the `fix` half — pure throughput. This is the red→green you'll gate.

**Do it:** enable encryption on the EBS volume (`encrypted = true` in `ebs.tf`), then re-scan just that
rule: `checkov --check CKV_AWS_8 -d data/terraform`. Do the same for one more — RDS
`storage_encrypted = true` (or add `aws_s3_bucket_server_side_encryption_configuration` for `_data`) and
re-scan its specific check.

> **▸ On track if:** the check you fixed flips **FAILED → PASSED** on the targeted re-scan
> (`checkov --check CKV_AWS_8 …` reports that check under *Passed* and no longer under *Failed*), while the
> rest of the tree still fails. That single flip is the atom the gate is built from.

### Step 4 — The judgment move: suppress one *true* false-positive correctly

**Concept (30 sec):** Flight-card #4. The port-443 `0.0.0.0/0` in `sg.tf` is the public ALB — it *should*
accept internet HTTPS. Over-rule the junior on the record, without muting the catastrophic siblings.

**Do it:** add the inline suppression with a real rationale on the 443 rule and re-scan:
`# checkov:skip=CKV_AWS_260: Public HTTPS ingress required for internet-facing ALB — approved <name/date>`.
Then **prove you didn't over-mute**: confirm the **port-22, port-3389, and port-5432** `0.0.0.0/0` findings
are *still firing*.

> **▸ On track if:** the 443 finding is silenced on re-scan **and** the SSH/RDP/PostgreSQL `0.0.0.0/0`
> findings still appear. A blanket `--skip-check CKV_AWS_260` would silence all four — that's the
> anti-pattern. **Record** the difference: a suppression is an audit trail, not a mute button.

### Step 5 — Encode the verdict as the gate

**Concept (30 sec):** Flight-card #6. The scan is disposable; the gate is the deliverable. It must *fail*
the bad state and *pass* the fix, and it can't regress when someone copies the module.

**Do it:** starting from `data/workflow-template.yml`, write `iac-scan.yml` — a GitHub Actions workflow on
`pull_request` that runs checkov over the Terraform and **fails the PR on HIGH/CRITICAL** while soft-failing
lower severities (`soft_fail_on: MEDIUM,LOW,INFO`), uploading SARIF. Validate it with `actionlint`.

> **▸ On track if:** the gate's contract holds — it **fails** on the *original* `data/terraform/` (the
> wildcard IAM, the public RDS, the SSH/RDP/DB `0.0.0.0/0`) and **passes** on the *fixed* tree (encryption
> fixes applied, port-443 suppressed with rationale, the dangerous open ports closed).

---

## Prove the control (your finish line)

Run the gate's exact checkov command locally against **both** trees and check the **exit code**:

```bash
checkov -d data/terraform --hard-fail-on HIGH,CRITICAL ; echo "exit: $?"   # original → non-zero
# apply your fixes + the one documented suppression, then:
checkov -d fixed-terraform --hard-fail-on HIGH,CRITICAL ; echo "exit: $?"  # fixed → 0
```

**You're done when the bad Terraform FAILS the gate (non-zero exit) and the fixed tree PASSES (zero).** A
gate that doesn't change its exit code between bad and good isn't a gate; it's a report. This one assertion
is the whole module. Score your two warm-up answers and your predict-the-miss list against what the scan
actually did.

---

## Recall check — close the doc, answer from memory (3 min)

1. A scanner flags two identical `0.0.0.0/0` findings. Why can it never tell you which to fix, and where
   does that put your value?
2. When is an inline `checkov:skip` the *right* move — and what makes a suppression an audit trail rather
   than a mute button?
3. Your scan passes the fixed Terraform. Why is that not the deliverable, and what must the gate also do?

---

## Deliverables

Commit to your portfolio repo:

- **`finding-matrix.md`** — the consolidated cross-tool table with the `fix`/`decide` verdict column.
- **`iac-scan.yml`** — the CI gate (validated with `actionlint` or GitHub's validator).
- **`gate-proof.md`** — two terminal captures (exit code on original vs. fixed) proving the gate flips,
  plus the one-line justification for the port-443 suppression.

Do **not** commit: `/tmp/*.json` scanner output, any `*.tfstate`, or `data/terraform/` itself (it's seeded
in the lab repo, not yours).

## Automate & own it

**Required — this is the judgment-as-code core of the whole track, and the CI gate *is* the automation.**
Your finding is "these patterns must never re-enter the pipeline, and these intended exceptions must stay
allowed." Harden `iac-scan.yml` into something portable: `gate.sh`, a single script that

1. runs checkov (and optionally tfsec/trivy) over a directory passed as `$1`,
2. **exits non-zero iff** there is any HIGH/CRITICAL finding that is *not* a documented inline
   suppression — so an undocumented blanket-skip can't sneak a real exposure past the gate,
3. prints which finding IDs blocked it.

Then write the proof harness: run `gate.sh data/terraform/` (original → exit 1) and `gate.sh` on your
fixed tree (→ exit 0), and assert the flip. **Have a model draft the jq filters and the exit-code logic;
review every line** — confirm a *scanner error* doesn't read as a *clean pass*, and that the gate fails the
original for the *right* finding (the IAM/RDS exposure), not an unrelated nit. This gate is what every
downstream build module (07, 08) and the capstone reuse; it is your verdict, made un-recurrable.

## Definition of done (`iac-security` ✅)

- [ ] All three scanners ran; `finding-matrix.md` covers every misconfigured resource with a CIS mapping
  *and* a `fix`/`decide` verdict per row.
- [ ] At least two known-bad patterns fixed and verified **FAILED → PASSED** on a targeted re-scan.
- [ ] The port-443 rule is suppressed with an inline rationale **and** the port-22/3389/5432 findings still
  fire — you over-ruled the junior on one decision without muting the others.
- [ ] You can name at least two dangerous things the scanner did *not* catch (the literal RDS password; the
  intended-vs-catastrophic open-port distinction).
- [ ] `iac-scan.yml` / `gate.sh` exits **non-zero on the original tree and zero on the fixed tree** —
  demonstrated with `$?`.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

This gate is the keystone of the track's build half. **Module 07** adds secret-scanning (gitleaks) for the
RDS password this config scanner *missed*; **Module 08** wraps the gate into a fully hardened pipeline
(pinned actions, least-priv tokens, SBOM); the **Phase 1 project** ships a real-breach account's fix *as
Terraform gated by this scanner in CI*; and the **capstone** bar is literally this gate's contract — a
green `terraform apply` rebuilds the fixed system, the gate fails the original config, the detection fires
on the simulation but not benign traffic. Upstream, this is module 01's "encode the fix as a guardrail"
made real.

## Marketable proof

> "I scanned a Terraform codebase with checkov, tfsec, and trivy; triaged findings into known-bad
> patterns versus context-dependent decisions; correctly suppressed a true false-positive with a
> documented rationale *without* muting the real exposures next to it; and shipped the CI gate that fails
> the merge on the original config and passes only the fix — proven by exit code. I can explain what a
> static scanner structurally cannot catch (the intended-vs-catastrophic open port, the secret in a
> variable, IAM that composes into admin) and why the gate needs a human verdict wrapped around it."

## Stretch

- Write a **custom Checkov check** (Python or YAML) that encodes a specific verdict no built-in rule covers
  — e.g. *every* resource must carry `Owner`/`Environment`/`CostCenter` tags — and add it to the gate. This
  is judgment-as-code at its purest: your org's rule, mechanically enforced.
- Add a `pre-commit` hook (the `checkov` pre-commit) so misconfigs fail *before* push, and a secret-scan
  (`gitleaks`) hook that catches the `rds.tf` password the config scanner missed — closing the gap you
  found in Step 1.
