# Module 09 — Cryptography Basics

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *the trust layer under every secure system.*

## Why this matters
Every trust decision online rests on crypto: that a download wasn't tampered with
(hashing), that a session is private (symmetric), that a server is who it claims
(asymmetric + certificates). You don't need the math, but you do need to know what each
primitive guarantees — and what it doesn't. Get this wrong and the Cloud, Web, and
Crypto/PKI tracks all inherit the mistake.

## Objective
Explain and exercise the core primitives — hashing, symmetric and asymmetric encryption,
and certificates — with `openssl`, and recognise when one is misused.

## The core idea
Crypto is the trust layer under everything, and you don't need the math — you need to know what each
primitive *guarantees* and, more importantly, what it *doesn't*. Three jobs, three tools. **Hashing**
(SHA-256) proves **integrity** — same input, same fingerprint — and is one-way, not secret (this is the
exact foundation the offensive password-cracking module stands on). **Symmetric** encryption (AES)
gives **confidentiality** with one shared key — fast, but it raises the question "how do both sides get
the key safely?" **Asymmetric** (RSA/EC) answers that with a keypair, which also enables signatures and
underpins **certificates** — the chain of trust that lets you believe a server is who it claims (TLS).

The judgment-laden insight that prevents real bugs: **"encrypted" ≠ "authenticated."** Encryption hides
data; on its own it does *not* prove the data wasn't tampered with — which is why AEAD modes (that do
both) exist and why authenticated encryption is the modern default. "I encrypted it, so it's secure" is
precisely the mistake the Cloud, Web, and PKI tracks inherit when this module is skimmed.

The judgment on tooling: crypto is where confident-but-wrong AI is most dangerous — models cheerfully
suggest broken modes (ECB) and dead ciphers because those appear all over their training data. Use a
model to *explain* a concept, then verify the actual command and parameters against the OpenSSL
Cookbook before relying on them. In crypto, "looks right" and "is right" sit very far apart.

## Learn (~4 hrs)

**Concepts**
- [Crypto 101 (free book)](https://www.crypto101.io/) — a no-math, practical intro to the primitives and how they fail; the best free starting point.
- [Computerphile — AES Explained (~14 min)](https://www.youtube.com/watch?v=O4xNJsjtN6E) — Dr Mike Pound makes the core symmetric cipher click; his "Diffie Hellman" and "Hashing Algorithms" videos are the natural follow-ons.

**Hands-on with openssl & TLS**
- [OpenSSL Cookbook (free, Ivan Ristić)](https://www.feistyduck.com/library/openssl-cookbook/) — the canonical reference for the exact commands in the lab.
- [The Illustrated TLS 1.3 Connection](https://tls13.xargs.org/) — a byte-by-byte walk through a real handshake; makes "what a certificate is for" finally click.

**Reference**
- [RFC 8446 (TLS 1.3)](https://datatracker.ietf.org/doc/html/rfc8446) — the source of truth; skim, don't read cover to cover.

## Key concepts
- Hashing for integrity, not secrecy — SHA-256
- Symmetric encryption (one shared key) — AES, and why AEAD matters
- Asymmetric encryption (keypair) — RSA / EC
- Certificates and the chain of trust (X.509, TLS)
- "Encrypted" ≠ "authenticated"

## AI acceleration
Crypto is where confident-but-wrong AI advice is dangerous — models suggest broken modes
(ECB) and dead ciphers. Use a model to explain a concept, then verify the actual command
and parameters against the OpenSSL Cookbook before you rely on them.
