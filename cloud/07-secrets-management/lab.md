# Lab 07 — Make the Leak Expire: from a hardcoded key to leased, fetched credentials

> **Hands-on lab.** Environment: `plaintext-labs/cloud/07-secrets-management` (HashiCorp **Vault** +
> **Postgres** + **trufflehog**, plus **floci** — a free local AWS emulator — for the Secrets Manager
> variant; no cloud account). Objective: **detect a leaked credential in git history, then rebuild the
> architecture so the leak expires on its own** — Vault-leased DB creds an app fetches at runtime.
> Target: **~90 min**, one finish line.
>
> *Variant D · breach-driven, build-first. [← Back to the module concept](README.md)*

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **"Removing" a committed secret leaves it in history.** | `git log`/`trufflehog git` read *all* history, not HEAD — the only real fix is **revoke + rotate**, never a follow-up commit. |
| 2 | **A static secret fails OPEN.** | Valid from creation until a human notices and acts — rotation is a race you start *after* losing. This is why rotating Uber's key contained nothing. |
| 3 | **A leased/dynamic credential fails CLOSED.** | Minted per request, destroyed at lease end — a leaked copy is dead in minutes whether or not anyone noticed. |
| 4 | **Fetch at runtime; hold nothing.** | An env var baked in at deploy is a *slower hardcode*. The app authenticates to the broker and fetches the leased cred, which expires behind it. |
| 5 | **Auto-rotated root > encrypted.** | After `rotate-root`, *no human knows* the master password — you can't leak what you don't possess. |
| 6 | **The guardrail is two-sided.** | A gitleaks pre-commit hook stops the leak at the keyboard; a `Resource`-scoped read policy stops the store from over-sharing. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [build, in four moves](README.md#the-build-in-four-moves) and
> [Vault database secrets engine](README.md#go-deeper-35-hrs--optional).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A developer commits an AWS key, panics, and "removes" it in the next commit. Where is the key now,
   and what is the *only* correct response?
2. Uber rotated the leaked key after the breach. In one sentence, why didn't rotation contain it — and
   what property does a *leased* credential have that a well-stored *static* one still lacks?

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. Four services: a **lab**
container (`trufflehog`, `gitleaks`, `vault`, `psql`, `aws`, plus `hvac`/`psycopg2` clients), a **vault**
server (Vault dev mode), a **db** container (Postgres — the store Vault mints leased credentials
against), and a **floci** container (simulated AWS for the Secrets Manager variant).

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/07-secrets-management
make up          # build, seed the planted-secret repo, wire the DB secrets engine
make demo        # worked walkthrough: scan → static store → leased cred → runtime app → AWS variant
make shell       # drop into the lab container to work
make down        # stop when done
```

`data/repo/` is a small git repo with a fake AWS key (`AKIAIOSFODNN7EXAMPLE` + a fake secret) committed
in commit 1 and "removed" in commit 2 — the Uber pattern. The key is the AWS documentation example key
and is intentionally non-functional.

> **▸ On track if:** `make demo` runs four parts end to end — trufflehog prints an **AWS** finding from
> `data/repo`, `vault read database/creds/app-role` returns a unique username with a `lease_duration`, the
> runtime app reports `3 payment rows`, and the AWS variant prints a `Resource`-scoped policy. The
> environment is live.

> **Authorization note.** Only run `trufflehog`/`gitleaks` against repos you own or have written
> permission to scan. Everything here runs locally against seed data and simulated services **you own**;
> the credentials are non-functional placeholders.

---

## Scenario

You're the target account's responder. A GitHub secret-scanning alert says an AWS key was found in a
developer's repo. The developer insists they "removed it in the next commit" — the exact thing Uber's
engineers could have said in 2016. Your job is two halves: **confirm and triage the leak** (Part 1), then
**build the architecture that makes the leak expire on its own** (Parts 2–4), so the next hardcoded key
is harmless by construction. The build is the deliverable; the breach is the reason. Each step runs the
same rhythm: **Predict → Do → Reveal → Record.**

---

## Build it — read a little, do a little

### Part 1 — Find it, and prove deletion is a lie

**Concept (30 sec):** Flight-card #1. "Removing" a secret in a later commit protects nothing — it lives
in commit 1 forever, and `trufflehog git` reads the whole history. The tool finds; you triage.

**Predict, then do:** write down whether HEAD *looks* clean, then prove it isn't. In `/lab/data/repo`:
`git log --oneline` (three commits), `git show HEAD:config.py` (no key in the working tree), then
`git log --all -p | grep AKIA` (the key is right there in history). Now scan: `make scan-history` (or
`trufflehog git file:///lab/data/repo`).

> **▸ On track if:** trufflehog reports a finding with **Detector Type: AWS**, the **commit SHA** where
> `config.py` introduced `AKIAIOSFODNN7EXAMPLE`, and the file/line — even though HEAD is "clean." **Record:**
> the commit SHA, detector, and one line on why the "remove credentials" commit protects nothing.

**Understand verification (30 sec):** `make scan-history` runs `--no-verification` for speed. Re-run
`trufflehog git file:///lab/data/repo` *without* that flag: trufflehog calls the AWS STS API to check if
the key is live. The example key fails verification — the correct outcome.

> **▸ On track if:** you can say why **verified vs. unverified** changes your incident urgency (a live key
> is a page-someone emergency; a dead placeholder is a hygiene ticket). **Record** which one this is.

### Part 2 — Store it properly (encrypted, least-privilege) — necessary, not sufficient

**Concept (30 sec):** A secrets manager encrypts at rest and puts an access wall in front of every read.
Better than "in code" — but a stored *static* secret is still long-lived. It still fails open.

**Do it:** `make vault-demo` stores and reads a static secret under `secret//app/database`. Then author
least privilege yourself: write a Vault policy `app-ro` allowing *read-only* on `secret/data//app/*`
and **nothing else**, mint a 1-hour token with it, and prove the wall — that token reads
`secret//app/database` (success) and gets a **403** on `secret//infra/network`.

> **▸ On track if:** the `app-ro` token reads its own path and is **denied (403)** outside it — blast-radius
> containment a hardcoded key can never give you. **Record:** rotate the stored value (`vault kv put`
> again), confirm the version increments, then state the catch in one line — *well-stored, but still
> long-lived; still fails open.*

### Part 3 — Make it leased and fetched (the move the breach is about)

**Concept (30 sec):** Flight-cards #3 and #4. Vault's database engine mints a brand-new Postgres user per
request with a short lease and destroys it at lease end. Nobody types it; nothing stores it.

**Do it:** `make dynamic-creds` (or `vault read database/creds/app-role`) — run it **twice**.

> **▸ On track if:** each run returns a **different unique username** (a `v-token-app-role-…` value), a
> `lease_id`, and `lease_duration` **~300s**. No password was typed or stored. **Record:** paste the two
> usernames — proof they're per-request.

**Use it, then watch it die:** connect with a minted user
(`PGPASSWORD=<pw> psql -h db -U <user> -d corp -c 'SELECT count(*) FROM payments;'`) — it works. Wait past
the TTL, or `vault lease revoke <lease_id>`, and try again.

> **▸ On track if:** the query first returns `3` (the seeded payment rows), then **login fails** after the
> lease expires. **This is the answer to the predict prompt:** there is nothing to rotate and nothing to
> leak long-term — a leaked copy is already dead. **Record** the before/after.

**Fetch at runtime — hold nothing:** `make app-run` (`python3 data/app_runtime.py`) and read the code —
the app carries **no** password; it authenticates to Vault, requests a leased credential, connects, and
the credential expires behind it.

> **▸ On track if:** the app prints `[app] Vault minted a dynamic DB user: v-token-app-role-…`, its
> `lease_id`/`ttl`, `queried Postgres as … : 3 payment rows`, and `No static secret was read from code,
> env, or disk.` **Record** one line on why an env var baked at deploy would *not* count as fixing this.

**Automate rotation of the one secret that's left:** `make rotate-root`
(`vault write -f database/rotate-root/postgres`). Vault changes the Postgres admin password and keeps it
to itself.

> **▸ On track if:** the target prints that the admin password is **now known only to Vault** — afterward
> *no human knows it*. **Record** one line on why that's strictly stronger than "it's encrypted."

### Part 4 — The cloud-native parallel, IAM-gated

**Concept (30 sec):** Flight-card #6. The native store's blast radius is set by the read policy —
`Resource`-scoped to one ARN, not `*`.

**Do it:** `make aws-secrets` (`data/setup-aws-secrets.sh`) puts the secret in Secrets Manager (floci),
authors an IAM policy allowing `secretsmanager:GetSecretValue` on **only that secret's ARN**, and reads
it back. Read the policy JSON.

> **▸ On track if:** the printed policy's `Resource` is the **one secret ARN**, not `*`, and the value
> reads back. **Record:** when you'd reach for Secrets Manager (managed, IAM-native, AWS-only) vs. Vault
> (multi-cloud, dynamic creds for many backends).

> **Emulator honesty:** floci does **not** fully enforce IAM, so the `Resource`-scoped policy is validated
> *as written*, not by a denied API call bouncing. Treat the IAM gate as **assessed from config** here —
> the identical pattern enforces for real against AWS.

---

## Prove the control (your finish line)

**One finish line: the leaked secret is detected *and* the credential is moved to a broker so the leak
can't recur.** You're done when all three hold together:

1. **Detected** — `trufflehog` finds the planted key in `data/repo` history (commit SHA + detector +
   file), proving the "removed it" commit protected nothing.
2. **Moved to a broker** — `app_runtime.py` connects to Postgres holding **no** static secret, using a
   Vault-leased credential that expires behind it. The Part 1 leak is now *architecturally impossible*:
   there is no long-lived key in code to leak.
3. **The guardrail flips** — your `Automate & own it` hook (below) **fails** a commit that re-introduces
   the AKIA key and **passes** a clean one, and your native-store read is `Resource`-scoped to one ARN.
   If it doesn't flip, the verdict isn't yet code.

Score your README "Predict it" answer against the reveal in Part 3; note whether you got it.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why doesn't "removing" a committed secret in the next commit remove it — and what's the only correct
   response to a leaked credential?
2. Why didn't rotating Uber's key contain the breach, and what property does a leased credential have that
   a well-stored static one lacks?
3. After `rotate-root`, why is "no human knows the master password" stronger than "the password is
   encrypted"?

---

## Deliverables

Commit to your portfolio repo:

- **`incident-notes.md`** — triage: commit SHA, detector, verified vs. unverified, why rotation alone
  wouldn't have contained Uber, and what you'd tell the developer.
- **`app-ro.hcl`** — your Vault policy.
- **`secret-handling.md`** — the four patterns you ran (static-in-code → Vault KV + policy → leased creds
  + runtime fetch → Secrets Manager + IAM), the threat each closes, and the one-line case for *why leased
  beats well-stored-static*.
- **`secrets-guard.sh`** — the guardrail from **Automate & own it**.

Do **not** commit: the `data/repo/` directory, any real credentials, leased DB credentials, Vault tokens
(even dev-mode), or the Secrets Manager values.

## Automate & own it

**Required — judgment-as-code, two-sided guardrail.** The Uber leak had two failure points: the key
reached git, and the stored secret (had they used one) could have been read by anything. Encode both:

1. **Stop it at the keyboard** — write `secrets-guard.sh`, a **gitleaks pre-commit hook** (and a CI gate)
   that runs over the staged diff, **exits non-zero** if a credential pattern (AKIA, DB URI, token) is
   found, and prints a summary (tool, finding count, top pattern). Install it on `data/repo/` and show it
   *blocking* a commit that re-introduces the AKIA key — prevention ahead of detection.
2. **Gate the store** — confirm your native-store read is `Resource`-scoped to the one secret ARN (the
   `make aws-secrets` policy), and state in `secret-handling.md` how an over-broad `secretsmanager:*` on
   `*` would re-open the blast radius you closed.

Have AI draft the hook's exit-code merging and the IAM JSON; you verify the exit code actually propagates
a non-zero from gitleaks, that stderr is **not** suppressed (a tool error must not look like a clean
scan), and that the IAM `Resource` is the literal ARN. This is your verdict made un-recurrable — the leak
can no longer reach history, and the store can no longer over-share.

```bash
#!/usr/bin/env bash
# Starter scaffold — secrets-guard.sh
TARGET="${1:-.}"
command -v gitleaks >/dev/null || { echo "gitleaks not found" >&2; exit 1; }
# YOU: run gitleaks over the staged diff (protect mode); capture exit code
# YOU: print summary (tool, finding count, top pattern); do NOT swallow stderr
# YOU: exit non-zero on any finding so the commit/CI step fails
```

## Definition of done (`secrets-management` ✅)

- [ ] `trufflehog` finds the planted key in history with its commit SHA, file, and **AWS** detector — and you can explain why the "remove credentials" commit protected nothing.
- [ ] The `app-ro` token reads its path and is **denied (403)** outside it.
- [ ] `vault read database/creds/app-role` mints a unique, **expiring** Postgres login that works, then stops after its TTL — and you can answer the predict prompt with it.
- [ ] `app_runtime.py` connects holding **no** static secret (`3 payment rows`) and you can say why this makes the Part 1 leak architecturally impossible.
- [ ] `rotate-root` leaves the admin password known only to Vault, and a secret sits in Secrets Manager behind a `Resource`-scoped (not `*`) IAM read policy.
- [ ] The guardrail **fails** the AKIA-reintroducing commit and **passes** a clean one.
- [ ] You can explain all six flight-card facts cold.

## Connects forward

The `gitleaks` guardrail you wrote becomes the secrets stage of the **CI/CD pipeline** in module 08,
where it gates PRs before a secret can ever merge. The leased-credential and runtime-fetch architecture
is what closes the "secrets pulled into a broker" requirement of the **Phase-1 project** and the
**capstone** — the over-broad role and the hardcoded key both stop being a way in.

## Marketable proof

> "I found a leaked AWS key in a git repo's history after the developer believed it was removed, then
> rebuilt the architecture that makes the Uber breach impossible: Vault-leased database credentials an app
> fetches at runtime, automated root rotation so no human holds the master password, and an
> IAM-`Resource`-scoped Secrets Manager store — fronted by a gitleaks pre-commit hook that blocks the leak
> at the keyboard. I can explain why rotating Uber's key after the fact contained nothing."

## Stretch

- Swap the leased backend: configure Vault's `aws` secrets engine to mint short-TTL **IAM** credentials instead of Postgres logins, and compare the model to a static access key.
- Make `app_runtime.py` *renew* its lease on a timer (`sys/leases/renew`) and show what happens when it lets the lease lapse mid-request — the failure mode you must design around.
- Re-render the predict prompt as a one-paragraph brief to a non-technical CISO: why "we rotated the key" is not an incident-contained statement.
