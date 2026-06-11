# Lab 07 — Secrets Management & Detection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/07-secrets-management
make up
make demo
make shell
make down
```

The environment has four services: a **lab** container (`trufflehog`, `vault`, `psql`, `awslocal`,
plus the `hvac`/`psycopg2` Python clients), a **vault** container (HashiCorp Vault 1.17 dev mode —
root token `root-dev-token`, address `http://vault:8200`), a **db** container (Postgres 16, the
store Vault mints dynamic credentials against), and a **localstack** container (simulated AWS for the
Secrets Manager variant). `make up` seeds the repo *and* configures Vault's database secrets engine.

`data/repo/` is a small git repository with a fake AWS access key that was committed and then
"removed" in a subsequent commit — exactly the pattern that leaves a credential in history. The key
(`AKIAIOSFODNN7EXAMPLE` + fake secret) is intentionally non-functional.

This lab has two equal halves: **detecting** a leaked secret (Part 1) and **safely operating**
secrets so the leak never happens — static storage with least privilege (Part 2), *dynamic*
credentials an app fetches at runtime (Part 3), and the cloud-native Secrets Manager pattern (Part 4).

> Never run trufflehog against repositories you do not own or have explicit written permission to
> scan. The fake credentials in this lab are non-functional placeholders.

## Scenario

Meridian Financial's security team has received an alert from their GitHub secret-scanning
integration: a potential AWS key was found in a developer's repository. The developer says they
"already removed it in the next commit." You are running the incident triage: verify whether the
key persists in history, assess whether it was ever live, and then demonstrate the remediation
architecture — Vault-managed secrets — to the engineering team.

## Do

### Part 1: Secrets Detection

1. [ ] **Understand the repository history.**
   From the lab shell, navigate to `/lab/data/repo` and inspect the git log.
   *Hint:* `git log --oneline` shows the commit history. Then `git log -p` shows the full diff per
   commit. Can you see the key in the history even though the "remove credentials" commit came later?

2. [ ] **Run trufflehog against the full git history.**
   Run `trufflehog git file:///lab/data/repo` from the lab container.
   Note: trufflehog scans the complete history, not just HEAD.
   What detector matched the finding? What commit SHA was the key introduced in?

3. [ ] **Run trufflehog with verification disabled.**
   Add `--no-verification` and observe the output. Understand the difference: trufflehog normally
   tries to call the AWS STS API to verify if a key is live. The fake key in this lab fails
   verification — which is the correct outcome for a non-functional test key.
   *Hint:* `trufflehog git file:///lab/data/repo --no-verification --json`

4. [ ] **Find the specific commit and affected file.**
   Using `git log -p` and the commit SHA from the trufflehog output, find the exact file and line
   where the credential was introduced. Note the commit message and timestamp. In a real incident
   this is the data you'd take to the developer for a "when did this happen and is it live?" conversation.

5. [ ] **Understand why deletion doesn't fix it.**
   Run `git show HEAD` on the repository. Confirm the key is NOT in the current working tree.
   Now run `git log --all -p | grep AKIA`. Confirm it IS in history. Write a one-line explanation
   of why the key needs to be rotated regardless of the "remove" commit.

### Part 2: Vault Secrets Management

6. [ ] **Explore the Vault environment.**
   From the lab shell, set `VAULT_ADDR=http://vault:8200` and `VAULT_TOKEN=root-dev-token`.
   Run `vault status` and `vault secrets list`. Note which secrets engines are enabled.

7. [ ] **Store a secret in Vault.**
   Store a fake database password for Meridian's app under `secret/meridian/app/database`.
   *Hint:* `vault kv put secret/meridian/app/database username=appuser password=db-password-placeholder`
   Then read it back: `vault kv get secret/meridian/app/database`. Note the `created_time` metadata.

8. [ ] **Write a Vault policy.**
   Create a policy called `meridian-app-ro` that allows read-only access to `secret/meridian/app/*`
   and nothing else. Write the policy file and apply it with `vault policy write`.
   *Hint:* The policy HCL format is `path "secret/data/meridian/app/*" { capabilities = ["read"] }`

9. [ ] **Create a token with the policy and verify least-privilege.**
   Create a token attached to `meridian-app-ro` with a TTL of 1 hour.
   *Hint:* `vault token create -policy=meridian-app-ro -ttl=1h`
   Use the new token to try to read `secret/meridian/app/database` — it should succeed.
   Then try to read `secret/meridian/infra/network` — it should fail with a 403. This is the
   blast-radius containment that static credentials cannot provide.

10. [ ] **Rotate the static secret.**
    Update the password under `secret/meridian/app/database` to a new value. Read it back and
    confirm the `version` field incremented. Note that Vault's KV v2 keeps the previous version —
    you can roll back if needed, or force-destroy old versions. This is manual rotation; Part 3
    removes the need for it.

### Part 3: Dynamic credentials & runtime fetch (the real operate upgrade)

Static secrets — even well-stored, least-privilege ones — share one flaw: they're long-lived, so a
leak is valid until someone notices and rotates. Dynamic secrets remove that flaw: the app is handed
a credential minted *on request* that *expires on its own*.

11. [ ] **Mint a dynamic database credential.**
    `make up` already enabled Vault's database secrets engine against the `db` Postgres container.
    Mint a credential: `make dynamic-creds` (or in the shell: `vault read database/creds/app-role`).
    Note the **unique username**, the `lease_id`, and the `lease_duration` (300s). Run it twice — you
    get a *different* user each time. Nobody typed or stored a password.

12. [ ] **Use the dynamic credential, then watch it die.**
    From the lab shell, connect with the minted user:
    `PGPASSWORD=<pw> psql -h db -U <minted-user> -d meridian -c 'SELECT count(*) FROM payments;'`.
    It works. Wait past the 5-minute TTL (or `vault lease revoke <lease_id>`) and try again — the
    login now fails. The credential self-destructed; there is nothing to rotate and nothing to leak
    long-term.

13. [ ] **Have the app fetch its secret at runtime.**
    Run `make app-run` (`python3 data/app_runtime.py`). Read the code: the app holds **no** password
    — it authenticates to Vault, asks for a dynamic credential, connects, and the credential expires
    behind it. Contrast with `data/repo/config.py` from Part 1, where the secret lived in code. This
    is the architecture that makes the trufflehog finding impossible.

14. [ ] **Automate rotation of the root credential.**
    Even the admin password Vault uses to mint users should rotate. Run `make rotate-root`
    (`vault write -f database/rotate-root/meridian-postgres`). Vault changes the Postgres admin
    password and *keeps it to itself* — after this, no human knows it. Explain in one line why
    "no human knows the credential" is a stronger property than "the credential is encrypted."

### Part 4: The cloud-native variant — AWS Secrets Manager

15. [ ] **Store and read a secret via Secrets Manager, gated by IAM.**
    Run `make aws-secrets` (`data/setup-aws-secrets.sh`). It stores the app secret in Secrets Manager
    (LocalStack), authors a least-privilege IAM policy that allows `secretsmanager:GetSecretValue` on
    *only that secret's ARN*, and reads it back. Read the policy JSON: note the `Resource` is the one
    secret, not `*`. Explain when you'd reach for Secrets Manager (managed, IAM-native, AWS-only) vs.
    Vault (multi-cloud, dynamic creds for many backends).

## Success criteria — you're done when

- [ ] trufflehog finds the planted credential in git history and reports the commit SHA and file
- [ ] You can explain in one sentence why the "remove credentials" commit doesn't protect Meridian
- [ ] A Vault-stored secret is readable with the `meridian-app-ro` policy token, and the same token
      gets a 403 outside its policy path
- [ ] `vault read database/creds/app-role` mints a unique, expiring Postgres login that works, then
      stops working after its TTL
- [ ] `app_runtime.py` connects to Postgres holding no static secret, and you can explain why this
      makes the Part 1 leak architecturally impossible
- [ ] A secret is stored in Secrets Manager behind a `Resource`-scoped (not `*`) IAM read policy

## Deliverables

Commit to your portfolio repo:
- `incident-notes.md` — triage notes: commit SHA, detector, why rotation is required, what you'd
  tell the developer
- `meridian-app-ro.hcl` — the Vault policy you wrote
- `secret-handling.md` — a short comparison of the four patterns you ran (static-in-code → Vault KV
  + policy → Vault dynamic creds + runtime fetch → Secrets Manager + IAM), with the threat each one
  closes and when you'd choose it
- `secrets-scanner.sh` — the automation script from **Automate & own it** below

Do **not** commit: the `data/repo/` directory (it's in the lab repo), any real credentials, dynamic
DB credentials, or Vault tokens (even dev-mode ones).

## Automate & own it

**Required.** Write `secrets-scanner.sh` — a pre-commit and CI gate that:
1. Runs `trufflehog git` against the repo in `$1` (default: current directory)
2. Runs `gitleaks detect` against the same repo (for coverage comparison)
3. Exits non-zero if either tool finds a verified or unverified credential
4. Outputs a summary: tool, finding count, highest-severity pattern found

AI drafts the argument handling and exit-code merging. You verify:
- that the exit-code logic correctly propagates a non-zero from either tool
- that the script does not suppress stderr (important — tool errors should not look like clean scans)
- that it handles the case where a tool is not installed (graceful degradation vs. silent skip)

```bash
#!/usr/bin/env bash
# Starter scaffold
TARGET="${1:-.}"
FAIL=0
command -v trufflehog >/dev/null || { echo "trufflehog not found"; exit 1; }
# YOU: run trufflehog; capture exit code
# YOU: run gitleaks if available; capture exit code
# YOU: print summary; exit $FAIL
```

## AI acceleration

Paste a `trufflehog` JSON output to a model and ask it to draft the "what to do next" section
of a security incident ticket: which service owns the credential type, what rotation steps are
needed, and how to confirm the credential is no longer live. This is where AI accelerates the
triage-to-remediation cycle — a 5-minute ticket draft instead of 45 minutes of documentation
hunting. What you must validate: the rotation steps are actually correct for the specific service
(AWS IAM key rotation is different from GitHub PAT rotation is different from a database password).

## Connects forward

In Module 08 (CI/CD Security) you will integrate `gitleaks` into a pipeline that gates PRs before
they can introduce secrets. The Vault architecture you demonstrated here is what Meridian would use
to eliminate the hardcoded credentials that trufflehog is catching.

## Marketable proof

> "I found a leaked AWS credential in a git repository's history after the developer believed it was
> removed, then rebuilt the architecture that makes the leak impossible — Vault dynamic credentials an
> app fetches at runtime, automated root rotation, and an IAM-gated Secrets Manager store."

## Stretch

- Wire `app_runtime.py` to renew its lease (`sys/leases/renew`) on a timer instead of re-fetching,
  and show what happens when it lets the lease lapse mid-request.
- Add a `git-secrets` (or `pre-commit` + `gitleaks`) hook to `data/repo/` and show it blocking a
  commit that contains the AKIA pattern — prevention at the keyboard, ahead of detection in CI.
- Swap the dynamic-creds backend: configure Vault to mint short-TTL AWS IAM credentials (the `aws`
  secrets engine) instead of Postgres logins, and compare the model.
