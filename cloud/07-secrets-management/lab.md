# Lab 07 — Make the Leak Expire: From a Hardcoded Key to Leased, Fetched Credentials

*Variant D · breach-driven, build-first. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Four services: a **lab**
container (`trufflehog`, `gitleaks`, `vault`, `psql`, `awslocal`, plus `hvac`/`psycopg2` clients), a
**vault** server (HashiCorp Vault dev mode), a **db** container (Postgres — the store Vault mints leased
credentials against), and a **localstack** container (simulated AWS for the Secrets Manager variant).

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/07-secrets-management
make up          # build, start Vault, seed the planted-secret repo, wire the DB secrets engine
make demo        # worked walkthrough: scan → store → mint leased cred
make shell       # drop into the lab container to work
make down        # stop when done
```

`data/repo/` is a small git repo with a fake AWS key (`AKIAIOSFODNN7EXAMPLE` + a fake secret) committed
and then "removed" in a later commit — the Uber pattern. The key is intentionally non-functional.

> Never run `trufflehog`/`gitleaks` against repositories you do not own or have permission to scan.
> Everything here runs locally against seed data and simulated services you own. The credentials are
> non-functional placeholders.

## Scenario
You're the target account's responder. A GitHub secret-scanning alert says an AWS key was found in a
developer's repo. The developer insists they "removed it in the next commit" — the exact thing Uber's
engineers could have said in 2016. Your job is two halves: **confirm and triage the leak** (Part 1),
then **build the architecture that makes the leak expire on its own** (Parts 2–4), so the next hardcoded
key is harmless by construction. The build is the deliverable; the breach is the reason.

## Do

### Part 1 — Find it, and prove deletion is a lie

1. [ ] **See the secret survive its own "removal."** In `/lab/data/repo`, run `git log --oneline`, then
   `git show HEAD` (the key is *not* in the working tree) and `git log --all -p | grep AKIA` (it *is*
   in history). Write one line on why the "remove credentials" commit protects nothing — and why the
   only real response is revoke-and-rotate, not a follow-up commit.

2. [ ] **Scan with trufflehog.** Run `trufflehog git file:///lab/data/repo` (try `--json`). Record the
   **detector** that matched, the **commit SHA** the key was introduced in, and the file/line. This is
   the data you'd take to the developer: *when did this happen, and is it live?*

3. [ ] **Understand verification.** Re-run with `--results=verified,unknown` (or note the default
   behaviour): trufflehog tries the AWS STS API to check if the key is live. The fake key fails
   verification — the correct outcome here. Record why "verified" vs. "unverified" changes your
   incident urgency.

### Part 2 — Store it properly (encrypted, least-privilege) — necessary, not sufficient

4. [ ] **Store and gate a secret in Vault.** Set `VAULT_ADDR`/`VAULT_TOKEN`, then store the target account's app DB
   secret under `secret//app/database`. Write a Vault policy `app-ro` that allows
   *read-only* on `secret/data//app/*` and **nothing else**; mint a 1-hour token with it. Prove
   the wall: that token reads `secret//app/database` (success) and gets a **403** on
   `secret//infra/network`. That's blast-radius containment a hardcoded key can't give you.

5. [ ] **Note the flaw that remains.** Rotate the stored password (`vault kv put` again) and confirm the
   version increments. Then state the catch in one line: this secret is *well-stored* but still
   **long-lived** — it still fails open. Storing it better did not change *what it is*.

### Part 3 — Make it leased and fetched (the move the breach is about)

6. [ ] **Mint a leased database credential.** `make up` enabled Vault's database secrets engine against
   the `db` container. Run `vault read database/creds/app-role` (or `make dynamic-creds`) **twice**: note
   the **different unique username** each time, the `lease_id`, and the `lease_duration` (~300s). Nobody
   typed or stored a password.

7. [ ] **Use it, then watch it die.** Connect with the minted user
   (`PGPASSWORD=<pw> psql -h db -U <user> -d  -c 'SELECT count(*) FROM payments;'`) — it works.
   Wait past the TTL (or `vault lease revoke <lease_id>`) and try again — login fails. **This is the
   answer to the predict prompt:** there is nothing to rotate and nothing to leak long-term; a leaked
   copy is already dead.

8. [ ] **Fetch at runtime — hold nothing.** Run `make app-run` (`python3 data/app_runtime.py`) and read
   the code: the app carries **no** password — it authenticates to Vault, requests a leased credential,
   connects, and the credential expires behind it. Contrast `data/repo/config.py` from Part 1, where the
   secret lived in code. Write one line on why an env var baked at deploy would *not* count as fixing this.

9. [ ] **Automate rotation of the one secret that's left.** Run `make rotate-root`
   (`vault write -f database/rotate-root/postgres`). Vault changes the Postgres admin password
   and keeps it to itself — afterward **no human knows it.** Explain in one line why that's stronger than
   "it's encrypted."

### Part 4 — The cloud-native parallel, IAM-gated

10. [ ] **Store in a native store behind a `Resource`-scoped read.** Run `make aws-secrets`
    (`data/setup-aws-secrets.sh`): it puts the secret in Secrets Manager (LocalStack), authors an IAM
    policy allowing `secretsmanager:GetSecretValue` on **only that secret's ARN**, and reads it back.
    Read the policy JSON — confirm `Resource` is the one ARN, not `*`. State when you'd reach for Secrets
    Manager (managed, IAM-native, AWS-only) vs. Vault (multi-cloud, dynamic creds for many backends).

> **LocalStack honesty:** LocalStack CE does not fully *enforce* IAM, so the `Resource`-scoped policy is
> validated as written, not by a denied API call bouncing. Treat the IAM gate as *assessed from config*
> here — the same pattern enforces for real against AWS.

## Success criteria — you're done when
- [ ] `trufflehog` finds the planted key in history and you have its commit SHA, file, and detector
- [ ] You can explain in one sentence why the "remove credentials" commit doesn't protect 
- [ ] The `app-ro` token reads its path and gets a 403 outside it
- [ ] `vault read database/creds/app-role` mints a unique, **expiring** Postgres login that works, then
      stops working after its TTL — and you can answer the predict prompt with it
- [ ] `app_runtime.py` connects holding **no** static secret, and you can say why this makes the Part 1
      leak architecturally impossible
- [ ] A secret sits in Secrets Manager behind a `Resource`-scoped (not `*`) IAM read policy

## Deliverables
Commit to your portfolio repo:
- `incident-notes.md` — triage: commit SHA, detector, why rotation alone wouldn't have contained Uber, what you'd tell the developer
- `app-ro.hcl` — your Vault policy
- `secret-handling.md` — the four patterns you ran (static-in-code → Vault KV + policy → leased creds + runtime fetch → Secrets Manager + IAM), the threat each closes, and the one-line case for *why leased beats well-stored-static*
- `secrets-guard.sh` — the guardrail from **Automate & own it**

Do **not** commit: the `data/repo/` directory, any real credentials, leased DB credentials, Vault
tokens (even dev-mode), or the Secrets Manager values.

## Automate & own it
**Required — judgment-as-code, two-sided guardrail.** The Uber leak had two failure points: the key
reached git, and the stored secret (had they used one) could have been read by anything. Encode both:

1. **Stop it at the keyboard** — write `secrets-guard.sh`, a **gitleaks pre-commit hook** (and a CI
   gate) that runs over the staged diff, **exits non-zero** if a credential pattern (AKIA, DB URI, token)
   is found, and prints a summary (tool, finding count, top pattern). Install it on `data/repo/` and show
   it *blocking* a commit that re-introduces the AKIA key — prevention ahead of detection.
2. **Gate the store** — confirm your native-store read is `Resource`-scoped to the one secret ARN (the
   `make aws-secrets` policy), and state in `secret-handling.md` how an over-broad `secretsmanager:*` on
   `*` would re-open the blast radius you closed.

Have AI draft the hook's exit-code merging and the IAM JSON; you verify the exit code actually
propagates a non-zero from gitleaks, that stderr is **not** suppressed (a tool error must not look like a
clean scan), and that the IAM `Resource` is the literal ARN. This is your verdict made un-recurrable —
the leak can no longer reach history, and the store can no longer over-share.

```bash
#!/usr/bin/env bash
# Starter scaffold — secrets-guard.sh
TARGET="${1:-.}"
command -v gitleaks >/dev/null || { echo "gitleaks not found" >&2; exit 1; }
# YOU: run gitleaks over the staged diff (protect mode); capture exit code
# YOU: print summary (tool, finding count, top pattern); do NOT swallow stderr
# YOU: exit non-zero on any finding so the commit/CI step fails
```

## AI acceleration
Paste a `trufflehog` JSON finding and ask a model to draft the "what to do next" incident section —
owner of the credential type, rotation steps, how to confirm it's no longer live. A 5-minute draft
versus 45 minutes of doc-hunting. **Validate the rotation steps are right for the specific service** —
AWS IAM key rotation, GitHub PAT rotation, and a Postgres password rotation are three different
procedures the model will sometimes blur. For Vault/IAM policy authoring, ask for the minimal-privilege
version, then *prove* it denies everything outside the one path/ARN rather than trusting the read.

## Connects forward
The `gitleaks` guardrail you wrote becomes the secrets stage of the **CI/CD pipeline** in module 08,
where it gates PRs before a secret can ever merge. The leased-credential and runtime-fetch architecture
is what closes the "secrets pulled into a broker" requirement of the **Phase-1 project** and the
**capstone** — the over-broad role and the hardcoded key both stop being a way in.

## Marketable proof
> "I found a leaked AWS key in a git repo's history after the developer believed it was removed, then
> rebuilt the architecture that makes the Uber breach impossible: Vault-leased database credentials an
> app fetches at runtime, automated root rotation so no human holds the master password, and an
> IAM-`Resource`-scoped Secrets Manager store — fronted by a gitleaks pre-commit hook that blocks the
> leak at the keyboard. I can explain why rotating Uber's key after the fact contained nothing."

## Stretch
- Swap the leased backend: configure Vault's `aws` secrets engine to mint short-TTL **IAM** credentials instead of Postgres logins, and compare the model to a static access key.
- Make `app_runtime.py` *renew* its lease on a timer (`sys/leases/renew`) and show what happens when it lets the lease lapse mid-request — the failure mode you must design around.
- Re-render the predict prompt as a one-paragraph brief to a non-technical CISO: why "we rotated the key" is not an incident-contained statement.
