# Module 05 — CI/CD Pipelines & Gates

*Type 7 · Build-&-Operate (secondary: Gate) — build a running pipeline gate, then operate it. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *the security check that runs before the merge is the one that can't be bypassed — but the pipeline that runs it is itself a target.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Infrastructure as Code](../02-infrastructure-as-code/README.md), [IaC Security Scanning](../03-iac-security-scanning/README.md)
{ .module-meta }

## Why this matters
Every security tool in this track — `checkov`, `gitleaks`, `sigma-cli` — is only as good as the
thing that runs it consistently. Run them by hand and they run inconsistently; the misconfiguration
that ships is always "the one we forgot to check." A CI/CD pipeline turns those tools into **gates**:
checks wired between commit and deploy that a bad change *cannot get past*. That is the build this
module is about — a secret-scan + IaC-scan + SBOM pipeline that you stand up, run, and watch **block
a merge**.

But there is a second, harder lesson, and it is the one that turns a build module into a security
module: **the pipeline is itself a high-value target.** Your CI runner holds the keys to everything —
cloud credentials, deploy keys, signing material — and it runs other people's code (third-party
actions, a contributor's PR) on every push. Get the gate's own configuration wrong and you haven't
just failed to catch a bad change; you've built the exfiltration channel for every secret in the
build. The whole point of operating this pipeline is to build one that *can't* become that channel.

## The case (short)
In **2021, Codecov's Bash Uploader was silently tampered with.** Codecov ships a script that
thousands of CI pipelines `curl | bash` to upload coverage reports. An attacker extracted a
credential from a public Docker image, used it to modify that script in Codecov's bucket, and added
**two lines that `curl`'d the runner's environment variables to an external IP.** Every pipeline that
fetched the latest script — for over two months — handed over whatever was in its environment: AWS
IAM keys, deploy keys, API tokens, service-account credentials. It went undetected from late January
until April, when **a customer noticed the SHA-256 of the downloaded script didn't match the one
published on GitHub.** A pinned hash would have caught it on day one.
[Codecov — April 2021 post-mortem / root cause analysis](https://about.codecov.io/apr-2021-post-mortem/) ·
[Rapid7 — analysis of the Codecov supply-chain compromise](https://www.rapid7.com/blog/post/2021/04/16/codecov-discloses-supply-chain-compromise/)

That is the cautionary backdrop for everything you build here. (The 2020 **SolarWinds** Orion
compromise is the same lesson at nation-state scale: malicious code injected into the *build
pipeline* shipped, signed and trusted, to 18,000 customers — the build system itself was the
breach.) A CI gate that runs an *unpinned* third-party action is doing exactly what Codecov's victims
did: trusting a moving target with the keys to the build. So the pipeline you operate in the lab is
built to assume its own dependencies might be hostile.

## The core idea
A pipeline gate is a graph of jobs wired to repo events. The build is two decisions stacked: **what
runs** (the gates) and **what the gate-runner is allowed to do** (its trust boundary). Get the first
and you catch bad changes; get the second and the gate can't be turned into Codecov.

**The gates, commit → deploy.** Three checks, each fail-closed: a **secret scan** (`gitleaks`) so a
hardcoded credential never reaches the remote; an **IaC scan** (`checkov`) so an unencrypted bucket
or `0.0.0.0/0` rule can't merge; and an **SBOM** step (`syft`) that produces a software bill of
materials so you know what's actually in the artifact you ship. Each runs on `pull_request`, exits
non-zero on a finding, and is a **required status check** — that "required" setting is what makes it
a gate rather than a suggestion. A green pipeline is the proof; a red one that *blocks the merge* is
the deliverable.

**The trust boundary is the whole security model.** GitHub Actions runs your YAML on a runner that
holds the repo's secrets, and the security model has two axes you control:

- **The event trigger decides whose code runs with whose privileges.** `pull_request` runs the PR's
  code with a *read-only*, fork-isolated token and no access to secrets — correct for scanning
  untrusted contributions. `pull_request_target` runs in the *base* branch's context, so it has the
  repo's secrets and a writable `GITHUB_TOKEN` — and if it then checks out and executes the PR's
  code, **any forked PR can read every secret.** That is precisely the Codecov shape, self-inflicted.
  `pull_request_target` has legitimate uses (a bot posting a comment with write access), but it must
  **never execute untrusted PR code.**
- **`permissions:` is least privilege for the token.** Set it at the job level to the minimum:
  `contents: read` for a scan, `pull-requests: write` only on the job that comments,
  `security-events: write` only on the job that uploads SARIF. `permissions: write-all` is a red
  flag — it hands every job a token that can rewrite the repo.

**No long-lived secrets, and pin everything you don't control.** Two hardening moves carry most of
the supply-chain risk, and they're the same ones this repo applied to its own workflows (T23):
**pin every third-party action to a full commit SHA** (`uses: actions/checkout@<40-hex>  # v4.2.2`),
not a mutable `@v4` tag a maintainer can re-point at new code — this is the literal control that
would have caught Codecov; and **authenticate to the cloud with short-lived OIDC tokens**, not a
long-lived `AWS_ACCESS_KEY_ID` sitting in repo secrets. A secret you don't store can't be
exfiltrated; an action you've pinned can't change under you. Operating the pipeline means watching
both of these hold.

## Learn (~2 hrs)

**GitHub Actions security model (~1 hr)**
- [GitHub Actions — security hardening for GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use) (~40 min) — the canonical reference. Read "Understanding the risk of script injections", "Using third-party actions" (the SHA-pinning rationale), and the `pull_request_target` warning in full; these three sections *are* the trust boundary.
- [GitHub Actions — using OpenID Connect to authenticate to cloud providers](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws) (~20 min) — why no long-lived cloud keys live in your repo; how a job mints a short-lived role-scoped token per run. Read the "Requesting the access token" and trust-policy parts.

**The supply-chain anchor (~30 min)**
- [Codecov — April 2021 post-mortem](https://about.codecov.io/apr-2021-post-mortem/) (~15 min) — read the primary source, not the journalism: how a leaked credential let two lines into a trusted script, and that a customer's **SHA mismatch** is what blew it open. This is the case for pinning.
- [Rapid7 — analysis of the Codecov supply-chain compromise](https://www.rapid7.com/blog/post/2021/04/16/codecov-discloses-supply-chain-compromise/) (~15 min) — a downstream victim's writeup: what was exfiltrated from CI environments and the blast radius. Grounds *why* the runner's environment is the crown jewels.

**The gate tools (~30 min)**
- [gitleaks — README through "Usage"](https://github.com/gitleaks/gitleaks) (~15 min) — the secrets-in-code gate; understand `detect` (CI scan) vs `protect` (pre-commit), and that it exits non-zero on a finding (that exit code *is* the gate).
- [Anchore syft — generate an SBOM](https://github.com/anchore/syft#quickstart) (~15 min) — produce a CycloneDX/SPDX bill of materials from an image or dir; the "what's actually in my artifact" step every supply-chain program now requires.

## Key concepts
- A **gate** is a check wired to a repo event that *blocks the merge* on a finding — "required status check" is the setting that makes it binding, not advisory
- The **event trigger** sets the trust boundary: `pull_request` (read-only, no secrets, fork-isolated) vs `pull_request_target` (base context, secrets, writable token) — never run untrusted PR code under the latter
- **`permissions:` at job level**, minimum required; `write-all` is a red flag
- **Pin third-party actions to a full commit SHA**, not a `@v4` tag — the exact control that would have caught Codecov 2021 (the script's hash changed under everyone)
- **OIDC over long-lived secrets**: mint a short-lived cloud token per run; a secret you don't store can't be exfiltrated
- **Secret injection**: never `echo` a secret; pass it via `env:` to the command, never as a CLI argument
- The pipeline runs three fail-closed gates (secret-scan + IaC-scan + SBOM) and is itself hardened against being the next supply-chain channel

## AI acceleration
A model writes a functional GitHub Actions workflow in seconds — and that's exactly where this
module's holes ride in looking innocent: a `pull_request_target` where `pull_request` would do,
no `permissions:` block, every action on a mutable `@v4` tag, a long-lived `AWS_ACCESS_KEY_ID` in
secrets instead of OIDC. Have a model draft your gate pipeline, then **review every line against the
trust boundary above**: which trigger, what the token can do, is each `uses:` pinned to a SHA, where
do the cloud credentials come from. Then make it *prove* the gate works — the operating test, not the
vibe — by feeding it the bad change and confirming the build goes red. AI drafts → you review every
line → you own the pipeline that has the keys to your infrastructure.
