# Module 07 — Secrets Management & Detection

*Variant D · breach-driven, build-first deepened ("a leak you can't rotate fast enough"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *a secret in code is a secret you can never rotate fast enough; the fix isn't hiding it better, it's making it short-lived and fetched.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 02 — Cloud Identity & IAM](../02-cloud-identity-iam/README.md)
{ .module-meta }


## The case

In 2016, an attacker found a set of **Amazon Web Services access keys hardcoded in source code** that
Uber engineers had pushed to a **private GitHub repository**. The keys weren't on the public internet —
the repo was private — but the attacker reached it anyway (through a separate credential exposure) and,
once inside, the keys were just *sitting there in the code*. They unlocked an S3 bucket holding the
personal data of **roughly 57 million riders and drivers**, plus the driver's-license numbers of about
**600,000 drivers.** The [FTC's complaint and consent order](https://www.ftc.gov/legal-library/browse/cases-proceedings/152-3054-1623054-uber-technologies-inc-matter) lay out the chain;
the part that turned a breach into a *case* is what came next: Uber paid the attacker $100,000 through
its bug-bounty program to stay quiet and did not disclose the breach for **about a year**, which is why
the [Department of Justice prosecuted the company's chief security officer](https://www.justice.gov/usao-ndca/pr/former-chief-security-officer-uber-convicted-federal-charges-covering-data-breach) — a
landmark conviction of a security executive for the cover-up, not the breach.

Strip away the cover-up drama and you're left with the most ordinary breach there is: **a long-lived
credential written into code.** No exploit, no zero-day — a key that should never have existed in a
form a human could copy. So before the lab, sit with the one question that makes this module's
architecture click:

> **Uber rotated the leaked AWS key after the breach. Why didn't that contain it?**

## Your job

By the end of this module you'll **find** a leaked key the way an incident responder does (`trufflehog`,
full git history), and then — the spine of the module — **build the architecture that makes the leak
expire on its own.** You'll store a secret in HashiCorp Vault *and* an AWS-native store with an
IAM-gated read; mint a **dynamic, leased** database credential that no human ever sees; have a small app
**fetch it at runtime** instead of carrying it; and **automate rotation** so even the master password
rotates itself. The deliverable is a working demonstration that the Uber leak is *architecturally
impossible*, plus the pre-commit guardrail that stops the next one at the keyboard.

## Predict it before the lab

One light call — answer it now, because the answer is the whole module:

> **Uber rotated the key after the breach. Why didn't rotation contain it?** Was the problem that they
> rotated *too slowly*, or something rotation can't fix at all?

**The reveal.** Rotation invalidates a credential *going forward* — but by the time you rotate, the
attacker has already used the old key, and **the data is already gone.** Rotation is a race you start
*after* losing. That's the defining property of a long-lived static secret: it **fails open.** It is
valid from the moment it's created until the moment a human notices, decides, and acts — and the gap
between "leaked" and "noticed" is where every credential breach lives. You cannot rotate a static key
fast enough, because the clock doesn't start when it leaks; it starts when you find out, which is often
a year later (Uber) or never. The fix is not "rotate faster." It is to **change what the credential
is**: a secret that is *short-lived and fetched on demand* fails *closed* — a leaked copy is worthless
within minutes because it expires whether or not anyone noticed. That single inversion — from
"hide a permanent secret" to "the secret is temporary by construction" — is what the rest of this
module builds.

## The build, in four moves

The lab walks these; here's the model so the steps mean something.

**1 — Find what's already leaked, and understand why deletion is a lie.** When a developer commits a
secret, panics, and "removes" it in the next commit, the key is **still in git history** — `git log -p`
and `trufflehog git` read the whole history, not just HEAD. The only safe response to a leaked
credential is *revoke and rotate*, never *delete the commit*. `trufflehog` also *verifies*: it calls the
provider's API to check whether the found key is still live. The tool finds; you triage — real or
placeholder, live or dead, who owns it.

**2 — Store it properly: encrypted at rest, gated by least privilege.** A secrets manager (Vault, or the
cloud-native AWS Secrets Manager / SSM Parameter Store) centralises secrets, encrypts them at rest, and
**puts an access-control wall in front of every read.** This already beats "in code": the Vault policy
or the IAM `Resource`-scoped read means only the app's role can fetch the secret, and every fetch is
audited. But a stored static secret is *still long-lived* — it still fails open. Storing it better is
necessary, not sufficient.

**3 — Make it leased, so a leak expires on its own.** This is the move the shipped module under-sold and
the answer to the predict prompt. Vault's **database secrets engine** mints a credential *per request*:
the app asks Vault, Vault creates a brand-new Postgres user with a **lease** (say 5 minutes), hands it
back, and **destroys the user when the lease expires.** No human types it, no file stores it, and a
leaked copy is dead in minutes — it fails *closed*. AWS's native parallel is the role itself: an
EC2/Lambda/ECS execution role *is* the credential, minted and rotated by STS with no static key at all.
Same principle, two implementations: **eliminate the long-lived static credential.**

**4 — Fetch at runtime, and rotate what's left automatically.** The app must hold *no* secret — not even
in an environment variable baked in at deploy (that's just a slower hardcode). It authenticates to the
broker at startup and *fetches* the leased credential, which expires behind it. The one long-lived secret
that remains — the master password Vault uses to mint users — **rotates itself**: `vault write
database/rotate-root` changes the Postgres admin password and keeps it to itself, so afterward *no human
knows it*. "No human knows the credential" is a strictly stronger property than "the credential is
encrypted" — you can't leak what you don't possess.

## Learn (~3.5 hrs)

*A specialist operate module — it curates more than a foundations module, because the leased-credential
mechanism is the load-bearing skill and the docs explain it better than a paraphrase would.*

**Find the leak (~1 hr)**
- [trufflehog README — truffleSecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) (~30 min) — read the scan modes (`git`, `filesystem`, `github`) and especially **verification** (it calls the provider API to check a found key is live). This is the find half end to end.
- [MITRE ATT&CK T1552.001 — Credentials In Files](https://attack.mitre.org/techniques/T1552/001/) (~15 min) — the technique you're catching; the Uber keys are the textbook example. Read the mitigations column and note that "use a secrets store" is the listed control.
- [GitGuardian — State of Secrets Sprawl 2026](https://www.gitguardian.com/state-of-secrets-sprawl-report-2026) (~15 min, skim) — the scale: ~28.6 million new secrets leaked to public GitHub commits in 2025. Skim the headline numbers; it's the "this is common, not exotic" evidence.

**Build the fix (~2 hrs)**
- [Vault — database secrets engine](https://developer.hashicorp.com/vault/docs/secrets/databases) (~30 min) — the heart of the build: Vault mints a short-lived Postgres/MySQL user per request and destroys it at lease end. Read the overview and the PostgreSQL example; this is the leased-credential mechanism the lab uses.
- [Vault — manage dynamic credential leases tutorial](https://developer.hashicorp.com/vault/tutorials/db-credentials/manage-dynamic-leases) (~45 min) — work through it hands-on: lease TTL, renew, revoke. The TTL is the whole point — it's why a leaked dynamic credential is harmless.
- [AWS — Secrets Manager rotation overview](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html) (~20 min) — the cloud-native managed-rotation pattern and the Secrets-Manager-vs-Parameter-Store decision. Read the "How rotation works" section.
- [AWS — IAM policy for Secrets Manager (`Resource`-scoped read)](https://docs.aws.amazon.com/secretsmanager/latest/userguide/auth-and-access_identity-based-policies.html) (~15 min) — how you gate a native store so *only* the app role can read *one* secret ARN — the IAM guardrail half.

**Stop the next one (~30 min)**
- [gitleaks README + pre-commit usage](https://github.com/gitleaks/gitleaks) (~30 min) — the keyboard-level guardrail: read the `pre-commit` hook section so you can block the AKIA pattern *before* it ever reaches history. Compare to trufflehog (gitleaks is faster, config-driven; trufflehog verifies live).

## Key concepts
- A static secret **fails open**: it's valid from creation until a human notices and acts — rotation is a race you start *after* losing, which is why rotating Uber's key didn't contain anything
- A **leased/dynamic** credential **fails closed**: minted per request, destroyed at lease end, so a leaked copy expires on its own — change *what the secret is*, not how well you hide it
- Git history persistence: "removing" a committed secret leaves it in history (`trufflehog git`, `git log -p`) — the only fix is revoke-and-rotate
- An env var baked in at deploy is a slower hardcode; the app must **fetch at runtime** and hold nothing
- "No human knows the credential" (auto-rotated root) > "the credential is encrypted" — you can't leak what you don't possess
- The guardrail is two-sided: a **gitleaks pre-commit hook** (stop the leak at the keyboard) + an **IAM/`Resource`-scoped read policy** (only the app role can fetch the stored secret)

## AI acceleration
Hand a model a `trufflehog` JSON finding and ask it to draft the incident ticket: which service owns the
credential type, the exact rotation steps, and how to confirm the key is no longer live. It's a fast,
strong first pass for triage — and the thing you must check is that the **rotation procedure is correct
for *that specific* credential** (rotating an AWS IAM key, a GitHub PAT, and a Postgres password are
three different procedures the model will sometimes conflate). For the build, AI is excellent at drafting
a Vault policy or a `Resource`-scoped IAM read — but verify the policy *denies* everything outside the
one path/ARN by testing it, not by reading it. The model drafts; you prove the wall holds and you own
the architecture.
