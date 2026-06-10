# Module 01 — Primitives in Practice

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *Every cryptographic system is built from a small set of primitives — choose the wrong one and the system is broken before you write a line of code.*

## Why this matters

Cryptography failures are in the OWASP Top 10 every year — not because cryptographers are rare, but because developers reach for the nearest API without understanding what guarantee it provides. AES-ECB is deterministic and leaks patterns; HMAC-MD5 is still technically a MAC but its collision resistance is gone; RSA with PKCS#1 v1.5 padding is vulnerable to Bleichenbacher's attack. The misuse patterns are predictable precisely because the underlying guarantee of each primitive is not well understood. This module builds the working mental model: what each primitive does, what it does not do, and how you know which one a situation calls for.

## Objective

Use OpenSSL to encrypt, decrypt, and authenticate data using the three foundational primitives — symmetric encryption, authenticated encryption, and asymmetric operations — and observe concretely what guarantee each provides and where it fails.

## The core idea

Cryptographic primitives are building blocks, not systems. A primitive makes a single, well-defined guarantee — and nothing more. Symmetric encryption (e.g. AES) guarantees confidentiality: an adversary without the key cannot recover the plaintext. It makes no guarantee about integrity — an attacker can flip ciphertext bits and the decryption will succeed, producing corrupted plaintext you may not detect. Authenticated encryption (e.g. AES-GCM) adds an integrity and authenticity guarantee: the decryption will fail if the ciphertext was tampered with. This is not a marginal improvement — it is a categorically different guarantee, and choosing the wrong one depending on your threat model is a design flaw.

The distinction between confidentiality, integrity, and authenticity is the lens through which every cryptographic primitive must be evaluated. Confidentiality hides the content from an adversary. Integrity ensures the content was not modified in transit. Authenticity ensures the content came from a specific party. A symmetric cipher provides confidentiality alone. A MAC (Message Authentication Code) provides integrity and authenticity alone — it does not encrypt. Authenticated encryption combines both. Digital signatures provide authenticity and non-repudiation but typically don't encrypt. Understanding which combination your use case requires determines which primitive or scheme you reach for.

Mode matters as much as algorithm. AES is a block cipher — it encrypts a fixed-size block. How you apply it to arbitrary-length data (the "mode") determines the security properties. ECB (Electronic Codebook) applies AES independently to each block: identical plaintext blocks produce identical ciphertext blocks, leaking plaintext structure. CBC (Cipher Block Chaining) chains blocks using XOR with the previous ciphertext block, hiding identical plaintext blocks — but without authentication, an attacker can still flip bits in a predictable way (the padding oracle attack). GCM (Galois/Counter Mode) combines counter-mode encryption with a Galois MAC, providing authenticated encryption. The algorithm (AES) is the same in all three; the mode determines the actual security guarantee.

Key size and algorithm selection interact with threat models in ways that surprise practitioners. AES-256 is not twice as secure as AES-128 in any practical sense — the difference matters only against quantum adversaries (Grover's algorithm halves the effective key length). What does matter is the *mode* (ECB is broken regardless of key size) and the *implementation* (a timing side-channel in the code defeats the algorithm's mathematical strength). This is the calibration that "choose strong crypto" glosses over: algorithm selection is less important than mode selection, and both matter less than implementation correctness.

## Learn (~4 hrs)

**Cryptographic primitives — the concepts**
- [Cryptography I — Stanford/Coursera (Dan Boneh)](https://www.coursera.org/learn/crypto) — audit for free; watch Week 1 (discrete probability and stream ciphers) and Week 2 (block ciphers) for the mathematical grounding. These two weeks are the clearest explanation of why modes matter.
- [Crypto 101 (free e-book)](https://www.crypto101.io/) — chapters 1–5; a practitioner's introduction to the guarantee model (confidentiality, integrity, authenticity) and the common primitives. Download the PDF.

**Applied OpenSSL**
- [OpenSSL man pages — enc(1)](https://docs.openssl.org/3.0/man1/openssl-enc/) — the reference for `openssl enc`; understand the `-e`/`-d`, `-K`, `-iv`, and `-aead` options.
- [OpenSSL Cookbook (Ivan Ristić, free online)](https://www.feistyduck.com/library/openssl-cookbook/) — Chapter 1 "OpenSSL" and Chapter 3 "PKI and Certificates"; these two chapters give the practical command-line fluency you need for this track.

**Why modes matter**
- [AES-ECB penguin — Wikipedia illustration](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation#ECB) — the canonical image of ECB mode leaking plaintext structure through a penguin bitmap; shows the problem in one image.

## Key concepts

- Primitive guarantees: AES (confidentiality only), AES-GCM (confidentiality + integrity + authenticity), HMAC (integrity + authenticity, no confidentiality), RSA/EC (public-key operations).
- Confidentiality ≠ integrity. A cipher that doesn't authenticate can be tampered with.
- Mode determines security properties: ECB (broken), CBC (no auth, padding oracle risk), GCM (authenticated — use this).
- Key size matters less than mode choice; mode choice matters less than correct implementation.
- "Choose strong crypto" is insufficient guidance — identify the required guarantees first, then choose the primitive that provides them.

## AI acceleration

Ask an AI to explain why AES-CBC is vulnerable to a padding oracle attack. Then verify the explanation against a primary source (e.g. the original Vaudenay paper abstract, or the OWASP padding oracle description). AI is good at explaining cryptographic concepts in plain English; always cross-check technical claims against primary sources before treating them as correct.
