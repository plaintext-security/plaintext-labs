# Lab 11 — Secrets Handling in Pipelines: OIDC & Short-Lived Credentials

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[LocalStack](https://localstack.cloud/) to simulate AWS **STS + IAM** locally — no cloud account or
real credentials required. A "runner" container plays the role of a CI job; it mints a short-lived,
signed OIDC-style JWT and exchanges it at STS for temporary credentials.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/11-pipeline-secrets
make up         # start LocalStack, register the IAM OIDC provider + a scoped deploy role
make bad        # the BEFORE: deploy with a stored long-lived key (the leak surface)
make oidc       # the AFTER: federate via AssumeRoleWithWebIdentity for short-lived creds
make check      # PROVE it: no static secret, credential short-lived + trust policy scoped
make demo       # the full before -> after -> proof walkthrough
make shell      # drop into the runner to work by hand
make down       # stop when done
```

`make up` registers an IAM OIDC identity provider for the lab's local issuer and creates
`MeridianDeployRole`, whose **trust policy** (`data/trust-policy.json`) is scoped to exactly one
subject (`repo:meridian/api:ref:refs/heads/main`) and audience (`sts.amazonaws.com`). The runner
container ships `awslocal` (a drop-in for `aws` pointed at LocalStack), `python3`, and the
`mint_oidc_token.py` / `check_no_static_secret.py` tooling.

> Everything runs locally against a simulated AWS environment you own. No real cloud credentials.
>
> **First run note / pending validation:** this environment is **new and has not yet been validated
> with `make up`/`make demo` on a Linux Docker host** (it was authored in a session without Docker).
> The moving parts most likely to need a tweak on first run are: (1) LocalStack community is
> **lenient** about OIDC — it returns correctly-shaped temporary credentials from
> `AssumeRoleWithWebIdentity` but does **not** strictly fetch the JWKS and cryptographically verify
> the JWT signature, nor strictly enforce the trust-policy `sub`/`aud` conditions, the way real AWS
> STS does. So the lab teaches the *real-world* pattern (a signed JWT, a JWKS, a scoped trust policy)
> while the lab's **proof** asserts what LocalStack faithfully reproduces: **no stored static key**, a
> returned **SessionToken + future Expiration** (short-lived), and a **statically-analysable scoped
> trust policy**. (2) The IAM `create-open-id-connect-provider` thumbprint is a placeholder — fine
> against LocalStack; real AWS validates it. If `make demo` snags, those two are where to look —
> see `data/setup.sh` and `data/pipeline-oidc.sh`.

## Scenario

Meridian Financial's `api` repo deploys to AWS from GitHub Actions. The deploy job authenticates with
a long-lived IAM access key stored as a repo secret — and last quarter a near-identical key leaked
through a verbose CI log at a peer company and was abused for three weeks before anyone rotated it.
Security's mandate: **no long-lived cloud credential may be stored in CI.** Your job is to refactor
the deploy pipeline from the stored static key to **OIDC federation** — the runner mints a per-run
identity token and trades it at AWS STS for a short-lived credential — and then to **prove** the
static secret is gone and the minted credential is genuinely short-lived and scoped to this pipeline.

## Do

### Part 1: See the leak surface (the BEFORE)
1. [ ] **Run the static-key pipeline.** `make bad`. Read `data/pipeline-bad.sh`: the runner is handed
   a long-lived `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — two strings that *are* a standing IAM
   principal with no expiry. Note what the credential lacks: there is **no session token and no
   expiration**. Where would this key have to live in a real pipeline, and which of this track's
   earlier tools (Module 05, Module 06) exist specifically to catch it leaking?

### Part 2: Build the OIDC pipeline (the AFTER)
2. [ ] **Read what `make up` trusted.** Inspect the registered identity provider and role:
   `make shell`, then `awslocal iam list-open-id-connect-providers` and
   `awslocal iam get-role --role-name MeridianDeployRole`. The role's trust policy
   (`data/trust-policy.json`) is the security control — find the `aud` and `sub` conditions and say,
   in one sentence, *which exact workflow* is allowed to assume this role.

3. [ ] **Mint a token and federate.** `make oidc` (or run `data/pipeline-oidc.sh` from the shell).
   Watch the three steps: a short-lived RS256 JWT is minted describing this run (`iss`/`aud`/`sub`),
   it's handed to `aws sts assume-role-with-web-identity`, and STS returns **temporary credentials**.
   Confirm the response carries a `SessionToken` and an `Expiration`. The runner started with **no**
   stored AWS key — where did the credential it deploys with come from, and when does it stop working?

4. [ ] **Refactor the real workflow.** Compare `data/deploy-static-key.yml` (the before) with
   `data/deploy-oidc.yml` (the after). Note the three changes that *are* the refactor:
   `permissions: id-token: write`, `role-to-assume:` instead of `aws-access-key-id`/
   `aws-secret-access-key`, and the role's trust policy doing the scoping. This is the exact
   GitHub→AWS pattern from the Learn path; the local lab is its mechanics made legible.

### Part 3: Prove it
5. [ ] **Run the proof.** `make check`. All assertions must PASS:
   - **no stored static key** — the OIDC pipeline carries no `AKIA…` key id or
     `aws-secret-access-key` input, and the workflow federates (`role-to-assume` + `id-token: write`);
   - **short-lived credential** — the credential minted in step 3 has a `SessionToken` and an
     `Expiration` in the future;
   - **scoped trust policy** — `aud = sts.amazonaws.com` and `sub` pinned to the exact repo/ref
     (`StringEquals`, no wildcard).

6. [ ] **Prove the deny / the wildcard mistake.** `make check-loose` runs the *same* checker against
   `data/trust-policy-loose.json`, whose `sub` is `repo:meridian/*:*`. Watch assertion 3 **FAIL**:
   that wildcard would let any fork or branch of the org assume the production deploy role — the OIDC
   equivalent of a wildcard IAM grant, and a documented real-world misconfiguration. In your
   write-up, explain why a passing `make oidc` with this loose policy is *worse* than the static key
   you removed, and what the correct `sub` admits.

## Success criteria — you're done when
- [ ] `make oidc` completes an `AssumeRoleWithWebIdentity` and the minted credential carries a
  `SessionToken` and a future `Expiration`.
- [ ] `make check` exits 0 — no stored static key in the OIDC pipeline, the credential is short-lived,
  and the trust policy is scoped to the exact repo/ref.
- [ ] `make check-loose` shows the scoped-trust assertion **FAIL** on the wildcard `sub` — you can
  explain why that is the wildcard-IAM failure mode for OIDC.
- [ ] `findings.md` records the before/after, the short-lived-credential proof, and the
  loose-vs-scoped `sub` reasoning.

## Deliverables
`findings.md` — the pipeline-secrets write-up: the static-key leak surface, the OIDC refactor (the
three workflow changes), the short-lived-credential proof (`SessionToken` + `Expiration`), and the
scoped-vs-wildcard `sub` analysis. `deploy-oidc.yml` — your refactored workflow (or a copy of the
reference) that federates with no stored key. Commit both. **Never commit** the OIDC signing key
(`data/oidc/private.pem`), the minted token, `role-arn.txt`, or any credential JSON — they're in
`.gitignore`.

## Automate & own it
**Required.** Write `verify_pipeline.py` (or extend `check_no_static_secret.py`) that a CI job can run
as a **gate**: given a workflow file and (optionally) a minted-credentials file, it exits non-zero if
the workflow stores a long-lived key, if the assumed credential lacks a `SessionToken`/`Expiration`,
or if the role trust policy's `sub` contains a wildcard. Have a model draft the JWT-decode and the
trust-policy walk; **you verify** the wildcard-`sub` case is actually caught (run it against
`trust-policy-loose.json` and confirm it fails) — a gate that passes a `repo:org/*:*` policy is worse
than no gate. Commit it as the reusable "no static secret in CI" check you'd drop into any repo.

## AI acceleration
A model writes the `configure-aws-credentials` OIDC workflow, the
`aws iam create-open-id-connect-provider` call, and the `assume-role-with-web-identity` invocation
fluently. Where you own the judgment is **the trust policy's `sub` condition** — ask for a GitHub→AWS
trust policy and it will happily emit a `StringLike` on `repo:org/*:*`, broad enough to "just work"
and broad enough to let any fork mint your production credential. Review every condition against
"could a workflow I didn't intend satisfy this `sub`?", pin it to the exact ref (or a protected
environment), and prove it with `make check` / `make check-loose` before trusting it.

## Connects forward
This is the build-side mirror of the leak-*detection* the track already teaches — `gitleaks`
(Module 05) and `trufflehog` (Module 06) hunt the stored key; here you remove the key so there is
nothing to hunt. The short-lived-token-per-request principle is the same one as user OIDC in the
**ZTNA** track and the workload SVIDs in **Workload Identity & mTLS** — verifiable identity, no
standing secret, automatic expiry — applied to the pipeline. In the track **capstone**, the rubric's
"secrets handled out of band" line is exactly this: the pipeline that deploys without a stored
credential.

## Marketable proof
> "I refactor CI pipelines from stored long-lived cloud keys to OIDC federation — the runner mints a
> per-run identity token and trades it at STS for short-lived, scoped credentials — and I prove the
> static secret is gone, the credential expires on its own, and the role's trust policy admits only
> the intended repo and branch, not any fork."

## Stretch
- **Tighten to a protected environment.** Change the trust policy `sub` to a GitHub *environment*
  form (`repo:meridian/api:environment:production`) and explain how requiring a protected environment
  (with required reviewers) adds a human gate on top of the cryptographic scoping.
- **Add a deploy gate.** Wire `verify_pipeline.py` into `data/deploy-oidc.yml` as a job step that
  fails the build if a static key reappears or the trust policy goes wildcard — the OIDC analogue of
  the secret-scanning gate from Module 05.
- **Compare providers.** Sketch the GitLab CI (`CI_JOB_JWT_V2` / `id_tokens`) and Buildkite OIDC
  equivalents — same `AssumeRoleWithWebIdentity` flow, different issuer and `sub` claim shape — and
  note what changes in the trust policy for each.
