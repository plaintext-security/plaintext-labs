# Lab 04 — Hashing, MACs & Passwords

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/04-hashing-macs-passwords
make up        # build the Python + OpenSSL + argon2 container
make demo      # show SHA-256 hash, HMAC-SHA256, Argon2id hash, and cracking exercise
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs offline. No external dependencies.

## Scenario

Meridian Financial's legacy payroll application stores employee passwords as unsalted SHA-256
hashes. A penetration test extracted the hash database. Your job: demonstrate how quickly an
unsalted SHA-256 database can be cracked, then implement Argon2id storage, and show the
cracking cost difference.

## Do

1. [ ] `make demo` — observe: SHA-256 hashes computed for the sample passwords, HMAC-SHA256
   with a key, Argon2id hashes with tuned parameters, and a simulated crack attempt against
   the SHA-256 hashes.

2. [ ] `make shell` and crack the unsalted SHA-256 hashes against the bundled wordlist
   (`/lab/data/passwords.txt`). The mechanism is the lesson: build the lookup of
   `sha256(word) -> word` over the wordlist and match the target hashes against it. How many of
   the targets fall, and roughly what rate would a GPU-backed crack hit against unsalted SHA-256?

3. [ ] Hash the same passwords with Argon2id using tuned parameters (`time_cost`, `memory_cost`,
   `parallelism`), timing each hash. What is the per-hash cost, how many Argon2id hashes/sec can
   this container manage, and how many orders of magnitude does that differ from the SHA-256
   rate in step 2?

4. [ ] Verify an Argon2id hash: hash a password, then confirm the verifier accepts the correct
   password and rejects a wrong one. (Note what the library raises on mismatch.)

5. [ ] Compute an HMAC-SHA256 over a message with `openssl mac … HMAC`, then change one
   character and recompute. Do the MACs match? Explain why HMAC is the right tool for message
   integrity but the wrong tool for password storage.

## Success criteria — you're done when

- [ ] You cracked at least two of the three unsalted SHA-256 hashes using the wordlist.
- [ ] You measured the Argon2id hashing rate and can state the orders-of-magnitude difference.
- [ ] You verified Argon2id accepts the correct password and rejects the wrong one.
- [ ] You can explain in one paragraph why HMAC is the right tool for message integrity but not password storage.

## Deliverables

`password-analysis.md` — your cracking results (how many cracked, how fast), the Argon2id
timing (hashes per second), and a one-page argument for migrating Meridian's password storage
from SHA-256 to Argon2id including work factor recommendation. Commit it.

## Automate & own it

**Required.** Write a Python script `check-password-hash.py` that reads a file of stored hashes
and flags any that are identifiable as MD5, SHA-1, or SHA-256 by their length and format (no
salt, no algorithm identifier prefix). Output: "VULNERABLE: N passwords stored as <algorithm>".
Have an AI draft the pattern-matching logic; you verify it correctly identifies `$argon2id$`
prefixed hashes as "OK" and bare hex strings as vulnerable.

## AI acceleration

Ask an AI: "What Argon2id time_cost, memory_cost, and parallelism settings are appropriate for
a login endpoint that should take ~200ms per hash on 2 CPU cores with 512MB available?" Use the
OWASP Password Storage Cheat Sheet to validate the recommendation. Then test it in the container
and measure the actual elapsed time.

## Connects forward

The password hash principles here are directly applied in module 07 (Secrets Management) —
Vault's internal authentication uses bcrypt, and knowing why matters. Module 10 (Auditing
Applied-Crypto Failures) includes finding unsalted or weak password hashes as an audit check.

## Marketable proof

> "I demonstrated the difference between unsalted SHA-256 (cracked in milliseconds) and Argon2id
> (computation-bounded by design), and wrote a migration recommendation for Meridian's password
> storage with tuned work factor parameters."

## Stretch

- Implement the [Have I Been Pwned k-anonymity API](https://haveibeenpwned.com/API/v3#SearchingPwnedPasswordsByRange):
  hash a password with SHA-1, send the first 5 hex characters to the API, check if your hash
  appears in the response. This is the production pattern for checking passwords without
  revealing them to the service.
- Research rainbow tables: how does a salt specifically defeat them? Write a one-paragraph
  explanation, then verify your understanding by showing that two Argon2id hashes of the same
  password produce different outputs (different salts).
