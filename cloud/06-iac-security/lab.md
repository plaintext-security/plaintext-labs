# Lab 06 — Encode the Verdict as a Gate: Scan, Fix, Suppress, Block the Merge

*Variant D · build-first, judgment-as-code. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Everything is **static
analysis**: no cloud account, no Terraform state, nothing is ever deployed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/06-iac-security
make up          # build the container (checkov, tfsec, trivy pinned)
make demo        # run all three scanners over data/terraform/
make shell       # drop in to work
make down        # stop when done
```

`data/terraform/` is a snapshot of the target account's module library — the same shapes behind the real
breaches: an unencrypted S3 bucket (`s3.tf`), `0.0.0.0/0` ingress (`sg.tf`), wildcard `s3:*`/`ec2:*` and
`iam:PassRole` IAM plus an `AdministratorAccess`-attached Lambda role and a `Principal: "*"` trust
(`iam.tf`), a public, unencrypted RDS instance with a literal password (`rds.tf`), and an unencrypted EBS
volume with IMDSv2 not enforced (`ebs.tf`). `data/workflow-template.yml` is your CI starting point.

> Static-analysis lab — nothing here touches a real account. The authorization rule still stands as a
> habit: only scan and deploy infrastructure you own or have written permission to change.

## Scenario

The target account's platform team writes Terraform; nobody built security into the pipeline. You have the module
library and one job that matters more than the scan: **leave behind a gate** that blocks any future PR
re-introducing these misconfigurations, while letting the genuinely-intended ones through. The scan finds
the bad patterns; *you* render the verdict on the decisions; the gate makes the verdict permanent.

The rhythm each part: **scan → triage (pattern vs. decision) → fix or suppress → prove the gate flips.**

## Do

### Part 1 — Predict, then scan

1. [ ] **Commit the prediction (from the README).** Before running anything, read `s3.tf`, `sg.tf`,
   `iam.tf`, `rds.tf`, `ebs.tf` and write two lists: lines a scanner will **FAIL**, and dangerous lines
   it will **MISS**. Keep this — you grade it against the scan output.

2. [ ] **Run all three scanners.** `make demo`, or individually `make checkov` / `make tfsec` /
   `make trivy-config`. Get JSON for the matrix: `checkov -d data/terraform --output json`,
   `tfsec data/terraform --format json`, `trivy config data/terraform --format json`. Count FAILED
   checks per tool. Note findings in one tool but not another — coverage is *not* identical.

3. [ ] **Grade your prediction.** Confirm the scanners caught the patterns (encryption, `0.0.0.0/0`,
   wildcard IAM). Then confirm the **misses**: did any tool flag `password = "changeme-before-deploy"` in
   `rds.tf` as a *secret*? (Mostly no — that's `gitleaks`/module 07's job, not a config rule.) Did any
   tool know the **port-443** `0.0.0.0/0` is intended while the **port-5432** one is a real exposure? (No
   — same pattern, opposite verdict.) **Record** one line: *what the scanner saw vs. what it couldn't decide.*

### Part 2 — Triage: pattern vs. decision

4. [ ] **Build the consolidated finding matrix.** One row per unique misconfiguration:
   `Resource | Misconfiguration | Detected By (checkov/tfsec/trivy) | CIS Control | Severity | Verdict`.
   The **Verdict** column is the point — for each finding, mark `fix` (known-bad pattern) or `decide`
   (needs human context). This is what you'd hand an engineering team.

5. [ ] **Read two checks to the source.** Pick one HIGH from checkov and one from tfsec. Look the check up
   (`github.com/bridgecrewio/checkov`; `aquasecurity.github.io/tfsec`), find the *exact field* it tests,
   confirm it against the `.tf`, and write the corrective attribute. A finding you can't trace to a field
   is a finding you can't defend in review.

6. [ ] **Fix a known-bad pattern, prove green.** Enable S3 encryption on `_data` (add
   `aws_s3_bucket_server_side_encryption_configuration`), then re-scan just that rule:
   `checkov --check CKV_AWS_18 -d data/terraform` (or the relevant ID). Watch it flip FAILED → PASSED.
   This is the red→green you'll gate. Do the same for one more (EBS `encrypted = true`, or RDS
   `storage_encrypted`).

7. [ ] **The judgment move — suppress one *true* false-positive correctly.** The port-443 `0.0.0.0/0`
   ingress in `sg.tf` is the public ALB; it *should* accept internet HTTPS. Add the inline suppression
   with a real rationale and confirm the finding is silenced on re-scan:
   `# checkov:skip=CKV_AWS_260: Public HTTPS ingress required for internet-facing ALB — approved <name/date>`.
   Then **prove you didn't over-mute:** confirm the **port-22, port-3389, and port-5432** `0.0.0.0/0`
   findings are *still firing*. Suppressing the intended rule must not silence the catastrophic ones — a
   blanket `--skip-check CKV_AWS_260` would, which is exactly the anti-pattern. **Record** the difference.

### Part 3 — Encode the verdict as the gate (the deliverable)

8. [ ] **Write the CI gate.** Starting from `data/workflow-template.yml`, write `iac-scan.yml`: a GitHub
   Actions workflow on `pull_request` that runs checkov over the Terraform and **fails the PR on HIGH/
   CRITICAL** while soft-failing lower severities (`soft_fail_on: MEDIUM,LOW,INFO`), uploading SARIF.
   The non-negotiable behaviour, stated as the gate's contract:
   - it **fails** on the *original* `data/terraform/` (the wildcard IAM, the public RDS, the SSH/RDP/DB
     `0.0.0.0/0`), and
   - it **passes** on the *fixed* tree (your encryption fixes applied, the port-443 rule *suppressed with
     rationale*, the dangerous open ports closed).

9. [ ] **Prove the gate flips.** Run the gate's exact command locally against both trees and check the
   **exit code** (`echo $?`) — non-zero on the original, zero on the fix. A gate that doesn't change its
   exit code between bad and good isn't a gate; it's a report. This is the whole module in one assertion.

## Success criteria — you're done when
- [ ] All three scanners ran; your finding matrix covers every misconfigured resource with a CIS mapping
  *and* a `fix`/`decide` verdict per row.
- [ ] At least two known-bad patterns fixed and verified FAILED → PASSED on re-scan.
- [ ] The port-443 rule is suppressed with an inline rationale **and** you proved the port-22/3389/5432
  findings still fire — you over-ruled the junior on one decision without muting the others.
- [ ] You graded your predict-the-miss list: you can name at least two dangerous things the scanner did
  not (the literal RDS password; the intended-vs-catastrophic open-port distinction).
- [ ] `iac-scan.yml` exits **non-zero on the original tree and zero on the fixed tree** — demonstrated
  with `$?`.

## Deliverables
Commit to your portfolio repo:
- `finding-matrix.md` — the consolidated cross-tool table with the `fix`/`decide` verdict column.
- `iac-scan.yml` — the CI gate (validate with `actionlint` or GitHub's validator).
- `gate-proof.md` — two terminal captures (exit code on original vs. fixed) proving the gate flips, plus
  the one-line justification for the port-443 suppression.

Do **not** commit: `/tmp/*.json` scanner output, any `*.tfstate`, or `data/terraform/` itself (it's
seeded in the lab repo, not yours).

## Automate & own it
**Required — this is the judgment-as-code core of the whole track.** Your finding is "these patterns must
never re-enter the pipeline, and these intended exceptions must stay allowed." Encode that verdict as a
**guardrail that fails the bad state and passes the fix** — your `iac-scan.yml` *is* that guardrail, but
harden it into something portable: `gate.sh`, a single script that

1. runs checkov (and optionally tfsec/trivy) over a directory passed as `$1`,
2. **exits non-zero iff** there is any HIGH/CRITICAL finding that is *not* a documented inline
   suppression — so an undocumented blanket-skip can't sneak a real exposure past the gate,
3. prints which finding IDs blocked it.

Then write the proof harness: run `gate.sh data/terraform/` (original → exit 1) and `gate.sh` on your
fixed tree (→ exit 0), and assert the flip. **Have a model draft the jq filters and the exit-code logic;
review every line** — confirm a *scanner error* doesn't read as a *clean pass*, and that the gate fails
the original for the *right* finding (the IAM/RDS exposure), not an unrelated nit. This gate is what every
downstream build module (07, 08) and the capstone reuse; it is your verdict, made un-recurrable.

## AI acceleration
Paste a misconfigured block and ask the model for the minimum attributes to pass the relevant `CKV_AWS_*`
check — fast and reliable for encryption/logging patterns. Where it earns scrutiny: **IAM remediation**
(wildcard "fixes" that move the `*` from `Action` to `Resource`, still broken — trace it through the
permission model from module 02, don't trust the green) and **suppressions** (the model will silence a
*real* exposure as readily as a false-positive). Then adversarially test your own gate: ask the model to
write a Terraform block that re-introduces a public-DB exposure *while passing your gate*. If it can, your
gate (or your suppression policy) is too loose — tighten and re-prove the flip.

## Connects forward
This gate is the keystone of the track's build half. **Module 07** adds secret-scanning (gitleaks) for the
RDS password this config scanner *missed*; **Module 08** wraps the gate into a fully hardened pipeline
(pinned actions, least-priv tokens, SBOM); the **Phase 1 project** ships a real-breach account's fix *as
Terraform gated by this scanner in CI*; and the **capstone** bar is literally this gate's contract — a
green `terraform apply` rebuilds the fixed system, the gate fails the original config, the detection fires
on the simulation but not benign traffic.

## Marketable proof
> "I scanned a Terraform codebase with checkov, tfsec, and trivy; triaged findings into known-bad
> patterns versus context-dependent decisions; correctly suppressed a true false-positive with a
> documented rationale *without* muting the real exposures next to it; and shipped the CI gate that fails
> the merge on the original config and passes only the fix — proven by exit code. I can explain what a
> static scanner structurally cannot catch (the intended-vs-catastrophic open port, the secret in a
> variable, IAM that composes into admin) and why the gate needs a human verdict wrapped around it."

## Stretch
- Write a **custom Checkov check** (Python or YAML) that encodes a specific verdict no built-in
  rule covers — e.g. *every* resource must carry `Owner`/`Environment`/`CostCenter` tags — and add it to
  the gate. This is judgment-as-code at its purest: your org's rule, mechanically enforced.
- Add a `pre-commit` hook (the `checkov` pre-commit) so misconfigs fail *before* push, and a secret-scan
  (`gitleaks`) hook that catches the `rds.tf` password the config scanner missed — closing the gap you
  found in step 3.
