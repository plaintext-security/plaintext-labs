# Lab 17 — Data Protection with KMS: Envelope Encryption & Key Policy

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. It uses
[LocalStack](https://localstack.cloud/) to simulate AWS KMS locally — no cloud account or real
credentials required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cloud/17-data-protection-kms
make up        # start LocalStack + create the KMS key
make demo      # envelope-encrypt a file, then the key-policy separation build->verify
make shell     # drop into the lab container to work
make down      # stop when done
```

`make up` creates a KMS key (`alias/meridian-data`) and writes its id to `data/key-id.txt`. The lab
container ships `awslocal` (a drop-in for `aws` pointed at LocalStack) and `openssl`.

> Everything runs locally against a simulated AWS environment you own. No real KMS key or data.

## Scenario

Meridian Financial stores customer financial records in S3 and database snapshots on EBS. The
auditors asked a simple question the team couldn't answer: *if an attacker copies a snapshot, can
they read it — and who, exactly, can decrypt our data?* Your job is to implement data-at-rest
protection the right way: envelope-encrypt records with a KMS-managed key, then write a key policy
that separates the people who *manage* the key from the services that *use* it — so a single
compromised credential can't both read everything and destroy the key.

## Do

### Part 1: Envelope encryption — protect data at rest
1. [ ] **Run the envelope walkthrough.** `make envelope` (or `make demo`). Read each step: KMS hands
   you a data key in plaintext *and* a KMS-wrapped copy; you encrypt the data locally with the
   plaintext key, then throw it away and keep only the ciphertext + the wrapped key. KMS never sees
   your data — it only wraps the key. Why is this better than sending the whole file to KMS to encrypt?

2. [ ] **Do it by hand.** In `make shell`, mint a data key yourself:
   `awslocal kms generate-data-key --key-id $(cat data/key-id.txt) --key-spec AES_256`.
   Note the two fields: `Plaintext` (the key you use, then discard) and `CiphertextBlob` (the wrapped
   key you store). Encrypt a file with `openssl enc -aes-256-cbc -pbkdf2`, then recover it by asking
   `awslocal kms decrypt` to unwrap the key. Confirm the recovered plaintext matches.

3. [ ] **Prove the off-switch.** The wrapped data key is useless without `kms:Decrypt` on the key.
   Write one sentence in `findings.md`: if you revoke the app's `kms:Decrypt`, what happens to every
   stored object *and every backup of it* — and why is that a stronger guarantee than deleting files?

### Part 2: Key policy — separate who manages from who uses
A KMS key policy is a *resource* policy: it lists principals and the `kms:` actions they may take on
the key. The control that matters is **separation of duties** — key administrators must not be able
to decrypt data, and the app that decrypts data must not be able to delete the key.

4. [ ] **See the gap.** Run `make check-keypolicy` (the checker against the original loose policy in
   `data/key-policy.json`). Two assertions FAIL: there's no key-administrator role, and the app role
   holds `kms:*` — so one compromised app credential can read every record *and* schedule the key for
   deletion (destroying all data). Read the policy to see why.

5. [ ] **Author the separated key policy.** Edit `data/key-policy-fixed.json` (a reference solution is
   bundled — try it yourself first). Split access into two principals:
   - **`MeridianKeyAdmin`** — may manage the key (`Describe`, `Enable/Disable`, `Put`, `ScheduleKeyDeletion`, …) but **not** `Encrypt`/`Decrypt`.
   - **`MeridianAppRole`** — may `Encrypt`/`Decrypt`/`GenerateDataKey` but **not** any administrative action.
   Keep the standard `EnableRoot` statement. Grant decrypt to no wildcard principal.

6. [ ] **Prove separation holds.** Run `make check-fixed`. All five assertions must PASS: the admin
   can administer but not decrypt, the app can decrypt but not administer, and no `*` principal can
   decrypt. If an assertion flips, you over- or under-granted. Capture the before/after in `findings.md`.

7. [ ] **(Stretch in-lab) Apply and rotate.** Apply your policy to the live key
   (`awslocal kms put-key-policy --key-id $(cat data/key-id.txt) --policy-name default --policy file://data/key-policy-fixed.json`),
   then enable rotation (`awslocal kms enable-key-rotation --key-id $(cat data/key-id.txt)`) and note
   what automatic key rotation does and does *not* re-encrypt.

## Success criteria — you're done when
- [ ] You envelope-encrypted a file and recovered it by unwrapping the data key through KMS.
- [ ] You can explain why revoking `kms:Decrypt` is the real off-switch for data at rest.
- [ ] Your `key-policy-fixed.json` makes `check_keypolicy.py` exit 0 — admins can manage but not
  decrypt, the app can decrypt but not administer, and no wildcard principal can decrypt.
- [ ] `findings.md` records the before/after separation result and the data-at-rest off-switch reasoning.

## Deliverables
`findings.md` — the data-protection write-up: the envelope-encryption flow, the key-access off-switch
reasoning, and the before/after key-policy separation result. `key-policy-fixed.json` — your
separated key policy that passes the checker. Commit both. Do not commit `data/key-id.txt`, any data
keys, or plaintext/ciphertext artifacts.

## Automate & own it
**Required.** Write `envelope.py` (or extend the bundled `envelope.sh`) that takes a file path,
envelope-encrypts it (generate-data-key → encrypt locally → store ciphertext + wrapped key as one
bundle), and decrypts it back — with the plaintext data key never written to disk. Have a model draft
the boto3 KMS calls; you verify the plaintext key is zeroed/never persisted and that decrypt round-trips.
This is the core of a client-side encryption helper you'd reuse across services.

## AI acceleration
Paste a KMS key policy into a model and ask it to identify separation-of-duties violations — a
principal that can both `Decrypt` and `ScheduleKeyDeletion`, or `kms:*` granted broadly. It's good at
spotting the obvious collapse. What it can't see is your org's intended roles, so confirm each flagged
principal against who *should* manage vs. use the key, and run `check_keypolicy.py` to prove the fix.

## Connects forward
This is the data-protection counterpart to Module 07 (Secrets Management): there you kept *credentials*
out of reach; here you keep *data* unreadable without a key you control. The key-policy separation skill
is the same least-privilege reasoning as Module 02 (IAM) and Module 03 (attack paths), applied to a
resource policy. In Module 16 (Incident Response), "who could decrypt this?" is answered by the key
policy you wrote here.

## Marketable proof
> "I implement data-at-rest protection with KMS envelope encryption, and I write key policies that
> separate key administration from key use — so a single compromised credential can neither read all
> the data nor destroy the key."

## Stretch
- Configure S3 default encryption with your KMS key and confirm objects are encrypted at rest with
  `aws s3api head-object` showing `ServerSideEncryption: aws:kms`.
- Compare an AWS-managed key, a customer-managed key (CMK), and a key with imported material (BYOK):
  who controls rotation and the key policy in each, and when does the difference matter?
