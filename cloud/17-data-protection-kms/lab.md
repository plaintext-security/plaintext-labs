# Lab 17 — Data Protection with KMS: Envelope Encryption & Key Policy

> **Hands-on lab.** Environment: `plaintext-labs/cloud/17-data-protection-kms` (runs on **floci**, a
> free local AWS emulator — no cloud account). Objective: **build real envelope encryption, then author
> a key policy that separates who manages the key from who uses it — and prove it with a checker.**
> Target: **~90 min**, one finish line. [← Back to the module concept](README.md)

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **KMS wraps a *data key*, never your data.** | `GenerateDataKey` hands you a plaintext key (use locally, then shred) + a KMS-wrapped copy (store it). KMS never sees the file. |
| 2 | **Revoking `kms:Decrypt` is the real off-switch.** | Every object *and every backup* is unreadable without it — a stronger guarantee than deleting files. |
| 3 | **A key has two doors: IAM policy *and* key policy.** | For KMS the **key policy is the root of authority**; an IAM grant only reaches the key if the key policy delegates to IAM. Audit both. |
| 4 | **Encryption at rest is silent against an authorized principal.** | Capital One's records were encrypted and read anyway — the failed control was **identity**, not the cipher. |
| 5 | **A good key policy enforces separation of duties.** | Admins manage but can't decrypt; the app decrypts but can't destroy the key; no wildcard principal gets decrypt. |
| 6 | **Default encryption + rotation are baseline, not the control.** | Rotation re-wraps *future* data keys — it does **not** re-encrypt data already at rest. Who-can-use-the-key still decides the breach. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) (envelope flow + the two-door model) and the primary
> [Key policies in AWS KMS](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. You wrote a flawless least-privilege **IAM** policy for a KMS key, and the data is still reachable.
   Which second door did you forget to check, and why is it the root of authority for KMS?
2. Envelope encryption asks KMS for a *data key* instead of sending the file to KMS. Name the two things
   `GenerateDataKey` returns — and which one you keep on disk.

---

## Setup

This is a **reference lab** — a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[floci](https://github.com/floci-io/floci), a free, MIT-licensed local AWS emulator, to simulate AWS
KMS on `localhost:4566` — no cloud account or real credentials. (floci replaces LocalStack, whose
community edition sunset in March 2026.)

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/17-data-protection-kms
make up        # start floci + create the KMS key (alias/data)
make demo      # envelope-encrypt a file, then the key-policy separation FAIL -> PASS
make shell     # drop into the lab container to work by hand
make down      # stop when done
```

`make up` creates a KMS key (`alias/data`) and writes its id to `data/key-id.txt`. The lab container
ships the AWS CLI (plain `aws`, pointed at floci via `AWS_ENDPOINT_URL`) and `openssl`.

> **▸ On track if:** `make up` finishes with `KMS key ready: <id>  (alias/data)` and `data/key-id.txt`
> exists — the key is seeded and the lab is live.

!!! warning "What this lab enforces — and what it doesn't (floci honesty)"
    floci simulates the KMS **API** (create-key, generate-data-key, encrypt/decrypt), not AWS's full
    IAM/key-policy **enforcement** — a disallowed call won't bounce on its own. So the envelope roundtrip
    is *real* (KMS actually wraps and unwraps your data key), but separation of duties is proven by
    **evaluating the key policy logically** with `check_keypolicy.py` — the same allow/deny logic AWS
    applies — not by relying on the simulator to deny a call. Because the lab drives plain `aws` via
    `AWS_ENDPOINT_URL`, the *identical* steps later run against a **real AWS account you own** to watch
    AWS enforce the policy live. **True key-policy enforcement requires real AWS; here you prove the
    policy is correct.**

> **Authorization note.** Only test systems you own or have written permission to test. Everything here
> runs locally against a simulated account you own — no real KMS key or data.

---

## Scenario

An account stores customer financial records in S3 and database snapshots on EBS. Auditors asked a
question the team couldn't answer: *if an attacker copies a snapshot, can they read it — and who,
exactly, can decrypt our data?* The data is already "encrypted at rest," which is exactly the trap from
[Module 01](../01-cloud-fundamentals/README.md): encryption is silent against a principal you
authorized to use the key. Your job is to implement data-at-rest protection the way that actually
decides a breach — envelope-encrypt records with a KMS-managed key, then write a key policy that
separates the people who *manage* the key from the services that *use* it, so a single compromised
credential can neither read everything nor destroy the key.

---

## Build it — read a little, do a little

### Step 1 — Envelope-encrypt a file, roundtrip through KMS

**Concept (30 sec):** Flight-card #1. KMS never sees your data — you ask it for a data key, encrypt
locally, then store ciphertext + the *wrapped* key.

**Do it:** run the walkthrough, then do it by hand.
```bash
make envelope        # or: make demo (also runs the key-policy check below)
```
Then in `make shell`, mint a data key yourself and roundtrip one file:
```bash
aws kms generate-data-key --key-id $(cat data/key-id.txt) --key-spec AES_256 \
  --query '[Plaintext,CiphertextBlob]' --output text
# note the two fields: Plaintext (use, then discard) + CiphertextBlob (the wrapped key you keep)
```
Encrypt a file with `openssl enc -aes-256-cbc -pbkdf2`, then recover it by asking `aws kms decrypt` to
unwrap the wrapped key. Why is this better than sending the whole file to KMS to encrypt?

> **▸ On track if:** `make envelope` ends with the **recovered plaintext matching the original**
> (`ACCOUNT=ACC-001 … SSN=…`), and by hand `generate-data-key` returns **both** `Plaintext` and
> `CiphertextBlob`. The envelope roundtrip succeeds. **Record** one line in `findings.md`: KMS wrapped
> the key, never the data.

### Step 2 — Prove the off-switch

**Concept (30 sec):** Flight-card #2. The wrapped data key is useless without `kms:Decrypt` on the key.

**Do it:** reason about revoking the app's `kms:Decrypt`.

> **▸ On track if:** you can state in one sentence, in `findings.md`, that revoking `kms:Decrypt` makes
> every stored object **and every backup of it** permanently unreadable — a stronger off-switch than
> deleting files, because you never have to find every copy.

### Step 3 — See the gap: the loose key policy fails separation

**Concept (30 sec):** Flight-card #3 + #5. A KMS key policy is a *resource* policy — the second door.
The loose `data/key-policy.json` grants `AppRole` `kms:*` and has no admin role at all.

**Do it:**
```bash
make check-keypolicy    # runs check_keypolicy.py against data/key-policy.json
```
Read the policy to see why each assertion lands where it does.

> **▸ On track if:** the checker prints **2 assertion(s) FAILED** and exits non-zero — the *key admin
> can administer* assertion FAILs (no `KeyAdmin` exists) and the *app CANNOT administer* assertion FAILs
> (`AppRole` holds `kms:*`, so one compromised app credential can read every record **and**
> `ScheduleKeyDeletion`). That collapse **is** the finding.

### Step 4 — Author the separated key policy

**Concept (30 sec):** Flight-card #5. Split usage from administration across two principals.

**Do it:** edit `data/key-policy-fixed.json` (a reference solution is bundled — try it yourself first):
- **`KeyAdmin`** — may manage the key (`Describe`, `Enable/Disable`, `Put`, `ScheduleKeyDeletion`, …) but **not** `Encrypt`/`Decrypt`.
- **`AppRole`** — may `Encrypt`/`Decrypt`/`GenerateDataKey` but **not** any administrative action.
- Keep the standard `EnableRoot` statement. Grant decrypt to **no** wildcard principal.

```bash
make check-fixed        # runs check_keypolicy.py against data/key-policy-fixed.json
```

> **▸ On track if:** the checker prints **All assertions PASS** and exits 0 — the admin can administer
> but not decrypt, the app can decrypt but not administer, and no `*` principal can decrypt. If an
> assertion flips, you over- or under-granted. **Record** the before/after in `findings.md`.

### Step 5 — (Stretch in-lab) Apply and rotate

**Do it:** apply your policy to the live key and enable rotation:
```bash
aws kms put-key-policy --key-id $(cat data/key-id.txt) --policy-name default \
  --policy file://data/key-policy-fixed.json
aws kms enable-key-rotation --key-id $(cat data/key-id.txt)
```

> **▸ On track if:** you can state what automatic key rotation **does** (re-wraps *future* data keys
> under new material) and **does not** (re-encrypt data already at rest) — the Flight-card #6 point.

---

## Prove the control (your finish line)

One finish line, two halves — both re-checked against the honesty bar:

1. **The envelope roundtrip succeeds.** `make envelope` recovers the exact plaintext by unwrapping a
   KMS-generated data key. You can explain why revoking `kms:Decrypt` is the real off-switch for data
   at rest (the wrapped key + every backup go dark at once).
2. **The separation-of-duties argument holds as code.** `check_keypolicy.py` **fails** the loose
   `data/key-policy.json` (exit 1, 2 FAILs) and **passes** your `data/key-policy-fixed.json` (exit 0,
   all PASS): admins manage but can't decrypt, the app decrypts but can't administer, no wildcard gets
   decrypt. **Caveat, stated in the write-up:** floci proves the policy is *correct*; only a real AWS
   account you own proves AWS *enforces* it — the identical `aws` steps run there unchanged.

If the check doesn't flip FAIL→PASS between the two policies, the separation isn't yet real.

---

## Recall check — close the doc, answer from memory (3 min)

1. Capital One's records were encrypted at rest and read in plaintext anyway. What was the actually-failed
   control, and why was the cipher irrelevant?
2. You wrote a flawless least-privilege IAM policy for a KMS key and the data is still reachable. Name
   the second door and why it, not IAM, is the root of authority for KMS.
3. What separation-of-duties split must a good key policy enforce, and what single-credential disaster
   does collapsing it (`kms:*` to the app role) invite?

---

## Success criteria — you're done when

- [ ] You envelope-encrypted a file and recovered it by unwrapping the data key through KMS (`make envelope` roundtrips).
- [ ] You can explain why revoking `kms:Decrypt` is the real off-switch for data at rest.
- [ ] Your `key-policy-fixed.json` makes `check_keypolicy.py` exit 0 — admins can manage but not
  decrypt, the app can decrypt but not administer, and no wildcard principal can decrypt.
- [ ] `findings.md` records the before/after separation result, the off-switch reasoning, and the
  real-AWS enforcement caveat.

These are observable and self-checked — this is an honor-system lab with no grader. The signal is
concrete: `check_keypolicy.py` exits non-zero on the loose policy and zero on your fix.

## Deliverables

`findings.md` — the data-protection write-up: the envelope-encryption flow, the key-access off-switch
reasoning, and the before/after key-policy separation result (with the "floci proves correct, real AWS
proves enforced" caveat noted). `key-policy-fixed.json` — your separated key policy that passes the
checker. Commit both. Do not commit `data/key-id.txt`, any data keys, or plaintext/ciphertext artifacts.

## Automate & own it

**Required — this is the guardrail you walk away with.** The separation check shouldn't live in your
head; encode it. Use the bundled `check_keypolicy.py` as your key-policy guardrail: it evaluates a
fixed matrix of `(principal, action)` assertions against any key policy and **fails (exit 1) on an
over-broad policy and passes (exit 0) on the scoped one** — proven both ways against
`data/key-policy.json` and your `data/key-policy-fixed.json`. Wire it into CI so a key policy that
collapses admin and usage into one principal can never merge. (Optionally extend it: add an assertion
for your own roles, or flag any statement that grants `kms:*` to a non-root principal.)

For the envelope side, write `envelope.py` (or extend the bundled `envelope.sh`) that takes a file
path, envelope-encrypts it (generate-data-key → encrypt locally → store ciphertext + wrapped key as
one bundle), and decrypts it back — with the plaintext data key never written to disk. Have a model
draft the boto3 KMS calls; you verify the plaintext key is zeroed/never persisted and that decrypt
round-trips. **AI drafts → you review every line → you own it.**

## Definition of done (`data-protection-kms` ✅)

- [ ] `make envelope` roundtrips a file: KMS-generated data key → local encrypt → unwrap → exact plaintext recovered.
- [ ] `check_keypolicy.py` prints 2 FAILs on `data/key-policy.json` and all PASS on your `data/key-policy-fixed.json`.
- [ ] `findings.md` states the off-switch reasoning, the two-door model, and the real-AWS enforcement caveat.
- [ ] The guardrail is wired so a `kms:*`-to-app-role key policy can't merge.
- [ ] You can explain all six flight-card facts cold.

## AI acceleration

Paste a KMS key policy into a model and ask it to identify separation-of-duties violations — a
principal that can both `Decrypt` and `ScheduleKeyDeletion`, or `kms:*` granted broadly. It's good at
spotting the obvious collapse. What it can't see is your org's intended roles, or whether a *second*
door (an IAM policy or a grant) opens access the key policy alone doesn't show — so confirm each
flagged principal against who *should* manage vs. use the key, and run `check_keypolicy.py` to prove
the fix.

## Connects forward

This is the data-protection counterpart to Module 07 (Secrets Management): there you kept *credentials*
out of reach; here you keep *data* unreadable without a key you control. The key-policy separation skill
is the same least-privilege reasoning as Module 02 (IAM) and Module 03 (attack paths), applied to a
resource policy — the second door to the key. In Module 16 (Incident Response), "who could decrypt
this?" is answered by the key policy you wrote here.

## Marketable proof

> "I implement data-at-rest protection with KMS envelope encryption, and I write key policies that
> separate key administration from key use — so a single compromised credential can neither read all
> the data nor destroy the key. I ship the separation check as a CI guardrail."

## Stretch

- Configure S3 default encryption with your KMS key and confirm objects are encrypted at rest with
  `aws s3api head-object` showing `ServerSideEncryption: aws:kms`.
- Compare an AWS-managed key, a customer-managed key (CMK), and a key with imported material (BYOK):
  who controls rotation and the key policy in each, and when does the difference matter?
