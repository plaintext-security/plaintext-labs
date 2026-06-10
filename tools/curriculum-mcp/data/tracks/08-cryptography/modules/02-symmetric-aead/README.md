# Module 02 — Symmetric & AEAD

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *AES-GCM is the right choice — until you reuse the IV, at which point it is broken in a way that's worse than CBC.*

## Why this matters

Authenticated Encryption with Associated Data (AEAD) is the modern answer to the "confidentiality vs integrity" false choice in module 01. AES-GCM is the dominant AEAD scheme in practice — it is the cipher suite in TLS 1.3, the default in many cloud encryption APIs, and the recommended mode in NIST guidance. But AEAD schemes have a specific failure mode that is catastrophically worse than a classical cipher's failure: nonce/IV reuse. Understanding AEAD in depth — what it guarantees, what it requires of the caller, and where implementations go wrong — is the applied cryptography skill that separates a practitioner from someone who just picked the recommended mode.

## Objective

Demonstrate AES-GCM authenticated encryption and the concrete failure mode of IV reuse — showing that two messages encrypted with the same key and IV allow an attacker to recover the XOR of both plaintexts — then implement the correct IV generation pattern.

## The core idea

AES-GCM is a composed construction: it uses AES in Counter Mode (CTR) for encryption and GHASH for authentication. The CTR keystream is generated from the key and nonce (IV); if the same nonce is used with the same key, the same keystream is generated. When an attacker has two ciphertexts encrypted with the same key/nonce pair, XORing them cancels the keystream and produces the XOR of the two plaintexts — a known-plaintext or crib-dragging attack can then recover both. This is "nonce misuse" and it completely breaks the confidentiality guarantee, regardless of the fact that GCM otherwise provides authenticated encryption.

The authentication tag in GCM also depends on the nonce. Nonce reuse allows an attacker to forge authentication tags — recovering the authentication key from two messages encrypted with the same nonce. The combined result of nonce reuse is catastrophic: both confidentiality and authenticity are broken simultaneously. This is categorically worse than CBC's padding oracle (which breaks confidentiality under specific conditions) because it requires only two observed ciphertexts with the same nonce to achieve full compromise.

The correct implementation pattern for AES-GCM is a randomly generated 96-bit (12-byte) nonce for every encryption operation. The nonce is not secret — it is transmitted alongside the ciphertext — but it must be unique per key. At 96 bits of randomness, the birthday bound probability of a collision at 2^32 encryptions is acceptable for most applications; if you need more encryptions under a single key, use a deterministic nonce (a counter) with collision-resistant generation, or rotate the key. The key insight is that the nonce uniqueness requirement is a caller responsibility — the AES-GCM algorithm cannot enforce it. Bugs that reuse nonces are typically found in embedded systems with weak entropy sources, in counter implementations that reset after restart, or in code that hardcodes a test nonce into production.

ChaCha20-Poly1305 is the AEAD alternative to AES-GCM. It uses the ChaCha20 stream cipher with the Poly1305 MAC. Its primary advantage is software performance without hardware AES acceleration — relevant for mobile devices, IoT, and systems where AES-NI is not available. Its nonce requirements are identical to GCM: unique 96-bit nonce per encryption. TLS 1.3 includes both `TLS_AES_256_GCM_SHA384` and `TLS_CHACHA20_POLY1305_SHA256` as mandatory cipher suites, and most TLS implementations negotiate ChaCha20 when AES-NI is unavailable on the client.

## Learn (~4 hrs)

**AES-GCM in depth**
- [NIST SP 800-38D — Recommendation for GCM](https://csrc.nist.gov/pubs/sp/800/38/d/final) — the specification; read Sections 5–6 (the construction and requirements) and Section 8 (the key usage guidance). The nonce uniqueness requirement is in Section 8.

**AEAD alternatives**
- [RFC 8439 — ChaCha20 and Poly1305 for IETF Protocols](https://www.rfc-editor.org/rfc/rfc8439) — the spec for ChaCha20-Poly1305; read the Introduction and Section 2 for the construction overview.

**IV reuse attack implementation**

**Python cryptography library**
- [cryptography.io — Symmetric encryption with AEAD](https://cryptography.io/en/latest/hazmat/primitives/aead/) — the `AESGCM` and `ChaCha20Poly1305` API reference; understand the `nonce` parameter and the `InvalidTag` exception.

## Key concepts

- AES-GCM = AES-CTR (encryption) + GHASH (authentication); both depend on the nonce.
- Nonce reuse breaks both confidentiality (XOR of plaintexts) and authenticity (tag forgery).
- The nonce must be unique per key; uniqueness is a caller responsibility the algorithm cannot enforce.
- Correct pattern: randomly generated 96-bit nonce per encryption, transmitted with ciphertext.
- ChaCha20-Poly1305 is the software-performance alternative; same nonce requirements, different algorithm.

## AI acceleration

Ask an AI to write a Python script demonstrating the GCM nonce-reuse attack: encrypt two messages with the same key and nonce, XOR the ciphertexts, and show the result is the XOR of the plaintexts. Verify the math works by running the script. Then ask it to write the *correct* version with a randomly generated nonce. Check that the random nonce version uses `os.urandom(12)` or equivalent — not a hardcoded value — before committing either.
