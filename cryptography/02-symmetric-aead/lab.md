# Lab 02 — Symmetric & AEAD

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/02-symmetric-aead
make up        # build the Python + OpenSSL container
make demo      # show CBC bit-flip, GCM authentication, and IV reuse attack
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs offline. No external dependencies.

## Scenario

Meridian's security audit team found a code path in the payroll API that reuses a hardcoded IV
for AES-GCM encryption. Before the developer team disputes the severity, your job is to
demonstrate concretely — in a controlled environment — what an attacker can do with two
ciphertexts encrypted under the same key and IV. Then implement the correct fix.

## Do

1. [ ] `make demo` — observe three demonstrations: (1) CBC bit-flip: an attacker modifies one
   block of CBC ciphertext and the next block decrypts to garbage — the confidentiality is
   corrupted but decryption succeeds. (2) GCM authentication: a tamper is detected. (3) GCM
   IV reuse: two ciphertexts with the same key/IV are XORed to reveal plaintext.

2. [ ] `make shell` and reproduce the IV-reuse attack yourself with the `cryptography`
   library's `AESGCM`. Encrypt two different short messages under the *same* key and IV, then
   XOR the two ciphertexts and XOR the two plaintexts. What relationship holds between the two
   results, and what can an attacker who knows one plaintext now do to the other?

3. [ ] Implement the fix: a random IV per encryption, serialised alongside the ciphertext
   (the IV is not secret — work out why it can travel in the clear). Confirm a fresh IV is
   generated on every call.

4. [ ] Add Associated Data to the GCM call, then attempt to decrypt with the AAD changed.
   What happens, and what threat does authenticating-but-not-encrypting the AAD defend against?
   Write a one-paragraph explanation.

5. [ ] Repeat the XOR experiment from step 2 against your fixed (random-IV) version. Confirm
   the ciphertext-XOR relationship no longer leaks plaintext, and explain why.

## Success criteria — you're done when

- [ ] You demonstrated the IV reuse attack produces `xor_ct == xor_pt`.
- [ ] You implemented the correct random-IV pattern and confirmed it's unique per call.
- [ ] You added and tested AAD and can explain what it protects against.
- [ ] You understand why `ct1 XOR ct2 = pt1 XOR pt2` when the IV is reused.

## Deliverables

`aead-demo.py` — a script that demonstrates the IV reuse attack *and* the correct fix, with
comments explaining each step. Commit it.

## Automate & own it

**Required.** Write a Python script `check-iv-reuse.py` that takes a JSONL file of `{iv, ct}`
records and checks for duplicate IVs — flagging any reused IV as a critical finding. Have an
AI draft the duplicate-detection logic; you verify it handles the case of two identical IVs in
a large file correctly, and that it is case-insensitive to hex encoding.

## AI acceleration

Ask an AI: "Explain crib-dragging on XORed plaintexts — if I know that pt1 starts with
'Salary:', what can I recover about pt2?" Use the answer to extend the attack demo: add a
crib-drag step that recovers the salary amount from the XOR output. Verify the arithmetic
manually before committing.

## Connects forward

The IV uniqueness requirement and AAD concept you practiced here appear in TLS 1.3's record
layer (module 05) — TLS uses a sequence number as the nonce, ensuring uniqueness per session.
Module 10 (auditing crypto failures) returns to IV reuse as a real audit finding.

## Marketable proof

> "I demonstrated the GCM nonce-reuse attack — showing two same-IV ciphertexts XOR to reveal
> plaintext — and implemented the correct random-IV pattern with associated data authentication."

## Stretch

- Implement ChaCha20-Poly1305 encryption using the `cryptography` library and encrypt the same
  message. Compare the ciphertext size, the nonce size, and the API to AES-GCM. When would you
  choose ChaCha20-Poly1305 over AES-GCM?
- Research XSalsa20 and NaCl/libsodium's `secretbox`. How does libsodium's API prevent nonce
  reuse compared to a raw GCM API call? What is its nonce size and why?
