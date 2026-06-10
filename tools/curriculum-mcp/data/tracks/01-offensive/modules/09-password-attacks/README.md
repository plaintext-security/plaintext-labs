# Module 09 — Password & Credential Attacks

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *credentials are the keys; cracking and capturing them is how access spreads.*

## Why this matters
Most breaches don't "hack in" — they log in. Once you have a foothold, dumped password
hashes, reused credentials, and weak passwords turn access into more access. Understanding
how hashes are cracked — and how fast — is also the only way to argue convincingly for the
defenses (strong hashing, length, MFA) that stop it.

## Objective
Crack real password hashes, understand hash types and attack modes, and explain credential
attacks like spraying and reuse — plus the defenses that defeat them.

## The core idea
"Most breaches don't hack in — they log in." Credentials are the universal skeleton key, and this
module turns on one asymmetry: a **hash** is a one-way fingerprint of a password, so cracking is simply
*guess → hash the guess → compare*. That means the entire security of a stolen hash database comes down
to **how expensive each guess is.** Fast hashes (MD5, NTLM) fall at billions of guesses per second on a
GPU — a dumped database is effectively plaintext within hours. Slow KDFs (bcrypt, argon2) are *designed*
to make each guess thousands of times costlier, so the same dump is infeasible. That single fact is why
one leaked database is a shrug and an identical one elsewhere is a catastrophe.

The "attack modes" are just progressively smarter guessing: dictionary (known passwords) → rules
(mutate them — `Password` → `P@ssw0rd!`) → mask (known structure) → brute force (last resort). And the
dominant real-world entry vector isn't cracking at all — it's **reuse**: credentials from one breach
sprayed across everything else, because humans recycle passwords. (This is the Foundations crypto
lesson cashed in: hashing is not encryption — there's no "decrypt," only guess-and-check.)

The judgment, and the defensive payoff: understanding crack *speed* is the only way to argue the
defenses convincingly — demonstrating that a 9-character fast-hashed password dies in minutes makes the
case for length + a strong KDF + MFA far better than any policy memo. A model identifies a hash type and
suggests modes instantly, but it also misidentifies hashes and sends you burning GPU-hours on the wrong
attack. Confirm the hash type and mode yourself; cracking is expensive to get wrong.

## Learn (~4 hrs)

**Cracking**
- [Hashcat — official wiki](https://hashcat.net/wiki/) — hash modes, attack modes, and rules; the authoritative reference.
- [Hashcat Tutorial: A Beginner's Guide (video)](https://www.youtube.com/watch?v=4bchWTf7un8) — a hands-on first pass before the wiki.

**Where it sits, and the defense**
- [MITRE ATT&CK — Brute Force (T1110)](https://attack.mitre.org/techniques/T1110/) and [OS Credential Dumping (T1003)](https://attack.mitre.org/techniques/T1003/) — the techniques you're performing.
- [OWASP — Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) — the defender's side: why bcrypt/argon2 + salting beats you.

## Key concepts
- Hashing vs encryption (callback to Foundations crypto)
- Hash types (MD5, NTLM, bcrypt) and why some crack in seconds
- Attack modes: dictionary, rules, mask, brute force
- Credential spraying and reuse (the real-world entry vector)
- Defenses: strong KDFs, salting, length, MFA

## AI acceleration
A model suggests hashcat modes and rules and identifies a hash type instantly — handy. But it
also misidentifies hashes or suggests attacks that waste GPU-hours. Confirm the hash type and
mode yourself; cracking is expensive to get wrong.
