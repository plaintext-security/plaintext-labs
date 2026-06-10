# Module 04 — Hashing, MACs & Passwords

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *A hash is not a MAC, a MAC is not a password hash, and using the wrong one for the job is a common and serious mistake.*

## Why this matters

Three distinct constructions — cryptographic hashes, message authentication codes, and password hashing functions — are routinely confused with each other, and the confusion leads to real vulnerabilities. Storing passwords as SHA-256 hashes is a breach waiting to happen; using HMAC where you need a password hash is the wrong tool; using MD5 where you need collision resistance is broken. Understanding what each construction provides — and what it explicitly does not — is the practitioner competency that prevents a category of vulnerabilities that appears in every major breach report.

## Objective

Use OpenSSL and the `argon2-cffi` Python library to compute hashes, HMACs, and password hashes; demonstrate the difference between each; and produce a cracking exercise that shows why password hashing with a proper KDF is non-negotiable.

## The core idea

A cryptographic hash function (SHA-256, SHA-3) maps arbitrary-length input to a fixed-length output. Its security properties are: preimage resistance (given a hash, you can't find the input), second-preimage resistance (given an input, you can't find a different input with the same hash), and collision resistance (you can't find any two inputs with the same hash). A hash has no key — it is deterministic and public. This means that if an adversary has the hash of a password, they can precompute a table of hash values for common passwords and look up the original. SHA-256 is fast — billions of hashes per second on modern hardware — which is exactly the wrong property for a password hash.

A Message Authentication Code (MAC) is a keyed construction. HMAC-SHA256 takes a key and a message and produces a tag that only someone with the key can produce or verify. It provides integrity and authenticity — but not confidentiality, and not preimage resistance in the password-storage sense. Using HMAC with the password as the key (a common mistake) still allows offline cracking if the attacker has the tag and can try billions of keys per second. The key in HMAC must be a secret held by the server, not derived from user input.

Password hashing functions — Argon2, bcrypt, scrypt, PBKDF2 — are designed specifically to be slow, memory-hard, and tunable. They include a random per-password salt (preventing precomputed table attacks), a cost factor (controlling how much work each hash requires), and optionally a memory parameter (making GPU-parallelised cracking expensive). Argon2id is the current recommendation from the OWASP Password Storage Cheat Sheet and the winner of the Password Hashing Competition. The core properties — salt, cost, memory hardness — make a brute-force attack against a properly hashed password database orders of magnitude harder than against an unsalted SHA-256 database.

The salt deserves specific attention because unsalted password databases are still found in breaches. A salt is a random value unique to each password that is stored alongside the hash. With salting, an attacker who obtains the database must crack each password individually — they cannot precompute a single table and look up all passwords at once. Without salting, a single crack against the most common password cracks every account that uses it. Two users with the same password have different hashes when salted; without salting, their hashes are identical and a single crack breaks both accounts simultaneously.

## Learn (~4 hrs)

**Hash functions and MACs**
- [Cryptography I (Dan Boneh, Stanford/Coursera)](https://www.coursera.org/learn/crypto) — Week 7 (Hash Functions and HMAC); free audit. The clearest treatment of the security properties of each construction and why they differ.
- [NIST SP 800-107 — Recommendation for Hash Functions](https://csrc.nist.gov/pubs/sp/800/107/r1/final) — Sections 1–3; the NIST guidance on SHA-2/SHA-3 usage.

**Password hashing**
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) — the authoritative practitioner guide; read the full page (~20 min). This is the reference for algorithm selection and work factor.
- [argon2-cffi documentation](https://argon2-cffi.readthedocs.io/en/stable/) — the Python Argon2 library; read the "Using argon2-cffi" section for the API.

**Hash cracking context**
- [Have I Been Pwned — Passwords FAQ](https://haveibeenpwned.com/Passwords) — the context for why password hash databases matter; understand what k-anonymity and Pwned Passwords provides.

## Key concepts

- Hash: keyless, deterministic, fast — do NOT use for passwords.
- HMAC: keyed, provides integrity/authenticity — the key must be server-secret, not user-supplied.
- Password hash (Argon2id): slow, salted, memory-hard — the only correct choice for password storage.
- Salt: random per-password value stored with the hash; prevents precomputed table attacks.
- Cost/work factor: tunable — set it so hashing takes ~100–300ms on your hardware.

## AI acceleration

Ask an AI to explain the difference between Argon2i, Argon2d, and Argon2id and which to use for password storage. Verify the recommendation against the OWASP Password Storage Cheat Sheet — does it match? AI explains the variants; OWASP is the authority on which to use in production.
