# Module 09 — Cryptography Basics

*Variant D · misconception, predict-then-reveal. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *the trust layer under every secure system — learned by seeing what "encrypted" doesn't mean.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~5–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules
{ .module-meta }


## Why this matters
Every trust decision online rests on crypto: that a download wasn't tampered with, that a login is
private, that a server is who it claims to be. You don't need the math — you need to know what each
tool *guarantees* and, far more importantly, what it *doesn't*. The single most expensive crypto
mistake in history wasn't broken math; it was using the *wrong tool for the job* and assuming the word
"encrypted" meant "safe." You'll learn the primitives by watching that exact assumption fail at the
scale of 153 million people.

## Objective
Explain the core primitives — **hashing**, **symmetric** and **asymmetric** encryption, and
**certificates** — exercise each with `openssl`, and state precisely why a password must be *hashed*,
never *encrypted*.

## The case
In October 2013, **Adobe** disclosed a breach of **153 million accounts**. Adobe's own statement was
reassuring: the passwords were **encrypted**. They had not been left in plaintext; a real cipher had
been applied. By the headline's logic, the users were protected.

Then security researchers got hold of the dump, and it fell apart. Adobe had encrypted the passwords
with **3DES in ECB mode**, using **one key for every password** and **no salt** — and, in many rows,
shipped a **plaintext password hint** right beside the ciphertext. The result became a textbook
example (and a viral "crossword" puzzle the community solved collaboratively): millions of passwords
recovered without anyone ever breaking the cipher's math. The clearest public walk-throughs are
[Paul Ducklin's "Anatomy of a password disaster" on Naked Security](https://nakedsecurity.sophos.com/2013/11/04/anatomy-of-a-password-disaster-adobes-giant-sized-cryptographic-blunder/)
and his follow-up, ["How to store your users' passwords safely"](https://nakedsecurity.sophos.com/2013/11/20/serious-security-how-to-store-your-users-passwords-safely/).

## Call it before you read on
Don't scroll. Write down one answer — being wrong here is the entire point; it's what makes the lesson
stick.

> **Adobe said the passwords were *encrypted*, not left in plaintext. So — were the users safe?**

Most beginners say "yes, encrypted means safe." Hold that thought.

## The reveal — encrypted, and not remotely safe

No. They were catastrophically exposed, and the reason is the whole point of this module: **for a
password, "encrypted" is the wrong goal — you want it *hashed*.** Three separate mistakes stacked up,
and each one is a primitive you need to understand.

**A *hash* is one-way; a *cipher* is two-way — and a password should be one-way.** A **cryptographic
hash** (like SHA-256) is a function that turns any input into a fixed-size fingerprint, and *cannot be
reversed* — there's no "un-hash." A **cipher** (encryption) is *designed* to be reversed: whoever has
the key gets the original back. A login system never needs the original password back — it only needs
to check "does this match?" So you store the *hash*; on login you hash the attempt and compare. Adobe
*encrypted* (reversible) what should have been *hashed* (one-way). The moment the key leaked — and keys
always eventually leak — every password was recoverable. **Encryption is for data you need back;
hashing is for verifying something without storing it.**

**ECB mode leaks structure — equal input makes equal output.** A cipher processes data in blocks, and
**ECB** ("Electronic Codebook") is the naïve mode that encrypts each block *independently with the same
key*. So **identical plaintext always produces identical ciphertext.** With one key across all 153M
rows and no randomization, every user who picked `123456` got the *exact same* ciphertext — instantly
visible as the most common value in the dump. Cross-reference those clusters with the plaintext hints
sitting alongside ("name of my dog", "1-6") and you recover the password for an entire cluster at once.
This is the famous **"ECB penguin"**: encrypt an image in ECB and you can still *see* the penguin,
because the patterns survive. ECB hides values, not patterns — and patterns were enough.

**Salt makes identical passwords look different — Adobe had none.** A **salt** is a random value mixed
into each password *before* hashing, stored alongside the result. Its job is exactly to defeat the ECB
problem: with a unique salt per user, two people with the same password get two *different* stored
values, so an attacker can't cluster them and can't reuse one cracked guess across the whole database.
No salt + ECB + a shared key + plaintext hints is four reinforcing failures — but the root error is the
first one: a password should never have been *encrypted* at all.

**The model to keep:** *a password should be **hashed** — one-way and salted — never **encrypted**.*
Encryption protects data you intend to read again; hashing proves a match without ever holding the
secret. If you answered "encrypted means safe," you've just made the exact assumption that turned a
real cipher into 153M crackable passwords — and that is the assumption the Web, Cloud, and PKI tracks
all inherit when this module is skimmed.

## Learn (~3 hrs)

*Short on purpose. The reveal above is the spine; read these to deepen the mechanism, not to relearn
the model.*

**The primitives, no math**
- [Crypto 101 (free book, Laurens Van Houtven)](https://www.crypto101.io/) — a no-math, practical intro to hashing, ciphers, and how they fail. Read the early chapters on hash functions and block-cipher modes; it explains ECB's weakness directly.
- [Computerphile — AES Explained (~14 min)](https://www.youtube.com/watch?v=O4xNJsjtN6E) — Dr Mike Pound makes symmetric encryption click; his adjacent "Hashing Algorithms and Security" video is the natural follow-on for the hash-vs-cipher distinction.

**Storing passwords the right way (the primary source)**
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) — the canonical answer to "what should Adobe have done": a salted, slow password hash (bcrypt/Argon2), never encryption. Read the "do / don't" up top.
- [NIST SP 800-63B — Digital Identity (§5.1.1, memorized secrets)](https://pages.nist.gov/800-63-3/sp800-63b.html) — the authoritative standard on password handling; skim §5.1.1 only for the storage requirements.

**Hands-on reference**
- [OpenSSL Cookbook (free, Ivan Ristić)](https://www.feistyduck.com/library/openssl-cookbook/) — the canonical reference for the exact commands in the lab; confirm every flag here.

## Key concepts
- **Hash vs cipher:** a hash is one-way (no un-hash); a cipher is two-way (reversible with the key)
- **Hash a password, encrypt data you need back** — Adobe encrypted what should have been hashed
- **ECB leaks structure:** identical input → identical output (the "ECB penguin"); patterns survive
- **Salt** = a per-user random value mixed in before hashing, so identical passwords store differently
- Symmetric (one shared key, AES), asymmetric (a keypair, RSA/EC), and certificates (the chain of trust behind TLS)

## AI acceleration
Crypto is where confident-but-wrong AI advice is most dangerous: models cheerfully suggest broken modes
(ECB) and dead ciphers because those appear all over their training data. Hand a model the Adobe story
and ask it to explain why the passwords were crackable *before* you read the reveal — then check it
against this module. It often gets the headline ("ECB is bad") but blurs *why* hashing, not encryption,
was the real fix. Use a model to *explain* a concept, then verify the actual command and flags against
the OpenSSL Cookbook before you rely on them. You own the verdict.
