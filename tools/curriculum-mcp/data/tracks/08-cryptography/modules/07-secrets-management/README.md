# Module 07 — Secrets Management

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *Secrets in environment variables, config files, and source code are not secrets — they are liabilities waiting to be found.*

## Why this matters

Secrets management is the gap between "we have good cryptography" and "our credentials are actually secure." The most careful TLS configuration is irrelevant if the database password is in a `.env` file committed to git, or if every developer has a copy of the production API key in their shell history. Secrets management tools — HashiCorp Vault and Mozilla SOPS are the open-source standard — solve the distribution and lifecycle problems that make secrets insecure: centralised storage, access control, audit logging, automatic rotation, and encryption at rest and in transit.

## Objective

Use Vault's dev server to store, retrieve, and rotate a database credential, demonstrate the audit log, and use SOPS with an age key to encrypt a YAML configuration file — covering both the runtime secrets broker pattern and the secrets-in-git pattern.

## The core idea

Vault's security model separates *secrets storage* from *secrets access*. Secrets are stored encrypted in Vault's backend (an encrypted database, a cloud KMS, or a hardware HSM). Access is controlled by policies — Vault tokens or identity-linked roles grant access to specific paths, not to all secrets. Every read, write, and rotation is written to the audit log. This combination — encrypted storage, policy-based access, comprehensive audit trail — is why Vault is the production standard for secrets management in cloud-native environments.

The critical insight is that the secret itself never needs to leave Vault in most architectures. Dynamic secrets take this further: instead of storing a long-lived database password, Vault creates an ephemeral database credential on demand, with a short lease, and revokes it when the lease expires. An application that uses dynamic secrets never holds a long-lived credential — if the application is compromised, the attacker gets a credential that expires in minutes. This is the opposite of a hardcoded password: the application gets a fresh, expiring credential every time it connects.

SOPS (Secrets Operations) solves a different problem: secrets that need to live *in* a git repository, such as Kubernetes secrets, Helm values files, or Terraform variable files. SOPS encrypts the values (not the keys) of a YAML, JSON, or dotenv file, using a key from Vault, AWS KMS, GCP KMS, or a local age key. The encrypted file can be committed to git — the keys are readable (so a reviewer can see what is being configured), the values are encrypted (so a compromised git clone doesn't yield live credentials). This is the "GitOps-safe secrets" pattern.

The common mistake organisations make is treating secrets management as a one-time deployment problem — "we set up Vault, now we're done." The ongoing discipline is secret rotation: Vault's leases automatically revoke dynamic secrets, but static secrets (API keys, TLS certificates, service account passwords) require an explicit rotation process. Secret sprawl — the gradual accumulation of copies of a secret across environments, developer machines, CI/CD systems, and backups — is the primary way secrets leak even in organisations that use Vault. The remediation is a combination of access auditing (who has retrieved this secret, and from where?), automatic rotation (so copies that do exist become stale quickly), and detection (module 08 scans for secrets that escaped the vault).

## Learn (~4 hrs)

**HashiCorp Vault**
- [Vault documentation — Getting Started](https://developer.hashicorp.com/vault/tutorials/get-started) — work through the "Your first secret" and "Dynamic secrets" tutorials (~1 hr); these two tutorials cover the core workflow.
- [Vault architecture documentation](https://developer.hashicorp.com/vault/docs/internals/architecture) — read the storage backend, seal/unseal, and audit device sections; understand why Vault needs an unseal key before explaining it to others.

**SOPS**
- [mozilla/sops README (GitHub)](https://github.com/getsops/sops) — read the usage section and the "Encryption Protocol" section to understand how SOPS encrypts values while preserving key structure.
- [age encryption tool](https://github.com/FiloSottile/age) — read the README; age is the modern, simple alternative to GPG for SOPS key management.

**Secrets management principles**
- [CISA Alert AA22-137A — Weak Security Controls (Credentials section)](https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-137a) — real-world context for why hardcoded credentials are exploited routinely; read the credentials section.

## Key concepts

- Vault: encrypted storage + policy-based access + audit log. Never store secrets in environment variables or config files committed to source control.
- Dynamic secrets: Vault creates ephemeral credentials on demand; revokes them automatically on lease expiry. No long-lived credentials in the application.
- SOPS: encrypts values (not keys) in structured files; git-safe secrets for Kubernetes/Terraform/Helm workflows.
- Secret rotation: Vault automates dynamic secret revocation; static secrets require an explicit rotation process.
- Secret sprawl: the accumulation of secret copies is the primary leak vector — audit access logs and rotate frequently.

## AI acceleration

Ask an AI to generate a Vault policy HCL file that grants read access to `secret/meridian/app/*`
but not write or delete access. Then verify the policy against the [Vault policy documentation](https://developer.hashicorp.com/vault/docs/concepts/policies) —
does the capability list match the intended permissions? Apply the policy and confirm a token
with that policy can read but not write the secret.
