# Module 11 — Secrets Handling in Pipelines (OIDC)

*Type 7 · Build-&-Operate — refactor a deploy pipeline from a stored long-lived key to OIDC federation, then prove no static secret remains and the minted credential is short-lived; the deliverable is the working federated pipeline and its verification, not an essay. (Secondary: Judgment-as-Code — the IAM trust policy whose `sub` scope is the real control.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *the most secure secret in a pipeline is the one that doesn't exist — mint a short-lived credential at deploy time instead of storing a key you'll spend the rest of the year hoping nobody leaks.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

This track has taught you to *hunt* leaked secrets thoroughly — `gitleaks` in Module 05, `trufflehog`
in Module 06, keeping credentials out of state files and git in Module 02. But every one of those is
damage control on a system that still *stores* a long-lived cloud key somewhere a pipeline can read it.
That stored key is the wound the scanners keep dressing: the AWS access key sitting in a CI secret, the
deploy credential pasted into a variable, the service-account JSON baked into a runner. It never rotates
on its own, it's copied into every fork and every log line that forgets to mask it, and the breach
write-ups are monotonous — the Codecov supply-chain compromise, the CircleCI January-2023 incident, the
endless "exposed CI token" disclosures all turn on *a credential that existed long enough to be stolen*.
The build-side fix is not "scan harder." It's to make the pipeline mint a **short-lived, federated
credential at runtime** so there is no static secret to leak in the first place. This is the single most
prevalent real-world CI security control the track hasn't had you build — and it's the mirror image of
all the leak-detection you already know.

## Objective

Refactor a deployment pipeline from a **stored long-lived cloud key** to **OIDC federation**: the runner
presents a signed, per-run identity token to AWS STS via `AssumeRoleWithWebIdentity` and receives
short-lived credentials scoped by an IAM **trust policy** to exactly this repo and branch. Then **prove
it**: confirm the pipeline holds *no* long-lived AWS key anywhere, and that the credentials it minted are
genuinely **short-lived** (a session token is present and an expiry is set) and **scoped** (the trust
policy admits only the intended subject/audience). The proof is the deliverable — anyone can claim "we use
OIDC"; you show the static key is gone and the minted credential expires.

## The core idea

Start with what a stored credential actually *is*: standing, ambient authority. A long-lived AWS access
key in a CI secret is a bearer token with no expiry and no context — whoever holds the two strings *is*
that IAM principal, from anywhere, until a human remembers to rotate it. That's the entire leak surface.
It has to be written down (in a secret store, an env var, a `.tfvars`), it gets copied wherever the
pipeline runs, and it survives every incident because nothing forces it to age out. Secret-scanning
exists *because* this pattern exists. The move that dissolves the problem is to stop storing the key and
instead **prove who you are at the moment you need access, and get a credential that's already expiring.**

**OIDC web-identity federation** is how a pipeline does that. The CI platform (GitHub Actions, GitLab,
Buildkite) runs its own OpenID Connect identity provider: at job time it mints a short-lived **JWT** that
*describes this specific run* — signed by the platform's private key, carrying claims like
`iss` (who issued it), `aud` (who it's for), and `sub` (the exact repo + branch + environment, e.g.
`repo:acme-corp/api:ref:refs/heads/main`). The job hands that JWT to **AWS STS** via
`AssumeRoleWithWebIdentity`. STS fetches the provider's public keys from its published JWKS endpoint,
**verifies the signature** (so the token can't be forged), checks the claims against the role's trust
policy, and — if it all matches — returns **temporary credentials**: an access key, a secret, *and a
session token, stamped with an expiry minutes to an hour out.* No secret was stored anywhere. The runner
arrived with nothing and left with a credential that's already on a timer.

The piece that carries the security is the **trust policy**, and this is where the judgment lives. Setting
up the IAM OIDC provider establishes *that* you trust GitHub's issuer; the trust policy on the role decides
*which workflows* may assume it, by asserting conditions on the JWT's claims — `aud` must equal
`sts.amazonaws.com`, and `sub` (via `StringEquals` or a carefully bounded `StringLike`) must match the
exact repo and ref. Get this wrong and you've rebuilt the very problem you were escaping: a trust policy
that matches `repo:acme-corp/*:*` lets *any* branch of *any* fork mint your production credential — the
OIDC equivalent of a wildcard IAM grant, and a documented real-world misconfiguration. A `sub` pinned to
`repo:acme-corp/api:ref:refs/heads/main` (or to a protected GitHub *environment*) admits only the pipeline
you meant. The trust policy is the scope, and a loose condition is worth no more than the static key you
removed.

Which reframes where the off-switch is. With a stored key, revocation means a human finding the secret in
every store and rotating it before the attacker uses it — a race you often lose. With OIDC, there is no
secret to find: you **edit the trust policy** (tighten the `sub`, remove the provider, narrow the role's
permissions) and the next run simply can't assume the role. The control plane moved from "protect and
rotate a secret" to "govern who is allowed to federate" — declarative, in one IAM document, with every
`AssumeRoleWithWebIdentity` call landing in CloudTrail as an audit trail the static key never produced.
The same short-lived-token-per-request principle is exactly what Module 02's user OIDC and the ZTNA track's
workload SVIDs do; here it's the pipeline that holds no standing secret.

## Learn (~3 hrs)

**The pattern: OIDC in CI (~1.5 hrs)**
- [GitHub — About security hardening with OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect) — the authoritative "why no long-lived secret" framing and how the runner mints a per-job token. Read "Overview of OpenID Connect" and the JWT-claims section (`sub`, `aud`, `iss`) — those claims are exactly what your trust policy scopes to.
- [GitHub — Configuring OpenID Connect in Amazon Web Services](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services) — the end-to-end GitHub→AWS recipe the lab mirrors: add the IAM OIDC provider, write the role's trust policy on `token.actions.githubusercontent.com`, and the `id-token: write` + `configure-aws-credentials` workflow. This is the build you're reproducing locally.

**The AWS side: AssumeRoleWithWebIdentity & the trust policy (~1 hr)**
- [AWS IAM — Create an OpenID Connect (OIDC) identity provider in IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html) — what an IAM OIDC provider is (issuer URL + audience + thumbprint) and how a role's trust policy then conditions on the token's claims. Read "Creating OIDC identity providers" and the trust-policy condition example — the `StringEquals` on `:sub` is the scoping control.
- [AWS STS — AssumeRoleWithWebIdentity (API reference)](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html) — the call itself: what you pass (`RoleArn`, `WebIdentityToken`) and what comes back. Read the **Response Elements** — `Credentials` carries `AccessKeyId`, `SecretAccessKey`, `SessionToken`, and `Expiration`. That `SessionToken` + `Expiration` is precisely what the lab's check asserts to prove the credential is short-lived.

**Why this is the standard, and the failure modes (~0.5 hr)**
- [aws-actions/configure-aws-credentials — README](https://github.com/aws-actions/configure-aws-credentials#oidc) — the action that does the federation in real pipelines; read the "OIDC" / "Assuming a role" section and the security note on **not** using long-lived keys. Reference for the *Automate & own it* build.
- [Datadog Security Labs — How attackers exploit GitHub Actions OIDC misconfigurations (the loose `sub`)](https://securitylabs.datadoghq.com/articles/exploiting-github-actions-cicd-pipelines/) — concrete write-up of the over-broad trust-policy condition that lets a fork or unintended branch assume the role; read for the exact `sub`-wildcard mistake your trust policy must avoid. *(If unreachable, the GitHub doc's "Configuring the subject in your cloud provider" section covers the same scoping mistake.)*

## Key concepts
- A stored long-lived key is standing, ambient authority — no expiry, copied everywhere; it *is* the leak surface that secret-scanning exists to manage.
- OIDC federation mints a per-run signed JWT (`iss`/`aud`/`sub`) that *describes the job*; STS verifies it against the provider's JWKS and returns short-lived credentials — no secret stored.
- `AssumeRoleWithWebIdentity` returns temporary creds with a **`SessionToken` and `Expiration`** — the proof a credential is short-lived, not standing.
- The **trust policy is the scope**: `aud = sts.amazonaws.com` and a `sub` pinned to the exact repo/ref (not `repo:org/*:*`). A loose `sub` is a wildcard grant — a real, exploited misconfiguration.
- The off-switch moved from "find and rotate the secret" to "edit the trust policy / remove the provider" — declarative, one document, audited in CloudTrail.
- Same principle as user OIDC (Module 02) and workload SVIDs (ZTNA) — short-lived, verifiable identity per request, no standing secret — applied to the pipeline.

## AI acceleration

A model writes the *plumbing* here fluently: the `configure-aws-credentials` workflow with
`permissions: id-token: write`, the `aws iam create-open-id-connect-provider` call, the
`AssumeRoleWithWebIdentity` request. Where you own the judgment is **the trust policy's `sub`
condition**, because that is the actual security control and the model has no way to know which repo and
branch *should* be allowed to federate. Ask it for a GitHub→AWS trust policy and it will happily emit a
`StringLike` on `repo:org/*:*` — broad enough to "just work," and broad enough to let any fork mint your
production credential. Review every condition against "could a workflow I didn't intend satisfy this
`sub`?", pin it to the exact ref or a protected environment, and **prove it the way the lab does**:
confirm no static key remains and that the minted credential carries a session token and a future expiry.
AI drafts the federation; you scope the trust and verify the secret is genuinely gone.
