# Lab 09 — Hash It, Don't Encrypt It: Crypto Primitives with openssl

*Variant D · misconception, interleaved. [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo: a small Debian +
`openssl` container, so every learner runs the exact same toolchain.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/foundations/09-cryptography
make up      # build the Debian + openssl container
make demo    # SHA-256, AES round-trip, RSA, certificate read, bit-flip
make shell   # interactive openssl shell
make down    # stop when done
```

> Only test systems you own or have explicit written permission to test. The one network step (reading
> a live certificate) only *reads* a public site's published certificate over a normal TLS connection —
> it attacks nothing. Everything else runs locally in the container.

## Scenario
You're the engineer who has just read the Adobe post-mortem and been told "store our passwords
properly." Before you can fix it, you need each primitive to be *concrete*, not a word — so you'll
exercise all four with `openssl`, then reproduce the Adobe failure in miniature and the correct fix
beside it. The deliverable is `crypto-notes.md`: one honest line per primitive, plus a side-by-side
showing **why ECB leaks and salt fixes it.**

Each step runs the same rhythm: **Predict** (commit before you run it) → **Do** (run the command) →
**Reveal** (what it proves) → **Record** (one line in the notes). Look the exact invocations up in the
OpenSSL Cookbook — choosing the right subcommand and flags is part of the lesson.

## Do

1. [ ] **Hashing — the one-way fingerprint.**
   **Predict:** if you hash the same message twice, do you get the same digest? If you change one
   character, how much of the digest changes?
   **Do:** produce a **SHA-256** digest of a short message, then hash it again, then hash a
   one-character edit of it. **Reveal:** identical input → identical digest (it's deterministic), but a
   one-char change rewrites the whole digest (the *avalanche* effect) — and there is no command to turn
   a digest back into the message. **Record:** "hash = one-way fingerprint; proves integrity, not
   secrecy."

2. [ ] **Symmetric encryption — data you need back.**
   **Predict:** with one shared key, can you both lock and unlock the message?
   **Do:** encrypt the message with **AES** and decrypt it back — a full round-trip. (Use a
   key-derivation flag so a passphrase works.) **Reveal:** same key encrypts and decrypts; this is the
   *reversible* tool — exactly what Adobe used, and exactly what a password storage system must **not**.
   **Record:** "symmetric = one shared key, reversible; for data you need to read again."

3. [ ] **Asymmetric encryption — the keypair.**
   **Predict:** if the *public* key encrypts, which key decrypts?
   **Do:** generate an **RSA** keypair, encrypt a short message with the public key, decrypt with the
   private key. **Reveal:** only the private-key holder can decrypt — this is what lets a stranger send
   you a secret and what underpins certificates. **Record:** "asymmetric = a keypair; public encrypts /
   private decrypts; enables signatures + TLS."

4. [ ] **Certificates — who vouches for the server.**
   **Do:** pull a real website's certificate over TLS and read its **issuer**, **subject**, and
   **validity dates**. **Reveal:** the *issuer* is the Certificate Authority your OS/browser already
   trusts; that signature is why you believe the server is who it claims. **Record:** "certificate =
   asymmetric keys + a CA's signature = the chain of trust behind HTTPS."

5. [ ] **Reproduce the Adobe failure — and the fix.** This is the heart of the lab.
   **Predict:** if you encrypt two *identical* passwords in **ECB** mode with the same key, will the two
   ciphertexts look the same or different? What about hashing them **with a unique salt each**?
   **Do:** encrypt the same short string twice with `openssl enc -aes-128-ecb` (same key, no salt) and
   compare the outputs. Then salt-and-hash the same string twice (prepend a different random salt each
   time, then SHA-256) and compare those. **Reveal:** the ECB ciphertexts are **identical** — that's the
   pattern leak that let researchers cluster Adobe's 153M rows; the salted hashes are **different** —
   that's the fix. **Record:** the two pairs, side by side, with one line: *"ECB: same in, same out
   (leaks); salted hash: same in, different out (safe)."*

6. [ ] **(Optional) Tamper check.** Flip a single byte of the AES ciphertext from step 2 and try to
   decrypt — observe that plain CBC produces garbage but doesn't *detect* the change, which is why
   authenticated encryption (AES-GCM) exists. **Record:** one line on "encrypted ≠ authenticated."

## Success criteria — you're done when
- [ ] You produce a SHA-256 digest and can say in one sentence why it proves integrity but not secrecy.
- [ ] You round-trip a message through both AES (symmetric) and RSA (asymmetric).
- [ ] You can read a certificate's issuer, subject, and validity, and name who vouches for it.
- [ ] **You reproduced the Adobe failure:** two identical inputs in ECB give identical ciphertext, while
  two salted hashes of the same input differ — and you can explain why that distinction sank Adobe.
- [ ] You scored your "Call it" prediction from the README against the reveal.

## Deliverables
`crypto-notes.md` — one line per primitive (what it guaranteed), the side-by-side ECB-vs-salted-hash
result from step 5, and a one-line verdict: *why a password must be hashed-and-salted, never encrypted.*
This is the Adobe lesson in your own words. Commit it. Do **not** commit keys, ciphertext blobs, or any
real passwords.

## Automate & own it
**Required — a small reviewable script.** Turn the lesson into a tiny tool `hash_and_verify.py`: it
takes a password, generates a **random salt**, computes a salted hash, and stores `salt:hash`; a
`verify` mode takes a candidate password and the stored `salt:hash` and prints **match / no match** —
*without ever storing the password itself.* This is, in miniature, what Adobe should have built. Run it
to confirm the same password with two different salts produces two different stored hashes. Have a model
draft it; **review every line** — confirm it never logs or returns the plaintext, and confirm the salt
is actually random per call — and commit *your* reviewed version. (Standard library only: `hashlib` +
`secrets` + `hmac.compare_digest` for the comparison.)

## AI acceleration
Ask a model *why* Adobe's ECB-encrypted passwords were crackable and what they should have used — then
audit the answer against this module. It usually names "ECB is bad" but is fuzzier on the deeper fix
(hash, don't encrypt; salt per user). Then paste in your `hash_and_verify.py` and ask it to find a flaw
— a non-constant-time comparison, a reused salt, the plaintext leaking into a log — and harden it.

## Connects forward
This underpins the Cloud track (TLS and secrets), the Crypto/PKI track (certificates and key management
in depth), and the Web track (session and password handling). The salted-hash check you wrote is the
"check crypto the right way" step of the Foundations capstone.

## Marketable proof
> "I can exercise and audit the core crypto primitives with openssl — hashing, AES, RSA, and a live
> certificate chain — and I can explain, with a reproduced ECB-vs-salted-hash demo, exactly why Adobe's
> 153M 'encrypted' passwords were crackable and why a password must be hashed and salted, not encrypted."

## Stretch
- Replace the SHA-256 in `hash_and_verify.py` with a *real* password hash (bcrypt or Argon2 via a
  library) and explain what "slow by design" buys you that a fast hash like SHA-256 does not.
- Redo the symmetric step with `-aes-256-gcm` (authenticated encryption) and explain what the
  authentication tag detects that plain CBC silently misses.
