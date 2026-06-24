# Module 04 — Hashing, MACs & Passwords

*Type 2 · Misconception Reveal — you predict a fast unsalted hash is 'good enough' for passwords, then crack it at scale (the LinkedIn / Adobe reality); the reveal is that a slow, salted KDF is the only fix. (Secondary: Blast-Radius Trace.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**[Track 08 — Cryptography, PKI & Secrets]** — *A hash is not a MAC, a MAC is not a password hash, and using the wrong one for the job is a common and serious mistake.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

In 2012, **LinkedIn** lost roughly **117 million** account credentials — and because the passwords were stored as **unsalted SHA-1** hashes, ~90% were cracked within 72 hours of the dump surfacing ([TechCrunch — "117 million LinkedIn emails and passwords from a 2012 hack just got posted online"](https://techcrunch.com/2016/05/18/117-million-linkedin-emails-and-passwords-from-a-2012-hack-just-got-posted-online/)). SHA-1 was not the problem in itself — it was that a *fast, keyless, unsalted* hash is precisely the wrong tool for password storage: no salt means identical passwords share a hash and a single rainbow-table pass cracks them all, and the speed of SHA-1 means a GPU tries billions of guesses a second. Three distinct constructions — cryptographic hashes, message authentication codes, and password hashing functions — are routinely confused with each other, and the confusion leads to real vulnerabilities. Storing passwords as SHA-256 hashes is a breach waiting to happen; using HMAC where you need a password hash is the wrong tool; using MD5 where you need collision resistance is broken. Understanding what each construction provides — and what it explicitly does not — is the practitioner competency that prevents a category of vulnerabilities that appears in every major breach report.

## Objective

Use OpenSSL and the `argon2-cffi` Python library to compute hashes, HMACs, and password hashes; demonstrate the difference between each; and produce a cracking exercise that shows why password hashing with a proper KDF is non-negotiable.

## The core idea

A cryptographic hash function (SHA-256, SHA-3) maps arbitrary-length input to a fixed-length output. Its security properties are: preimage resistance (given a hash, you can't find the input), second-preimage resistance (given an input, you can't find a different input with the same hash), and collision resistance (you can't find any two inputs with the same hash). A hash has no key — it is deterministic and public. This means that if an adversary has the hash of a password, they can precompute a table of hash values for common passwords and look up the original. SHA-256 is fast — billions of hashes per second on modern hardware — which is exactly the wrong property for a password hash.

A Message Authentication Code (MAC) is a keyed construction. HMAC-SHA256 takes a key and a message and produces a tag that only someone with the key can produce or verify. It provides integrity and authenticity — but not confidentiality, and not preimage resistance in the password-storage sense. Using HMAC with the password as the key (a common mistake) still allows offline cracking if the attacker has the tag and can try billions of keys per second. The key in HMAC must be a secret held by the server, not derived from user input.

Password hashing functions — Argon2, bcrypt, scrypt, PBKDF2 — are designed specifically to be slow, memory-hard, and tunable. They include a random per-password salt (preventing precomputed table attacks), a cost factor (controlling how much work each hash requires), and optionally a memory parameter (making GPU-parallelised cracking expensive). Argon2id is the current recommendation from the OWASP Password Storage Cheat Sheet and the winner of the Password Hashing Competition. The core properties — salt, cost, memory hardness — make a brute-force attack against a properly hashed password database orders of magnitude harder than against an unsalted SHA-256 database.

The salt deserves specific attention because unsalted password databases are still found in breaches. A salt is a random value unique to each password that is stored alongside the hash. With salting, an attacker who obtains the database must crack each password individually — they cannot precompute a single table and look up all passwords at once. Without salting, a single crack against the most common password cracks every account that uses it — which is exactly why LinkedIn's unsalted SHA-1 store collapsed so fast in 2012. Two users with the same password have different hashes when salted; without salting, their hashes are identical and a single crack breaks both accounts simultaneously.

## Learn (~4 hrs)

**Password-hashing's real-world failure — the *why* (~15 min)**
- [TechCrunch — "117 million LinkedIn emails and passwords from a 2012 hack just got posted online" (2016)](https://techcrunch.com/2016/05/18/117-million-linkedin-emails-and-passwords-from-a-2012-hack-just-got-posted-online/) — LinkedIn stored passwords as unsalted SHA-1; ~90% were cracked within 72 hours of the leak. The canonical case for *why* a fast, keyless, unsalted hash is the wrong primitive for passwords — and why salt + a slow KDF is non-negotiable.

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
- **LinkedIn 2012** (~117M unsalted SHA-1 hashes, ~90% cracked in 72 hours) is the canonical proof that fast + unsalted = a breach already cracked.
- Cost/work factor: tunable — set it so hashing takes ~100–300ms on your hardware.

## AI acceleration

Ask an AI to explain the difference between Argon2i, Argon2d, and Argon2id and which to use for password storage. Verify the recommendation against the OWASP Password Storage Cheat Sheet — does it match? AI explains the variants; OWASP is the authority on which to use in production.
