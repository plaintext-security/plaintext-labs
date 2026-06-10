# Lab 01 — Primitives in Practice

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/01-primitives-practice
make up        # build the OpenSSL container
make demo      # encrypt with AES-CBC, then AES-GCM; show tamper detection
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs offline in a container you own. No external dependencies.

## Scenario

Meridian Financial's development team is debating whether to use AES-CBC or AES-GCM for
encrypting customer data at rest. Before the architecture review, your job is to demonstrate
concretely what guarantee each mode provides — including what an attacker can do to CBC that
they cannot do to GCM — so the team makes an informed choice.

## Do

1. [ ] Attempt the experiment first, then run `make demo` to check your prediction. Before
   running it, write down what you *expect* to happen when a ciphertext byte is flipped under
   CBC vs under GCM. Then compare against the demo.

2. [ ] `make shell` and encrypt `/lab/data/plaintext.txt` under AES-256-CBC. The `openssl enc`
   invocation is the syntax worth seeing once — supply a 256-bit key and a 128-bit IV as hex:
   ```bash
   openssl enc -aes-256-cbc -in /lab/data/plaintext.txt -out /tmp/cipher-cbc.bin \
     -K <64-hex-char key> -iv <32-hex-char IV>
   ```
   Now flip a byte inside the second ciphertext block, decrypt the tampered file, and record
   what comes out. Did decryption *succeed*? What does that tell you about CBC's integrity
   guarantee?

3. [ ] Encrypt the same plaintext under AES-256-GCM (same `enc` form, different cipher and a
   96-bit IV). Flip a ciphertext byte the same way and attempt to decrypt. What does OpenSSL do
   differently from the CBC case, and what is that behaviour called?

4. [ ] Document the difference: write two paragraphs in `primitives-analysis.md`:
   - What happened when you tampered with the CBC ciphertext, and what this means for Meridian's data-at-rest design.
   - What happened when you tampered with the GCM ciphertext, and why this is the correct guarantee.

5. [ ] Compute an HMAC of the plaintext with OpenSSL (`openssl mac … HMAC`). Then explain in
   your notes: how does a MAC-then-encrypt construction differ from AES-GCM's built-in
   authentication, and which ordering — Encrypt-then-MAC or MAC-then-Encrypt — is the safe
   default, and why?

## Success criteria — you're done when

- [ ] You observed CBC silently decrypting tampered ciphertext.
- [ ] You observed GCM returning an authentication error on tampered ciphertext.
- [ ] You documented the difference in `primitives-analysis.md` with a recommendation.
- [ ] You computed an HMAC and can explain the MAC-then-encrypt vs AEAD distinction.

## Deliverables

`primitives-analysis.md` — your two-paragraph CBC vs GCM analysis plus the HMAC comparison.
Commit it.

## Automate & own it

**Required.** Write a Python script `encrypt-aead.py` that: takes a plaintext file and a key,
encrypts with AES-256-GCM using the `cryptography` library (not OpenSSL subprocess), and
outputs the IV, tag, and ciphertext as a JSON object. Have an AI draft the script using
`cryptography.hazmat.primitives`; you verify the IV is randomly generated (not hardcoded) and
the tag is included in the output before committing.

## AI acceleration

Ask an AI: "What is the difference between AES-CBC and AES-GCM from an attacker's perspective?"
Use the answer to check your own CBC tamper experiment against the explanation. Then ask a
follow-up: "What is the Padding Oracle attack on CBC?" — and verify the explanation against the
OWASP Padding Oracle page before including any claims in your deliverable.

## Connects forward

The AEAD guarantee you observed here is the foundation for module 02 (Symmetric & AEAD) which
explores IV reuse attacks, and module 05 (TLS Deep Dive) where GCM is the dominant cipher suite
in TLS 1.3. Module 10 (Auditing Applied-Crypto Failures) returns to these failure modes in the
context of real-world findings.

## Marketable proof

> "I demonstrated the concrete security difference between AES-CBC and AES-GCM by tampering
> with ciphertexts — showing CBC's silent corruption failure and GCM's authentication check —
> and wrote an architecture recommendation for Meridian's data-at-rest design."

## Stretch

- Encrypt the same plaintext with AES-128-ECB and look at the output for a structured input
  (e.g. a file with repeated 16-byte blocks). Observe the identical ciphertext blocks. This is
  the visual proof that ECB mode is broken.
- Research the difference between GCM authentication tag sizes (96-bit vs 128-bit) and when
  a truncated tag is acceptable. Write one paragraph on the trade-off.
