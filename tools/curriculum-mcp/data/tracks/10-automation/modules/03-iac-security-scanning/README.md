# Module 03 — IaC Security Scanning

*Variant D · build-first, judgment-as-code ("encode your verdict as a gate"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *the misconfiguration that becomes a breach ships first as a line of Terraform. Catch it in the diff, then make the catch permanent.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 02 — Infrastructure as Code](../02-infrastructure-as-code/README.md)
{ .module-meta }


## Why this matters
A misconfigured S3 bucket costs nothing to fix in a `.tf` file before it deploys. After it ships with
public read, gets discovered by a scanner, lands in a breach report, and has to be disclosed to
customers, it costs orders of magnitude more. The uncomfortable through-line behind the real incidents
makes the point: the unencrypted public bucket behind the **2017 wave of S3 leaks** (Accenture,
Verizon/Nice, Booz Allen, Dow Jones), and the over-broad IAM role the attacker rode in the **2019
Capital One** breach — these almost never start life in a console. They start as a line of Terraform,
get reviewed by someone reading *logic* not *posture*, and ship. By the time a posture scanner finds
them in production, they have been live for months.

This module moves the catch left, to the diff. The same property that makes infrastructure-as-code
auditable makes it **scannable before a single resource exists**: a static analyzer parses the HCL,
builds the resource graph, and matches it against a rule library — `checkov`'s `CKV_AWS_*` checks,
`tfsec`'s built-ins — each mapped back to a CIS control. A misconfiguration that takes days to find in
production takes milliseconds to flag in a pull request, and costs nothing to fix before `tofu apply`.

But the scan is not the lesson. **The lesson is what you do with the verdict.** A finding you fix by
hand regresses the next time someone copies the module. IaC is the one place where your verdict can
become a *mechanical gate that blocks the merge* — and that gate is the deliverable of this module.

## The core idea: a scanner is a fast junior reviewer with no context

Hold this picture, because the rest of the module is its consequences. **A scanner is a brilliant,
tireless junior reviewer who has memorized every known-bad pattern and understands none of your
intentions.** It will catch `encrypted = false`, `acl = "public-read"`, `cidr_blocks = ["0.0.0.0/0"]`,
and `Action = "*"` every time, instantly, across ten thousand files. It will *never* tell you that the
open security group on port 443 is the one your public load balancer actually needs, or that the open
one on 5432 is a database you just exposed to the internet — because both are the same pattern, and the
difference is a *decision* the scanner can't see. It pattern-matches; it cannot read intent, business
context, or the blast radius two resources away.

So the scanner splits the world cleanly into two halves, and your job is different in each:

- **The known-bad pattern** — unencrypted storage, public ACL, wildcard IAM, SSH open to the world,
  IMDSv2 not enforced. Here the scanner is right and you just fix it. The skill is throughput, not
  judgment.
- **The bad *decision* the scanner misses** — an open SG that is genuinely intended (a true
  false-positive you must *suppress correctly*, with a rationale, not silence) versus an open SG that is
  a real exposure; a hardcoded secret in a variable default; an IAM policy that's valid HCL but composes
  into privilege escalation. Logic and context live here, and **this is where you add value the tool
  can't.**

The discipline that ties it together is the **suppression**. Every tool lets you silence a finding with
an inline comment (`#checkov:skip=CKV_AWS_18: <reason>`). Suppressing a *true* false-positive — the
logging bucket that doesn't need to log to itself, the intended public-HTTPS rule — is a legitimate,
senior move: you over-ruling the junior with a documented reason. Suppressing by check-ID across the
whole codebase, or with no rationale, is how the junior gets ignored entirely and the bad decision ships
anyway. **A suppression is an audit trail, not a mute button.** Getting that distinction right is the
judgment this module is about.

`checkov` (Bridgecrew / Palo Alto Networks) and `tfsec` (Aqua Security) cover overlapping but not
identical rule sets — running both is common because each catches what the other misses. The choice
between them matters far less than the **habit of running one consistently in CI as a gate**: `checkov
-d . --soft-fail-on LOW` exits non-zero when a real finding remains, and a pipeline that fails on that
exit code means the misconfig never reaches `tofu apply`. The calibration skill is the rest of it — too
strict and every PR fails on noise, too loose and real misconfigs slip through. **Start strict, suppress
with justification, never start permissive and tighten later.** The gate is where you encode that
verdict so it can't regress.

## Learn (~2 hrs)

*Build-first and tool-heavy: read enough to triage findings and write a real gate, then go to the lab.*

**The scanners and their rule libraries (~1 hr)**
- [Checkov — Quick Start](https://www.checkov.io/1.Welcome/Quick%20Start.html) (~25 min) — run the quickstart against a local Terraform directory; understand `--check`, `--skip-check`, and the output format. The [Terraform check index](https://www.checkov.io/5.Policy%20Index/terraform.html) is the fastest way to see *exactly what field each `CKV_AWS_*` check tests* — look up `CKV_AWS_18` (S3 access logging) and `CKV_AWS_19`/`CKV_AWS_145` (S3 encryption) so a finding stops being a black box.
- [tfsec — Documentation (Getting Started + Configuration)](https://aquasecurity.github.io/tfsec/latest/) (~20 min) — Terraform-specific depth and very readable output; read the severity levels and inline-suppression syntax, and notice the overlap (and gaps) versus Checkov.
- [Checkov — Suppressing and Skipping checks (inline `checkov:skip`)](https://www.checkov.io/2.Basics/Suppressing%20and%20Skipping%20Policies.html) (~15 min) — the *correct* way to record a true false-positive, with a rationale. This is the judgment move, documented.

**Writing the gate — the actual deliverable (~45 min)**
- [Checkov — Hard and soft fail (exit codes, `--soft-fail-on`, `--hard-fail-on`)](https://www.checkov.io/2.Basics/Hard%20and%20soft%20fail.html) (~20 min) — read precisely how Checkov sets its **exit code** and how `--soft-fail-on` / `--hard-fail-on` choose which severities block. The gate lives or dies on this.
- [`bridgecrewio/checkov-action` (the GitHub Action)](https://github.com/bridgecrewio/checkov-action) (~15 min) — the canonical CI integration; read how `soft_fail` and SARIF upload (`output_format: cli,sarif` → `github/codeql-action/upload-sarif`) wire into a PR check, and pin the action to a commit SHA.
- [Writing a custom Checkov check (Python / YAML)](https://www.checkov.io/3.Custom%20Policies/Python%20Custom%20Policies.html) (~10 min) — skim, for the stretch: when no built-in rule encodes *your* org's verdict, you write the rule.

**Why the patterns matter (~15 min)**
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services) (~10 min, skim) — the controls each `CKV_AWS_*` maps to (S3 encryption, SG ingress, IMDSv2). The gate enforces these; cite them in findings.
- [MITRE ATT&CK — T1078.004 Valid Accounts: Cloud Accounts](https://attack.mitre.org/techniques/T1078/004/) (~5 min) — the over-broad IAM role and public ingress these scans catch are exactly what an attacker rides after initial access; the framing for *why* a blocked merge prevents an attack, not just a lint warning.

## Key concepts
- A scanner is a fast junior reviewer with no context: it catches the known-bad *pattern* (`encrypted = false`, `public-read`, `0.0.0.0/0`, `*`) but never the bad *decision* (intended vs. catastrophic open port; a secret in a variable; IAM that composes into admin).
- Shift-left literally: block the misconfig in the PR diff, before `tofu apply`, not in a post-deploy audit months later.
- `checkov` and `tfsec` overlap but differ — run both; the choice matters less than the habit of gating in CI.
- Suppression is an audit trail, not a mute button: silence a *true* false-positive inline with a rationale and a check-ID — never blanket-skip across the codebase.
- Calibrate strict-first: too strict floods PRs with noise, too loose lets real misconfigs through; start strict and suppress with justification.
- The deliverable is the **gate**: the verdict encoded so it fails the bad state and passes the fix, and can't regress when someone copies the module.

## AI acceleration
AI is excellent at writing Terraform that *passes a scanner* — and just as good at writing Terraform
that looks correct but hides an IAM over-grant or an encryption miss. The reliable loop: let the model
draft a resource block, run `checkov`/`tfsec` on it immediately, feed the findings back, iterate — the
model is your first-pass engineer; you are the reviewer. Doing this by hand also teaches you which
misconfigs AI consistently produces. But the judgment the model can't do for you is exactly the
scanner's blind spot: it will happily "fix" a finding by moving a wildcard from `Action` to `Resource`
(still broken), suppress a *real* exposure as if it were a false-positive, or pass the gate while
leaving a secret in a variable. Make the model draft the gate and the suppressions; **you** confirm each
suppression has a real rationale, that the gate fails the *original* config for the *right* reason, and
that it passes only the genuinely-fixed one. AI authors, you review, you own the verdict.
