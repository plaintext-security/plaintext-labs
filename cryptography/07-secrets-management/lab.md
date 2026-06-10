# Lab 07 — Secrets Management

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/07-secrets-management
make up        # start Vault dev server + lab container with sops/age
make demo      # store/retrieve/rotate a secret in Vault; encrypt a YAML with sops
make shell     # drop into the lab container
make down      # stop when done
```

> Everything runs locally. Vault runs in dev mode (no persistence). SOPS uses a local age key.

## Scenario

Meridian Financial's payroll API has been hardcoding its database password in `config.yml`
and committing it to git. Your job: migrate the credential to Vault, demonstrate the full
lifecycle (store, retrieve, rotate, audit), and use SOPS to encrypt the remaining
configuration values that must stay in git.

## Do

1. [ ] `make demo` — watch the demo sequence: secret storage, retrieval, rotation, audit log
   review, SOPS encryption. Note the Vault path, the lease ID, and the audit log format.

2. [ ] `make shell` and use the Vault CLI (`vault kv`) to store a database credential under a
   path, read it back, and read it as JSON (the form an application consumes). Confirm the value
   round-trips.

3. [ ] Rotate the credential — overwrite it with a new value — then inspect the secret's
   metadata. How many versions does the KV engine retain, and can you still retrieve the
   previous one?

4. [ ] Inspect the Vault audit log (under `/vault/logs/`) and find the entries for your read and
   write operations. What does each entry record — and, critically, what does it *not* record?

5. [ ] Encrypt a YAML config containing sensitive values with SOPS, using a locally generated
   `age` key. Then decrypt it. In the encrypted file, which parts are ciphertext and which stay
   readable — and what does that property mean for committing the file to git?

6. [ ] Write `secrets-analysis.md`: compare the two patterns (Vault for runtime secrets vs
   SOPS for git-safe secrets). When would you use each, and what are the security trade-offs?

## Success criteria — you're done when

- [ ] You stored, read, and rotated a secret in Vault.
- [ ] You identified read/write operations in the Vault audit log.
- [ ] You encrypted a YAML file with SOPS and confirmed values are encrypted, keys are not.
- [ ] You can explain the difference between the Vault and SOPS patterns.

## Deliverables

`secrets-analysis.md` — your Vault vs SOPS comparison and the Meridian migration recommendation.
Commit it.

## Automate & own it

**Required.** Write a Python script `vault-rotate.py` that: connects to Vault via the `hvac`
library, reads a secret at a specified path, generates a new random password, writes the new
password to Vault, and prints a rotation summary (old version number, new version number,
timestamp). Have an AI draft the `hvac` API calls; you verify the version numbers increment
correctly and the old value is preserved in version history.

## AI acceleration

Ask an AI: "Write a Vault policy HCL that allows the payroll service to read
`secret/meridian/payroll/db` but not write or delete it, and deny access to all other paths."
Apply the policy in Vault and verify with a token that has only this policy — can it read?
Can it write? Check the Vault policy documentation to confirm the capability list is correct.

## Connects forward

The Vault dev server you used here is the same architecture as module 06's PKI integration —
Vault can serve as the backend for step-ca's certificate storage. Module 08 (Secret Detection)
covers the failure mode when secrets escape Vault — finding them in git history is the
detection exercise.

## Marketable proof

> "I migrated a hardcoded database credential to HashiCorp Vault, demonstrated rotation and
> audit logging, and encrypted git-committed configuration values with SOPS — the two patterns
> that eliminate credential sprawl in a production environment."

## Stretch

- Enable Vault's database secrets engine: configure it with a (mock) PostgreSQL connection and
  generate a dynamic credential. Observe the TTL and verify it can't be renewed past the max TTL.
  This is the dynamic secrets pattern that eliminates long-lived credentials entirely.
- Research Vault's AppRole authentication method: how does a CI/CD pipeline authenticate to
  Vault without a static token? What is a role ID and secret ID, and why are they safer than a
  long-lived root token?
