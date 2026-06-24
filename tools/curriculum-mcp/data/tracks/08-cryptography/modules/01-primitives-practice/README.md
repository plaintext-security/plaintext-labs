# Module 01 — Primitives in Practice

*Type 2 · Misconception Reveal — you predict 'encrypted = safe,' then watch ECB leak image structure and an unauthenticated-CBC ciphertext flip under a chosen bit-flip; the reveal is confidentiality ≠ integrity. (Secondary: Concept Autopsy.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**[Track 08 — Cryptography, PKI & Secrets]** — *Every cryptographic system is built from a small set of primitives — choose the wrong one and the system is broken before you write a line of code.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

In 2013, attackers exfiltrated **153 million Adobe accounts** — and the password column turned out to be encrypted with **3DES in ECB mode, with no salt** ([Schneier, "Cryptographic Blunders Revealed by Adobe's Password Leak"](https://www.schneier.com/blog/archives/2013/11/cryptographic_b.html)). Because ECB is deterministic, every user who chose the same password got the byte-for-byte identical ciphertext — so researchers recovered the top 100 passwords in hours, with no key, just by clustering identical blocks and reading the unencrypted "password hints" beside them. That is the whole lesson of this module in one breach: Adobe reached for *encryption* (reversible, wrong tool) instead of a *salted password hash*, and chose a *mode* (ECB) that leaks plaintext structure. Cryptography failures are in the OWASP Top 10 every year — not because cryptographers are rare, but because developers reach for the nearest API without understanding what guarantee it provides. AES-ECB is deterministic and leaks patterns; HMAC-MD5 is still technically a MAC but its collision resistance is gone; RSA with PKCS#1 v1.5 padding is vulnerable to Bleichenbacher's attack. The misuse patterns are predictable precisely because the underlying guarantee of each primitive is not well understood. This module builds the working mental model: what each primitive does, what it does not do, and how you know which one a situation calls for.

## Objective

Use OpenSSL to encrypt, decrypt, and authenticate data using the three foundational primitives — symmetric encryption, authenticated encryption, and asymmetric operations — and observe concretely what guarantee each provides and where it fails.

## The core idea

Cryptographic primitives are building blocks, not systems. A primitive makes a single, well-defined guarantee — and nothing more. Symmetric encryption (e.g. AES) guarantees confidentiality: an adversary without the key cannot recover the plaintext. It makes no guarantee about integrity — an attacker can flip ciphertext bits and the decryption will succeed, producing corrupted plaintext you may not detect. Authenticated encryption (e.g. AES-GCM) adds an integrity and authenticity guarantee: the decryption will fail if the ciphertext was tampered with. This is not a marginal improvement — it is a categorically different guarantee, and choosing the wrong one depending on your threat model is a design flaw.

The distinction between confidentiality, integrity, and authenticity is the lens through which every cryptographic primitive must be evaluated. Confidentiality hides the content from an adversary. Integrity ensures the content was not modified in transit. Authenticity ensures the content came from a specific party. A symmetric cipher provides confidentiality alone. A MAC (Message Authentication Code) provides integrity and authenticity alone — it does not encrypt. Authenticated encryption combines both. Digital signatures provide authenticity and non-repudiation but typically don't encrypt. Understanding which combination your use case requires determines which primitive or scheme you reach for.

Mode matters as much as algorithm. AES is a block cipher — it encrypts a fixed-size block. How you apply it to arbitrary-length data (the "mode") determines the security properties. ECB (Electronic Codebook) applies AES independently to each block: identical plaintext blocks produce identical ciphertext blocks, leaking plaintext structure — exactly the flaw that let researchers cluster and recover passwords from the Adobe 2013 dump without ever finding the key. CBC (Cipher Block Chaining) chains blocks using XOR with the previous ciphertext block, hiding identical plaintext blocks — but without authentication, an attacker can still flip bits in a predictable way (the padding oracle attack). GCM (Galois/Counter Mode) combines counter-mode encryption with a Galois MAC, providing authenticated encryption. The algorithm (AES) is the same in all three; the mode determines the actual security guarantee.

Key size and algorithm selection interact with threat models in ways that surprise practitioners. AES-256 is not twice as secure as AES-128 in any practical sense — the difference matters only against quantum adversaries (Grover's algorithm halves the effective key length). What does matter is the *mode* (ECB is broken regardless of key size) and the *implementation* (a timing side-channel in the code defeats the algorithm's mathematical strength). This is the calibration that "choose strong crypto" glosses over: algorithm selection is less important than mode selection, and both matter less than implementation correctness.

## Learn (~4 hrs)

**ECB's real-world failure — the *why* (~15 min)**
- [Schneier on Security — "Cryptographic Blunders Revealed by Adobe's Password Leak" (2013)](https://www.schneier.com/blog/archives/2013/11/cryptographic_b.html) — the 153M-account Adobe breach where passwords were *encrypted* with 3DES-ECB and unsalted; read why deterministic ECB plus reused password hints let researchers recover the most common passwords with no key. The canonical case that mode choice and "encrypt vs. hash" are not academic.

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
- ECB is not abstract: the **Adobe 2013** breach (153M accounts, 3DES-ECB, unsalted) was cracked by clustering identical ciphertext blocks — and used encryption where a salted password hash was the right tool.
- Key size matters less than mode choice; mode choice matters less than correct implementation.
- "Choose strong crypto" is insufficient guidance — identify the required guarantees first, then choose the primitive that provides them.

## AI acceleration

Ask an AI to explain why AES-CBC is vulnerable to a padding oracle attack. Then verify the explanation against a primary source (e.g. the original Vaudenay paper abstract, or the OWASP padding oracle description). AI is good at explaining cryptographic concepts in plain English; always cross-check technical claims against primary sources before treating them as correct.
