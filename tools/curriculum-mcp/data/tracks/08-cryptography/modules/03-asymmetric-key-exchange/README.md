# Module 03 — Asymmetric & Key Exchange

*Type 2 · Misconception Reveal — you predict where an asymmetric scheme fails, then see it: predictable keys (ROCA / Debian OpenSSL RNG) and reused nonces (PS3 ECDSA) hand over the private key. (Secondary: Concept Autopsy.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**[Track 08 — Cryptography, PKI & Secrets]** — *Public-key cryptography solves the key distribution problem; Diffie-Hellman turns it into something you can do over an untrusted channel.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

Asymmetric cryptography is only as strong as the randomness underneath it — and that is where it breaks in the real world. In 2017, **ROCA** ([CVE-2017-15361](https://nvd.nist.gov/vuln/detail/CVE-2017-15361)) showed that a flawed RSA key-generation routine in Infineon's crypto library produced primes with enough structure that the *public* key alone leaked the private key — affecting TPM chips, Estonian national ID cards, and YubiKeys in the field. Years earlier, **fail0verflow** recovered Sony's PlayStation 3 code-signing private key because Sony reused the *same* ECDSA random value `k` across signatures: two signatures sharing a nonce let you solve directly for the private key. Both are the same lesson from opposite ends — the math (factoring, the elliptic-curve discrete log) was never broken; the *key generation* and the *signature nonce* were. Every TLS session you initiate starts with a key exchange, every digital signature you verify uses asymmetric cryptography, and every SSH connection relies on public-key authentication — so understanding how the mechanism works, and the narrow places where it actually fails, is foundational for any practitioner who operates, audits, or builds systems that communicate securely.

## Objective

Generate RSA and ECDSA keypairs with OpenSSL, sign and verify a message, perform a simulated ECDH key exchange, and understand the concrete security properties and weaknesses of each operation.

## The core idea

Asymmetric cryptography is built on mathematical trapdoors: operations that are easy to perform in one direction and computationally infeasible to reverse without a secret. RSA's trapdoor is integer factorisation — generating two large primes and multiplying them takes milliseconds; factoring the product takes longer than the age of the universe at current computational limits. ECDSA and ECDH use elliptic curve discrete logarithm — multiplying a point on a curve by a scalar (private key) to get another point (public key) is fast; recovering the scalar from the two points is infeasible for properly chosen curves. In practice the trapdoor rarely fails head-on; what fails is the randomness feeding it — ROCA broke RSA by generating structured primes, and the PS3 ECDSA key fell because the per-signature nonce `k` was reused, letting the private key be solved for algebraically.

The difference between RSA and elliptic curve (EC) schemes is not security level — it is key size. A 256-bit EC key provides roughly the same security as a 3072-bit RSA key. For equivalent security, EC keys are orders of magnitude smaller, making them faster to generate, faster to sign with, and cheaper to transmit. This is why modern TLS, SSH, and code-signing infrastructure has migrated to ECDSA and Ed25519. RSA is not broken — but at 2048 bits it is marginal for long-lived keys, and generating new RSA infrastructure today should use at least 3072 bits.

Diffie-Hellman key exchange (DH) is the mechanism that allows two parties to establish a shared secret without transmitting the secret itself. Each party generates an ephemeral keypair, exchanges public keys, and computes the shared secret using their private key and the other party's public key. The shared secret is never transmitted — it is computed independently on each side and used to derive symmetric session keys. ECDH (Elliptic Curve Diffie-Hellman) is the EC variant; it is what TLS 1.3's key exchange uses. The "ephemeral" part is critical: if the server reuses the same DH parameters across sessions, past sessions can be decrypted if the server's long-term private key is later compromised — the forward secrecy property is lost.

Forward secrecy deserves explicit attention because it is the property that makes ephemeral key exchange valuable. A session has forward secrecy if compromising the long-term key does not allow decryption of past sessions. With static DH or RSA key exchange (the old TLS 1.2 pattern), the server's private key can decrypt any session recorded in the past. With ephemeral ECDH (ECDHE), each session's key is derived from a freshly generated ephemeral key that is discarded after the session — so even if the long-term key is compromised, past sessions remain encrypted. This is why "perfect forward secrecy" (PFS) appears in TLS audit reports as a positive finding.

## Learn (~4 hrs)

**Asymmetric crypto's real-world failures — the *why* (~25 min)**
- [NVD — CVE-2017-15361 (ROCA)](https://nvd.nist.gov/vuln/detail/CVE-2017-15361) — Infineon's RSA library generated primes structured enough that the public key leaked the private key; read the description and note the affected products (TPMs, ID cards, YubiKeys). Proof that *key generation*, not the factoring problem, is where RSA breaks in the field.
- [Console Hacking 2010 — "PS3 Epic Fail" (fail0verflow, 27C3 — media.ccc.de)](https://media.ccc.de/v/27c3-4087-en-console_hacking_2010) — ~1 hr; the segment on ECDSA shows that Sony reused the random nonce `k` across signatures, so the signing private key could be solved for algebraically. The textbook nonce-reuse signature break, in a shipped product.

**Asymmetric cryptography foundations**
- [Cryptography I (Dan Boneh, Stanford/Coursera)](https://www.coursera.org/learn/crypto) — Week 5 (Public Key Encryption) and Week 6 (Digital Signatures); audit for free. These are the clearest formal treatments of RSA and its security assumptions.

**Practical OpenSSL**
- [OpenSSL man pages — genpkey(1)](https://docs.openssl.org/3.0/man1/openssl-genpkey/) — generating RSA, EC, and X25519 keys.
- [OpenSSL man pages — pkeyutl(1)](https://docs.openssl.org/3.0/man1/openssl-pkeyutl/) — signing, verification, and ECDH key derivation.

**Forward secrecy**

**Algorithm selection**
- [Cryptographic right answers (Latacora)](https://www.latacora.com/blog/2018/04/03/cryptographic-right-answers/) — a concise, opinionated guide to current algorithm recommendations; read the asymmetric encryption and signatures sections.

## Key concepts

- RSA trapdoor: integer factorisation. EC trapdoor: elliptic curve discrete logarithm. Both are infeasible to reverse without the private key.
- Key size equivalence: 256-bit EC ≈ 3072-bit RSA security. EC is preferred for new infrastructure.
- DH key exchange: shared secret computed independently by each party; the secret is never transmitted.
- Forward secrecy: ephemeral keys per session → past sessions stay encrypted even if long-term key is compromised.
- TLS 1.3 mandates ECDHE; no static DH or RSA key exchange allowed.
- Asymmetric crypto breaks at the *randomness*, not the math: **ROCA** (CVE-2017-15361) leaked RSA private keys from structured key generation; the **PS3 ECDSA** key fell to a reused signature nonce `k`.

## AI acceleration

Ask an AI to explain the ECDH key exchange computation step-by-step: what Alice sends, what Bob sends, and how each computes the shared secret. Then verify the explanation by running through it manually with `openssl pkeyutl` — does the shared secret computed by Alice match the shared secret computed by Bob? AI explains the math; the terminal output confirms it.
