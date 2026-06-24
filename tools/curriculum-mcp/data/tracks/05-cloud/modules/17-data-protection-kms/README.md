# Module 17 — Data Protection & KMS

*Type 7 · Build-&-Operate (+ Type 3 · Blast-Radius) — build envelope encryption and a scoped key policy, then prove who can actually use the key. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *"encrypted at rest" is a checkbox; "who can use the key" is the control. Build the second one.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 01 — Shared Responsibility](../01-cloud-fundamentals/README.md) · [Module 02 — Cloud Identity & IAM](../02-cloud-identity-iam/README.md)
{ .module-meta }


## Why this matters

Back in [Module 01](../01-cloud-fundamentals/README.md), the Capital One autopsy turned on a line that
sounds impossible: the 100 million records were **encrypted at rest**, and the attacker read every one
of them in plaintext anyway. The DOJ indictment and the Senate report don't describe a broken cipher or
a stolen disk — they describe an over-broad IAM role that the account had *authorized* to read the data,
so the storage layer decrypted it transparently on the way out. ([DOJ indictment](https://www.justice.gov/usao-wdwa/press-release/file/1188626/download),
[US Senate report](https://www.hsgac.senate.gov/wp-content/uploads/imo/media/doc/Capital%20One%20Report.pdf).)

That is the whole reason this module exists. "Is it encrypted?" is the question auditors ask and
dashboards answer; it is almost never the question that decides a breach. **Encryption at rest is silent
against any principal you let use the key** — and in the cloud, "who can use the key" is itself a policy
you write, in two places, that most teams never read. This module is build-first: you'll stand up real
envelope encryption and then author the key policy that actually decides who can decrypt — turning
Module 01's reveal from a thing you *understood* into a thing you *built*.

## Objective

Build envelope encryption against a real KMS (LocalStack), then author and verify a key policy that
separates who *manages* the key from who *uses* it — and prove, with a checker, that an over-broad
policy fails and your scoped one passes. Walk away able to answer the auditor's real question: *who,
exactly, can decrypt our data?*

## The core idea

**Envelope encryption: KMS wraps a key, never your data.** A KMS key (a CMK) never touches your files.
You ask KMS for a *data key* and it hands back two things: the key in **plaintext** (you encrypt your
data with it locally, then throw it away) and the same key **KMS-wrapped** (you store this next to the
ciphertext). To read the data later, you send the wrapped key back and KMS unwraps it. The payoff is
the off-switch: every object — and *every backup of it* — is unreadable without `kms:Decrypt` on that
one key. Revoke decrypt and the data is gone-to-them without touching a single file. That is a stronger
guarantee than deleting files, and it's the mental model to keep: **the key, not the file, is the thing
you actually control.**

**Two doors lead to a key, and people only guard one.** Access to a KMS key is governed by *both* the
principal's **IAM policy** *and* the key's own **key policy** (a resource policy attached to the key
itself). This is the load-bearing gotcha and where intuition from Module 02 needs an update: for most
AWS resources IAM is the whole story, but **KMS is different — by default the key policy is the root of
authority, and an IAM grant only takes effect if the key policy also delegates to IAM.** So you can
write a perfect least-privilege IAM policy and still leak the key, because a permissive key policy
opened a second door you never looked at. The Capital One lesson, made precise: it wasn't "encryption
failed," it was that *something with a door to the key walked through it.* Auditing data protection
means auditing **both** doors — the IAM policy and the key policy — for every key. (See AWS's own
[Key policies in AWS KMS](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html) and
[Key policies vs. IAM policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html).)

**Grants are the third, temporary door — scoped to who can *use* the key.** Beyond the two static
policies, KMS [**grants**](https://docs.aws.amazon.com/kms/latest/developerguide/grants.html) hand a
specific principal a narrow, often time-bound set of *usage* operations (`Encrypt`, `Decrypt`,
`GenerateDataKey`) — the mechanism AWS services use to decrypt on your behalf without a standing policy
entry. They matter here because they're the cleanest expression of the whole module's thesis:
protection isn't "is it encrypted," it's **the exact set of principals that can use the key**, and a
grant is that set written down.

**The judgment that makes a key policy good: separation of duties.** The people who *manage* the key
(rotate it, disable it, schedule it for deletion) must **not** be able to decrypt data; the app that
*decrypts* data must **not** be able to delete the key. Collapse them — grant one role `kms:*` — and a
single compromised credential can both read every record *and* destroy the key (and with it, every
backup). The fix is two principals: a `KeyAdmin` with the administrative actions and no decrypt, and an
`AppRole` with usage and no administration — and decrypt granted to *no* wildcard principal. That split,
not the cipher, is what you build and verify in the lab.

**Default encryption is table stakes, not the control.** Turn on default encryption for S3, EBS, and
snapshots so nothing lands unencrypted by accident — it's free and you should — but treat it as the
*baseline that prevents the silly mistake*, not as protection. It defends against the stolen-disk
threat and nothing else. Rotation is the same shape: enabling rotation re-wraps *future* data keys
under new key material but does **not** re-encrypt data already at rest, so it limits exposure window,
it doesn't undo a leak. The control that decides a breach remains: who can use the key.

## Learn (~3 hrs)

*Build-first: read enough to author the key policy and the envelope flow well, then do it. Go to the
primary AWS docs for the mechanism, and pair them with the Capital One sources so the "encrypted ≠
protected" point stays concrete.*

**The two-door model — read this first (~1 hr)**
- [AWS — Key policies in AWS KMS](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html) (~25 min) — the primary source. Read why a key policy is *required* on every key and why it, not IAM, is the root of authority for KMS. This is the door Module 02's IAM reasoning doesn't cover.
- [AWS — Using key policies + IAM (default key policy)](https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html) (~20 min) — the exact rule: an IAM grant only reaches a key if the key policy delegates to IAM. Read the "Allows access to the AWS account and enables IAM policies" section — it's the precise mechanism behind "two doors."
- [AWS — Grants in AWS KMS](https://docs.aws.amazon.com/kms/latest/developerguide/grants.html) (~15 min, skim) — the temporary third door; read the operations list and the "for what" so you can tell a grant from a policy entry.

**Envelope encryption — the mechanism you build (~45 min)**
- [AWS — How envelope encryption works](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#enveloping) (~20 min) — the primary description of the data-key dance (plaintext key for local use, wrapped key for storage); read it before running `make demo` so the script confirms what you read.
- [AWS — `generate-data-key` (CLI reference)](https://docs.aws.amazon.com/cli/latest/reference/kms/generate-data-key.html) (~15 min) — the one call the whole envelope flow turns on; note the two return fields, `Plaintext` and `CiphertextBlob`.

**The "encrypted didn't matter" anchor (~30 min)**
- [Krebs on Security — what we can learn from the Capital One hack](https://krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/) (~20 min) — re-read with this module's lens: the data was encrypted; the over-broad authorized role is why that didn't help. The clearest public walk-through, and it corroborates the DOJ/Senate primaries cited above.
- [AWS — default encryption for S3 buckets](https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html) (~10 min, skim) — the baseline-not-control setting; read what it does and, crucially, what it does *not* defend against.

## Key concepts
- Envelope encryption: KMS wraps a **data key**, never your data — the wrapped key + ciphertext are stored together; only `kms:Decrypt` unwraps it
- The real off-switch for data at rest is **revoking key access**, not deleting files — it makes every object and every backup unreadable at once
- **Two doors to a key:** the principal's IAM policy *and* the key's resource policy — and for KMS the key policy is the root of authority; auditing means checking both
- KMS **grants** are a narrow, often temporary third door scoped to *usage* (`Encrypt`/`Decrypt`/`GenerateDataKey`) — protection is the exact set of principals who can use the key
- A good key policy enforces **separation of duties**: key admins can manage but not decrypt; the app can decrypt but not administer; no wildcard principal can decrypt
- Default encryption (S3/EBS/snapshots) and rotation are baseline hygiene, not the control — rotation re-wraps future keys, it does **not** re-encrypt data already at rest
- The Capital One lesson, precise: **encrypted ≠ protected** — encryption at rest is silent against a principal you authorized to use the key

## AI acceleration
Paste a KMS key policy into a model and ask it to find separation-of-duties violations — a principal
that can both `Decrypt` and `ScheduleKeyDeletion`, or `kms:*` granted to an app role. It's good at the
obvious collapse. Two things it can't do for you: it sees one document, so it can't tell you whether an
IAM policy or a grant opens a *second* door to the key (the whole point of this module), and it doesn't
know your org's intended roles — *should* this principal manage the key, or use it? Treat every flag as a
hypothesis, confirm it against who-should-do-what, and run `check_keypolicy.py` to prove the fix. You
direct it; you own the verdict on who can use the key.
