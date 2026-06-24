# Module 06 — Infrastructure-as-Code Security

*Variant D · build-first, judgment-as-code ("encode your verdict as a gate"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *the misconfig that becomes a breach ships first as a line of Terraform. Catch it in the diff, then make the catch permanent.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 01 — Shared Responsibility](../01-cloud-fundamentals/README.md) · [Module 05 — Posture Auditing](../05-posture-auditing/README.md)
{ .module-meta }


## Where the breaches actually start

You spent module 01 ruling on Capital One and module 05 finding live misconfigurations in a running
account. Here is the uncomfortable through-line: **the unencrypted bucket, the `0.0.0.0/0` security
group, the `*` IAM policy, the public RDS** — the exact configurations behind the 2017 wave of public-S3
leaks (Accenture, Verizon/Nice, Booz Allen) and the over-broad role that fed Capital One — almost never
start life in a console. They start as a line of Terraform, get reviewed by someone reading *logic* not
*posture*, and ship. By the time module 05's scanner finds them, they have been live for months.

This module moves the catch left, to the diff. The same property that makes infrastructure-as-code
auditable makes it **scannable before a single resource exists**: a static analyzer parses the HCL,
builds the resource graph, and matches it against a rule library — `checkov`'s `CKV_AWS_*` checks,
`tfsec`/`trivy`'s built-ins — each mapped back to a CIS control. A misconfiguration that takes days to
find in production takes milliseconds to flag in a pull request, and costs nothing to fix before
`terraform apply`. That is shift-left in the most literal sense.

But the scan is not the lesson. **The lesson is what you do with the verdict.** A finding you fix by hand
regresses the next time someone copies the module. The whole point of this track — render judgment, then
make it un-recurrable — lands hardest here, because IaC is the one place where your verdict can become a
*mechanical gate that blocks the merge*. That gate is the deliverable.

## The mental model: a scanner is a fast junior reviewer with no context

Hold this picture, because the rest of the module is its consequences. **A scanner is a brilliant,
tireless junior reviewer who has memorized every known-bad pattern and understands none of your
intentions.** It will catch `encrypted = false` and `cidr_blocks = ["0.0.0.0/0"]` every time, instantly,
across ten thousand files. It will *never* tell you that the open security group on port 443 is the one
your public load balancer actually needs, or that the open one on 5432 is a database you just exposed to
the internet — because both are the same pattern, and the difference is a *decision* the scanner can't
see. It cannot read intent, business context, or the blast radius two resources away.

So the scanner splits the world cleanly into two halves, and your job is different in each:

- **The known-bad pattern** — unencrypted storage, wildcard IAM, public ingress on a sensitive port,
  logging disabled. Here the scanner is right and you just fix it. The skill is throughput, not judgment.
- **The bad *decision* the scanner misses** — an open SG that is genuinely intended (a true
  false-positive you must *suppress correctly*, with a rationale, not silence), versus an open SG that is
  a real exposure; a hardcoded secret sitting in a variable default; an IAM policy that's technically
  valid HCL but composes into privilege escalation. Logic and context live here, and **this is where you
  add value the tool can't.**

The discipline that ties it together is the **suppression**. Every tool lets you silence a finding with
an inline comment (`# checkov:skip=CKV_AWS_260: <reason>`). Suppressing a *true* false-positive — the
intended public-HTTPS rule — is a legitimate, senior move; it is you over-ruling the junior with a
documented reason. Suppressing by check-ID across the whole codebase, or with no rationale, is how the
junior gets ignored entirely and the bad decision ships anyway. **A suppression is an audit trail, not a
mute button.** Getting that distinction right is the judgment skill this module grades.

## Predict it before you scan (one prompt — then build)

This module is build-first; there's only one thing worth calling in advance, and it's the thing that
makes the mental model concrete. Open the lab's `data/terraform/` and, before running anything:

> **Look at `main.tf`, `s3.tf`, `sg.tf`, `iam.tf`, and `rds.tf`. Which lines will a scanner FAIL — and
> which genuinely dangerous lines will it MISS?** Write two lists.

Most people get the first list roughly right (it's the visibly-wrong patterns). The second list is the
teaching event: the scanner will likely *miss* the `password = "changeme-before-deploy"` literal in
`rds.tf` (a secret in plain HCL is a different tool's job — `gitleaks`/`trufflehog`, module 07), it has no
way to know the port-443 `0.0.0.0/0` is *intended* while the port-5432 one is a catastrophe, and it
flags the `iam:PassRole` wildcard as a pattern without understanding it *composes into admin* (module
02's lesson). If your "miss" list is shorter than your "fail" list, you've just felt why the gate needs a
human verdict wrapped around it.

## Learn (~4 hrs)

*Build-first and tool-heavy: read enough to triage findings and write a real gate, then go to the lab.*

**The scanners and their rule libraries (~1.5 hrs)**
- [Checkov — docs: "What is Checkov" + "Run Checkov"](https://www.checkov.io/1.Welcome/What%20is%20Checkov.html) (~30 min) — the overview, the `CKV_AWS_*` check-ID format, and output modes. The built-in library in [`checkov/checkov/terraform/checks/resource/aws/`](https://github.com/bridgecrewio/checkov/tree/main/checkov/terraform/checks/resource/aws) is the fastest way to see *exactly what field a check tests* — read two of them (e.g. the S3 encryption and the security-group checks) so a finding stops being a black box.
- [tfsec — getting started + AWS checks](https://aquasecurity.github.io/tfsec/latest/) (~30 min) — Terraform-specific depth and very readable output; browse the AWS check list and notice the overlap (and gaps) versus Checkov.
- [Trivy — misconfiguration scanning](https://aquasecurity.github.io/trivy/latest/docs/scanner/misconfiguration/) (~30 min) — `trivy config` over Terraform/CloudFormation/Helm/K8s: one scanner that also covers the images from module 10. Note where its findings differ from the other two.

**Writing the gate — the actual deliverable (~1.5 hrs)**
- [Checkov — CLI command reference (exit codes, `--soft-fail-on`, `--check`/`--skip-check`)](https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html) (~30 min) — read precisely how Checkov sets its **exit code** and how `--soft-fail-on` / `--hard-fail-on` choose which severities block. The gate lives or dies on this.
- [`bridgecrewio/checkov-action` (the GitHub Action)](https://github.com/bridgecrewio/checkov-action) (~20 min) — the canonical CI integration; read how `soft_fail_on` and SARIF upload wire into a PR check.
- [Checkov — suppressing and skipping checks (inline `checkov:skip`)](https://www.checkov.io/2.Basics/Suppressing%20and%20Skipping%20Policies.html) (~20 min) — the *correct* way to record a true false-positive, with a rationale. This is the judgment move, documented.
- [Writing a custom Checkov check (Python / YAML)](https://www.checkov.io/3.Custom%20Policies/Python%20Custom%20Policies.html) (~20 min) — skim, for the stretch: when no built-in rule encodes *your* org's verdict, you write the rule.

**Why the patterns matter (~1 hr)**
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services) (~30 min, skim) — the controls each `CKV_AWS_*` maps to (2.1.1 S3 encryption, 5.2/5.3 SG ingress). The gate enforces these; cite them in findings.
- [MITRE ATT&CK — T1562 Impair Defenses](https://attack.mitre.org/techniques/T1562/) (~15 min) — many IaC misconfigs (logging off, SG wide open) enable this family; the framing for *why* a blocked merge prevents an attack, not just a lint warning.

> **A concrete IaC supply-chain risk, not just config drift:** a vulnerability in a *Terraform provider
> or shared module* poisons every config that uses it — pinning module/provider versions and scanning
> the modules you pull is part of IaC security, not separate from it. A concrete example:
> [CVE-2025-13357](https://nvd.nist.gov/vuln/detail/CVE-2025-13357) (CVSS 9.8) — the HashiCorp Vault
> Terraform provider (v4.2.0 to before v5.5.0) defaulted `deny_null_bind` to `false` for the LDAP auth
> method, so every config using that provider silently allowed anonymous-bind authentication bypass until
> upgraded to v5.5.0. Track a CVE like this via [NVD](https://nvd.nist.gov/) and note it in your findings.

## Key concepts
- A scanner is a fast junior reviewer with no context: it catches the known-bad *pattern* (`encrypted = false`, `0.0.0.0/0`, `*`) but never the bad *decision* (intended vs. catastrophic open port; a secret in a variable; permissions that compose into admin).
- Shift-left literally: block the misconfig in the PR diff, before `terraform apply`, not in a post-deploy audit months later.
- Checks map to CIS controls and ATT&CK techniques — traceability from a finding back to a published standard is what makes it a finding, not a lint nit.
- Suppression is an audit trail, not a mute button: silence a *true* false-positive inline, with a rationale and a check-ID — never blanket-skip across the codebase.
- The deliverable is the **gate**: the verdict encoded so it fails the bad state and passes the fix, and can't regress when someone copies the module.
- IaC has a supply chain too — pin and scan the providers/modules you pull.

## AI acceleration
AI is excellent at writing Terraform that *passes a scanner* — and just as good at writing Terraform that
looks correct but hides an IAM over-grant or an encryption miss. The reliable workflow: let the model
draft a resource block, run `checkov`/`tfsec` on it immediately, feed the findings back, iterate. The
model is your first-pass engineer; you are the reviewer. But the judgment the model can't do for you is
exactly the scanner's blind spot: it will happily "fix" a finding by moving a wildcard from `Action` to
`Resource` (still broken), suppress a *real* exposure as if it were a false-positive, or pass the gate
while leaving the secret in the variable. Make the model draft the gate and the suppressions; **you**
confirm each suppression has a real rationale, that the gate fails the *original* config for the *right*
reason, and that it passes only the genuinely-fixed one. AI authors, you review, you own the verdict.
