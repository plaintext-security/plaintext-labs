# Lab 03 — Encode the Verdict as a Gate: Scan, Fix, Suppress, Block the Merge

*Variant D · build-first, judgment-as-code. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Everything is **static
analysis**: no cloud account, no Terraform state, nothing is ever deployed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/03-iac-security-scanning
make up          # build the container (checkov + tfsec pinned)
make demo        # run both scanners over data/misconfig.tf
make shell       # drop in to work
make down        # stop when done
```

`data/misconfig.tf` is a platform team's first cloud deployment attempt — the same shapes behind the
real incidents: an S3 bucket with `acl = "public-read"` and no versioning/logging/encryption, a security
group with SSH (`0.0.0.0/0`) open to the world, an IAM role with `Action = "*"` / `Resource = "*"`
attached to an EC2 instance that doesn't enforce IMDSv2. The container has `checkov` and `tfsec`
installed.

> Static-analysis lab — nothing here touches a real account. The authorization rule still stands as a
> habit: only scan and deploy infrastructure you own or have written permission to change.


## Scenario
The platform team writes Terraform; nobody built security into the pipeline. A developer submitted a PR
to create the company's first S3 bucket and a bastion host — the PR description says "just a quick bucket
for file sharing." You have the module and one job that matters more than the scan: **leave behind a
gate** that blocks any future PR re-introducing these misconfigurations, while letting the
genuinely-intended ones through. The scan finds the bad patterns; *you* render the verdict on the
decisions; the gate makes the verdict permanent.

The rhythm of each part: **scan → triage (pattern vs. decision) → fix or suppress → prove the gate flips.**

## Do

### Part 1 — Scan and triage

1. [ ] **Run both scanners.** `make demo`, or individually `checkov -f data/misconfig.tf` and
   `tfsec data/`. Count FAILED checks per tool. Note findings that appear in one tool but not the other —
   coverage is *not* identical, which is why you run both.

2. [ ] **Build the consolidated finding matrix.** One row per unique misconfiguration:
   `Resource | Misconfiguration | Rule ID (checkov/tfsec) | CIS Control | Severity | Verdict`. The
   **Verdict** column is the point — for each finding, mark `fix` (known-bad pattern) or `decide` (needs
   human context). This is what you'd hand an engineering team.

3. [ ] **Read two checks to the source.** Pick one HIGH from checkov (e.g. the S3 encryption or
   wildcard-IAM finding) and one from tfsec. Look the rule up
   ([checkov policy index](https://www.checkov.io/5.Policy%20Index/terraform.html);
   [tfsec docs](https://aquasecurity.github.io/tfsec/latest/)), find the *exact field* it tests, confirm
   it against the `.tf`, and write the corrective attribute. A finding you can't trace to a field is a
   finding you can't defend in review.

4. [ ] **Name what the scanner can't decide.** Record one line: *what the scanner saw vs. what it
   couldn't decide.* The scanner flags `Action = "*"` as a pattern but doesn't know that, attached to the
   bastion's instance profile, it composes into admin on the instance; it has no way to know whether
   `0.0.0.0/0` on a port is an intended public endpoint or a catastrophe. Same pattern, opposite verdict.

### Part 2 — Fix and suppress (the judgment)

5. [ ] **Fix the known-bad patterns, prove green.** Copy `data/misconfig.tf` → `data/fixed.tf` and fix
   every HIGH/CRITICAL: enable S3 encryption and versioning, drop `public-read`, scope the SG ingress off
   `0.0.0.0/0` (or to the intended port only), replace the `*`/`*` IAM with a least-privilege policy,
   enforce IMDSv2 (`metadata_options { http_tokens = "required" }`). Re-scan: `checkov -f data/fixed.tf`
   and `tfsec data/fixed.tf` — watch the FAILED counts drop. This red→green is what you'll gate.

6. [ ] **The judgment move — suppress one *true* false-positive correctly.** One finding is a legitimate
   false positive for this use case: a dedicated logging bucket does not need access-logging *on itself*
   (logging to itself is a loop). Add the inline suppression with a real rationale and confirm the
   finding is silenced on re-scan:
   `#checkov:skip=CKV_AWS_18: Dedicated access-log bucket; self-logging is a loop — approved <name/date>`.
   Then **prove you didn't over-mute:** confirm the *other* findings (public ACL, open SSH, wildcard IAM)
   are *still firing*. Suppressing the intended exception must not silence the real exposures next to it —
   a blanket `--skip-check CKV_AWS_18` across the codebase would, which is exactly the anti-pattern.
   **Record** the difference.

### Part 3 — Encode the verdict as the gate (the deliverable)

7. [ ] **Write the CI gate.** Write `iac-scan.yml`: a GitHub Actions workflow on `pull_request` (paths
   `**/*.tf`) that runs checkov over the Terraform and **fails the PR on MEDIUM-or-higher** while
   soft-failing LOW/INFO (`--soft-fail-on LOW`), pinning the action to a commit SHA and uploading SARIF.
   The non-negotiable behaviour, stated as the gate's contract:
   - it **fails** on the *original* `data/misconfig.tf` (the public ACL, open SSH, wildcard IAM, no
     IMDSv2), and
   - it **passes** on the *fixed* tree (`data/fixed.tf` with your fixes applied and the logging-bucket
     finding *suppressed with rationale*).

8. [ ] **Prove the gate flips.** Wrap the gate's exact command in `ci-gate.sh` and run it against both
   files, checking the **exit code** (`echo $?`) — non-zero on `data/misconfig.tf`, zero on
   `data/fixed.tf`. A gate that doesn't change its exit code between bad and good isn't a gate; it's a
   report. This is the whole module in one assertion.

## Success criteria — you're done when
- [ ] Both scanners ran; your finding matrix covers every misconfigured resource with a CIS mapping
  *and* a `fix`/`decide` verdict per row.
- [ ] All HIGH/CRITICAL findings are fixed and verified FAILED → PASSED in `data/fixed.tf`.
- [ ] The logging-bucket finding is suppressed with an inline `#checkov:skip=` rationale **and** you
  proved the public-ACL / open-SSH / wildcard-IAM findings still fire — you over-ruled the junior on one
  decision without muting the others.
- [ ] You can name at least two things the scanner structurally could *not* decide (the
  intended-vs-catastrophic open port; the wildcard IAM that composes into admin via the instance profile).
- [ ] `ci-gate.sh` exits **non-zero on `data/misconfig.tf` and zero on `data/fixed.tf`** — demonstrated
  with `$?`.

## Deliverables
Commit to your portfolio repo:
- `findings.md` — the consolidated cross-tool finding matrix with the `fix`/`decide` verdict column, each
  finding's risk, and its fix (or suppression justification).
- `iac-scan.yml` — the CI gate (validate with `actionlint` or GitHub's workflow validator); action pinned
  to a commit SHA.
- `gate-proof.md` — two terminal captures (exit code on the original vs. the fixed tree) proving the gate
  flips, plus the one-line justification for the logging-bucket suppression.

Do **not** commit: scanner JSON output, any `*.tfstate`, or `data/misconfig.tf` itself (it's seeded in
the lab repo, not yours).

## Automate & own it
**Required — this is the judgment-as-code core of the module.** Your finding is "these patterns must
never re-enter the pipeline, and this intended exception must stay allowed." Encode that verdict as a
**guardrail that fails the bad state and passes the fix.** Your `iac-scan.yml` *is* that guardrail —
harden it into something portable: `gate.sh`, a single script that

1. runs checkov (and optionally tfsec) over a directory or file passed as `$1`,
2. **exits non-zero iff** there is any MEDIUM-or-higher finding that is *not* a documented inline
   suppression — so an undocumented blanket-skip can't sneak a real exposure past the gate,
3. prints which finding IDs blocked it.

Then write the proof harness: run `gate.sh data/misconfig.tf` (→ exit 1) and `gate.sh data/fixed.tf`
(→ exit 0), and assert the flip. **Have a model draft the exit-code logic and any jq filters; review
every line** — confirm a *scanner error* doesn't read as a *clean pass* (a non-zero from a crash is not
the same signal as a non-zero from a finding), and that the gate fails the original for the *right*
finding, not an unrelated nit. This gate is the template the CI/CD pipeline in module 05 reuses; it is
your verdict, made un-recurrable.

## AI acceleration
Ask a model to review `data/misconfig.tf` before running the scanners; compare its findings to checkov's
output — which did it miss, which did it correctly identify? That comparison tells you when to trust AI
code review for IaC and when the scanner is still the more reliable gate. Then adversarially test your
own gate: ask the model to write a Terraform block that re-introduces a public exposure *while passing
your gate*. If it can, your gate (or your suppression policy) is too loose — tighten and re-prove the
flip. Where AI earns the most scrutiny: **IAM remediation** (wildcard "fixes" that move the `*` from
`Action` to `Resource`, still broken) and **suppressions** (the model will silence a *real* exposure as
readily as a false-positive).

## Connects forward
This gate is the keystone of the track's build half. **Module 05** wraps it into a fully hardened CI/CD
pipeline (pinned actions, least-privilege OIDC tokens, secret-scan + SBOM gates). **Module 10** runs this
same workflow on *AI-generated* Terraform — identical gate, but the source of the misconfigs is the model
rather than a human developer. The Phase 1 project ships reproducible infra gated by this scanner.

## Marketable proof
> "I gate Terraform deployments with checkov and tfsec in CI — I triaged findings into known-bad patterns
> versus context-dependent decisions, correctly suppressed a true false-positive with a documented
> rationale *without* muting the real exposures next to it, and shipped the CI gate that fails the merge
> on the original config and passes only the fix — proven by exit code. I can explain what a static
> scanner structurally cannot catch (the intended-vs-catastrophic open port, the secret in a variable,
> IAM that composes into admin) and why the gate needs a human verdict wrapped around it."

## Stretch
- Write a **custom Checkov check** (Python or YAML) that encodes a specific verdict no built-in rule
  covers — e.g. *every* `aws_s3_bucket` must carry an `Environment` tag — and add it to the gate. This is
  judgment-as-code at its purest: your org's rule, mechanically enforced.
- Add a `pre-commit` hook (the `checkov` pre-commit) so misconfigs fail *before* push, and a secret-scan
  (`gitleaks`/`trufflehog`) hook that would catch a hardcoded credential the config scanner misses —
  closing the gap between what a config rule and a secret rule each cover.
