# Module 07 — Secrets Management & Detection

*Module concept · [Go to the hands-on lab →](lab.md)*


**Cloud & Container Security** — *the credential you don't know is in git is the one that gets you breached.*

## Why this matters
Leaked credentials are the single most common initial access vector in cloud breaches. GitHub's own
telemetry scans billions of public commits and finds millions of secrets per year — AWS keys, API
tokens, database passwords — many of them live and not yet rotated. Knowing how to find them before
an attacker does, and how to manage secrets properly so they don't end up there in the first place,
is table-stakes cloud security.

## Objective
Use `trufflehog` to find a planted secret in a git repository's history, understand why it persists
after deletion, and operate HashiCorp Vault in dev mode to store, retrieve, and rotate a secret —
bridging detection and prevention.

## The core idea

There is a specific reason leaked credentials are so damaging in cloud environments: they are
*ambient*. An AWS access key sitting in a public GitHub commit requires no exploit, no
vulnerability research, no phishing. Anyone who finds it gets everything the attached role can do.
Tools like `triagehog` (GitHub's internal scanner) and Orca, Wiz, and Lacework at the CSPM layer
all search for this pattern because it is both catastrophically common and entirely preventable.

The first thing to internalise is what "removing" a secret from git actually does — and doesn't.
When a developer pushes a commit with a hardcoded API key, then panics, creates a new commit
removing it, the key is *still in the repository's history*. It is still visible to anyone who
clones the repo and runs `git log -p`. The only safe response to a leaked credential is to revoke
and rotate it immediately, not to remove the commit. `trufflehog` scans the full history, not just
the current HEAD — that is why it finds things that a developer "already fixed."

The architectural alternative to hardcoded secrets is a secrets manager: a service that stores
credentials at rest (encrypted), enforces access control on reads, and — crucially — supports
*dynamic credentials* that are minted per-request and expire automatically. HashiCorp Vault is the
open-source canonical implementation. In Vault's model, your application never holds a long-lived
database password; instead it calls the Vault API at startup and receives a database credential that
expires in 30 minutes. If that credential leaks, the blast radius is bounded by its TTL.

The AWS-native equivalent is AWS Secrets Manager and IAM roles for services (no static key at all
— the EC2/Lambda/ECS role assumption is the credential, and it rotates automatically). But Vault
spans every cloud and every secret type, and understanding it teaches the mental model that the
native services implement. The pattern is always the same: centralise, encrypt at rest, audit every
access, rotate aggressively, and eliminate long-lived static credentials wherever possible.

One more practitioner note on detection: `trufflehog` is fast and covers hundreds of credential
patterns out of the box (AWS, GCP, GitHub, Slack, Stripe, database URIs, and more). Running it in
pre-commit hooks and in CI is low-effort and high-value. The meaningful human judgment is the same
as in any security signal: is this a real credential or a placeholder? Is it still valid? Who
owns the affected service and needs to rotate immediately? The tool finds; you triage.

## Learn (~4 hrs)

**Secrets detection (~1.5 hrs)**
- [trufflehog — trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) — the README covers scan modes (git, filesystem, S3, GitHub org), the verification feature (checks if found creds are still live), and integration patterns. Read the full README and the pre-commit hook section.
- [GitLeaks — gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) — the other major secrets scanner, used in Module 08. Compare the approaches: trufflehog verifies live creds; gitleaks is faster and config-file-driven.
- [MITRE ATT&CK T1552.001 — Credentials In Files](https://attack.mitre.org/techniques/T1552/001/) — the technique your scanner is catching; useful context for a threat brief.

**HashiCorp Vault (~2 hrs)**
- [Vault — Getting Started tutorial (HashiCorp Learn)](https://developer.hashicorp.com/vault/tutorials/get-started/why-use-vault) — the official hands-on path: start Vault in dev mode, write/read secrets, understand the path model and token auth. Work through all six steps (~90 min).
- [Vault secrets engines — database engine](https://developer.hashicorp.com/vault/docs/secrets/databases) — how dynamic database credentials work: Vault creates a short-lived Postgres/MySQL user and destroys it when the lease expires. Read the overview and the PostgreSQL example.

**AWS-native pattern (~0.5 hr)**
- [AWS Secrets Manager — rotation overview](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html) — how AWS's managed rotation works, and when to use Secrets Manager vs. Parameter Store vs. Vault.

## Key concepts
- Git history persistence: removing a commit doesn't remove a secret from history
- Credential verification vs. detection: trufflehog actively checks if credentials are live
- Vault path model: `secret/data/<path>`, auth methods, policies
- Dynamic credentials: lease TTL, renewal, revocation
- MITRE ATT&CK T1552 (Unsecured Credentials), T1528 (Steal Application Access Token)
- Pre-commit and CI gates for secrets scanning

## AI acceleration
Feed a git diff containing potential secrets to a model and ask it to identify all credential
patterns and assess which are likely real vs. placeholder. This is useful for triage, but the model
can miss novel patterns and will occasionally hallucinate likelihood. Verification (calling the AWS
STS API to check if a key is live, or running trufflehog with `--only-verified`) is the
authoritative check — the model is a first-pass filter, not the final word. For Vault policy
authoring, AI is excellent — ask for a minimal-privilege policy for a given use case and review it
by cross-referencing the Vault policy syntax docs.
