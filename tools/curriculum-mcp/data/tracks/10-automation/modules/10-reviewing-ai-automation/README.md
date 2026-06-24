# Module 10 — Reviewing AI-Generated Automation

*Variant D · adversarial review ("AI authors → you review → you own it," made into the whole lab). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *the automation an AI writes is fluent, plausible, and structurally correct — and that is exactly what makes its dangerous lines hard to see.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 03 — IaC Security Scanning](../03-iac-security-scanning/README.md) · [Module 05 — CI/CD Pipelines & Gates](../05-cicd-pipelines/README.md)
{ .module-meta }


## Why this matters

The automation in this track is increasingly *drafted by a model*. You ask for "a Terraform config for a data
bucket and an instance with admin access," or "a GitHub Actions workflow that comments on pull requests," and you
get back well-formatted HCL or YAML in seconds. It parses. The resource types are real. The attribute names are
spelled correctly. It will very often `apply` or `run` on the first try. **And that fluency is the trap.** A
human junior who didn't understand IAM would write IAM that *looks* like they didn't understand it — hesitant,
incomplete, obviously rough. A model writes the over-permissive policy with the same confident polish it writes
the correct one. There is no tell in the *style*; the tell is only in the *semantics*.

The cost of missing it is not hypothetical. In March 2025, attackers compromised the popular
**`tj-actions/changed-files`** GitHub Action and retroactively re-pointed its version tags at a malicious commit
that dumped CI secrets into build logs — **over 23,000 repositories** were affected, tracked as
[CVE-2025-30066](https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066-and-reviewdogaction).
Every repo that referenced the action as `tj-actions/changed-files@v44` instead of a pinned commit SHA inherited
the malicious code automatically. An AI assistant asked to "add the changed-files action to my workflow" will
write `@v44` — because that is what every example online does. The model didn't make a mistake; it faithfully
reproduced the *common* pattern, and the common pattern is the vulnerable one.

This is the module the rest of the track was building toward. You have the scanners (`checkov`, `tfsec`,
`gitleaks`, `actionlint`) and the gate from modules 03 and 05. Now the source of the misconfigurations is the
model, not a human developer — and the differentiating skill is no longer *using the tool*, it's **knowing what
the tool can't catch, how you knew the line was dangerous, and when you're allowed to trust the output anyway.**

## The core idea: fluency is not correctness — review the semantics, not the syntax

Hold one picture for the whole module. **AI-generated automation fails along a single axis: it is structurally
sound and semantically dangerous.** The syntax is correct (so it parses, applies, runs, and passes a linter); the
*meaning* is wrong in ways that only show up if you know the security model behind the resource. This is the
opposite of a normal junior's mistakes, and it inverts how you review. You are not looking for things that *look*
broken — nothing will. You are auditing whether each line *means* what it should.

**Call it before you read on.** You are handed a 40-line GitHub Actions workflow from a model. It uses real
actions, the YAML is valid, `actionlint` passes clean. Roughly what fraction of AI-generated automation that
*passes its linter* still contains a security-relevant defect? *Write your guess down.* — The honest answer from
the secure-code-review literature is: a large fraction. Independent studies of LLM-generated code put the
vulnerable-output rate around **one in five to one in three samples** even from frontier models (the figures move,
but the order of magnitude is stable). A clean linter run tells you the code is *well-formed*. It tells you almost
nothing about whether it is *safe*. If your intuition was "the linter would have caught it," that intuition is the
exact failure this module exists to correct.

The defects cluster into a small, learnable set of **failure modes**, and each has a *tell* — the thing that tips
you off, which you then confirm against the primary source rather than trusting your gut:

- **Over-broad authorization.** `Action = "*"`, `Resource = "*"`, a `GITHUB_TOKEN` with `permissions: write-all`,
  a role assumable by `Principal = "*"`. *Tell:* a wildcard where a specific value belongs. *Verify against:* the
  IAM/least-privilege docs and the actual API actions the resource needs.
- **Untrusted-input execution.** A `pull_request_target` workflow that checks out and runs the PR's code, or a
  `run:` step that interpolates `${{ github.event.pull_request.title }}` straight into a shell — the
  ["pwn request"](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) and
  script-injection patterns. *Tell:* attacker-controlled data crossing into a privileged context. *Verify against:*
  GitHub's security-hardening guidance.
- **Mutable supply-chain references.** `actions/...@v4` or `@main` instead of a 40-character commit SHA — the
  `tj-actions` failure mode. *Tell:* a tag or branch where an immutable SHA belongs. *Verify against:* the action's
  release/commit history and the hardening docs.
- **Disabled or absent safety controls.** `encrypted = false`, no `metadata_options { http_tokens = "required" }`,
  `force_destroy = true`, a `terraform` plan that *deletes* a stateful resource on apply, `acl = "public-read"`.
  *Tell:* a security default turned off, or a destructive operation with no guard. *Verify against:* the resource's
  provider docs and `terraform plan` itself.
- **Confidently-wrong justification.** A comment or a suppression that *explains* an insecure choice plausibly but
  falsely — `# public-read is fine, the data isn't sensitive` or
  `#checkov:skip=CKV_AWS_18: logging not needed`. *Tell:* a rationale you can't independently confirm. *Verify
  against:* whether the claim is actually true for *this* system, not in general.

The meta-skill — and the reason this is a measurement type, not just a checklist type — is **calibrating trust
with a number, not a vibe.** "Review AI output carefully" is useless advice; everyone agrees and nobody operates
on it. A *policy* is operable: it states a measured threshold below which AI-drafted automation may merge with
light review, and above which it requires a full human re-derivation — and it states which classes of finding are
**never** auto-suppressible regardless of the score (wildcard IAM, untrusted-input execution, unpinned third-party
actions). You earn that threshold by reviewing a sample, counting the planted defects you caught versus missed,
and writing the number down. A trust policy without a measured basis is the same vibe in a nicer font.

And the same skepticism applies to the *suppression*, just as it did in module 03 — but turned on the model. An
AI-written `#checkov:skip` or a "this is safe because…" comment is not evidence; it is **another AI artifact to
review.** Suppressing a *true* false-positive with a rationale a human can defend is a senior move. Accepting the
model's own justification for its own insecure line is how the defect ships with a paper trail that makes it look
reviewed. **A suppression is an audit trail, not a mute button — and least of all when the model wrote it.**

## Learn (~2 hrs)

*Review-first: read enough to recognise the failure modes and verify a finding against its primary source, then go
to the lab. The whole point is to stop trusting fluent output, so weight the primary sources over the summaries.*

**AI code review patterns — the failure modes and how to instruct against them (~1 hr)**
- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) (~20 min) — read **LLM09 Overreliance** ("failing to critically assess LLM outputs can lead to compromised decision-making, security vulnerabilities, and legal liabilities") and **LLM02 Insecure Output Handling**. This is the named, authoritative framing for *why* reviewing the model's output is itself a security control — the exact stance this module operationalises.
- [OpenSSF — Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions.html) (~25 min) — the inverse move: what *security instructions* to give the assistant up front (least privilege, pin dependencies, validate inputs) so it drafts safer code. Read the supply-chain and platform sections; you'll fold the best lines into your trust policy as the "prompt-side" half of the control. Authored by the OpenSSF Best Practices + AI/ML working groups.
- [OWASP Code Review Guide — *Reviewing code for...* (skim the access-control, injection, and configuration sections)](https://owasp.org/www-project-code-review-guide/) (~15 min) — the discipline of structured secure code review predates AI; the categories (authorization, injection, misconfiguration) map one-to-one onto the AI failure modes above. Read it as the checklist *skeleton* you'll specialise for AI-generated automation.

**GitHub Actions: the supply-chain and untrusted-input failure modes (~45 min)**
- [GitHub Docs — Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions) (~25 min) — the primary source. Read **"Using third-party actions"** (pin to a full commit SHA — *the only way to use an action as an immutable release*), **"Mitigating the risks of untrusted code checkout"** (`pull_request_target`), and **"Good practices for mitigating script injection attacks."** These three sections are the verify-against reference for three of the lab's planted defects.
- [GitHub Security Lab — Keeping your GitHub Actions and workflows secure, Part 1: Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) (~20 min) — the canonical explainer for *why* `pull_request_target` + checking out the PR's code hands a stranger your secrets and write token. Read it once and the "pwn request" pattern is unmistakable forever — exactly the tell you want.

**The real disaster the patterns prevent (~15 min)**
- [CISA — Supply Chain Compromise of `tj-actions/changed-files` (CVE-2025-30066)](https://www.cisa.gov/news-events/alerts/2025/03/18/supply-chain-compromise-third-party-tj-actionschanged-files-cve-2025-30066-and-reviewdogaction) (~10 min) — the primary advisory for the 23,000-repo compromise: mutable tags re-pointed at a malicious commit that dumped CI secrets to logs. Pair with the [GitHub Advisory (GHSA-mrrh-fwg8-r2c3)](https://github.com/advisories/GHSA-mrrh-fwg8-r2c3) for the affected versions and the one-line mitigation: *pin to a commit SHA.* This is why "the model wrote `@v44`" is not a nit.

## Key concepts
- AI automation fails on one axis: **structurally sound, semantically dangerous** — it parses, applies, and lints clean while *meaning* the wrong thing. Review the semantics, not the syntax.
- A clean linter/scanner run proves *well-formed*, not *safe*; a large fraction of linter-passing AI code still carries a security defect (OWASP LLM09 Overreliance).
- The failure modes are a small, learnable set — over-broad authorization, untrusted-input execution, mutable supply-chain refs, disabled safety controls, confidently-wrong justification — **each with a tell you confirm against the primary source.**
- The tell tips you off; the *primary source* (provider docs, GitHub hardening guide, `terraform plan`) is what makes the finding defensible. Never close a finding on intuition alone.
- Trust must be **measured, not vibed**: a trust policy states a threshold (caught-vs-planted on a reviewed sample) and a list of finding classes that are *never* auto-suppressible.
- An AI-written suppression or "this is safe because…" comment is another AI artifact to review — not evidence. A suppression is an audit trail, not a mute button.

## AI acceleration
The honest move here is reflexive: **use a model to both generate the dangerous automation and to propose the
fixes — then review every line of both.** Generating it teaches you the model's house style of mistake; reviewing
its fixes teaches you the model's house style of *bad fix* (moving a wildcard from `Action` to `Resource` and
calling it least-privilege; "pinning" an action by adding a comment instead of a SHA; suppressing a real exposure
as confidently as a false-positive). For each proposed fix, demand the *why*: "what can an attacker do before this
change that they can't after?" A model that can answer in terms of a concrete attack path is more trustworthy than
one that just edits a value — and the gaps in its answer are your map of what to verify manually. Then close the
loop the OpenSSF guide describes: write the *security instructions* you'd prepend to the next generation so the
model drafts the safer version first. AI authors, you review, **you own the verdict and the policy** — that
ownership is the entire deliverable.
