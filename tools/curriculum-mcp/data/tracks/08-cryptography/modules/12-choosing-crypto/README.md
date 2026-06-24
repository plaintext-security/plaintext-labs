# Module 12 — Choosing Your Crypto: an ADR

*Type 11 · Decision / ADR — turn the scattered algorithm/mode/library trade-offs from this track into owned Architecture Decision Records; the deliverable is a set of ADRs (options · trade-offs · decision · consequences · what-would-change-it) each citing the current standard, not an essay. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**[Track 08 — Cryptography, PKI & Secrets]** — *The trust layer of everything: the strongest primitive is worthless if you can't say why you chose it.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) + the earlier crypto modules (02 Symmetric & AEAD, 03 Asymmetric & Key Exchange, 04 Hashing/MACs/Passwords, 07 Secrets Management)
{ .module-meta }

## Why this matters

By now this track has taught you the trade-offs four times over — AES-GCM vs ChaCha20-Poly1305 in
module 02, Ed25519 vs RSA in module 03, Argon2id vs bcrypt in module 04, Vault vs SOPS vs cloud KMS
in module 07 — but it has never asked you to *commit a choice to paper and defend it*. That gap is
exactly where applied cryptography goes wrong in production. The algorithm/mode/library choice is the
single most ADR-shaped decision in security: it is made once, lived with for years, almost impossible
to reverse cheaply, and routinely made by copying a Stack Overflow snippet whose author is long gone
and whose context no longer applies. When a reviewer later asks "why CBC here?" or "why a 4096-bit RSA
key for a token that lives 90 seconds?", the honest answer is usually "nobody recorded why" — and an
unrecorded crypto decision is one nobody can audit, migrate, or defend.

The cost of *not* recording the choice is concrete: the same fast-hash-for-passwords mistake gets
re-made because the last engineer's reasoning was never written down; a service ships AES-GCM and then
reuses a nonce because nobody captured the "GCM is fine **only if** the IV is unique" caveat that makes
the choice safe; a "we'll just use RSA, it's standard" decision quietly blocks the post-quantum
migration five years later. This track's own capstone rubric rewards "cites the standard for each
decision" — a criterion it grades *implicitly* but never gives you a vehicle to produce. The ADR is
that vehicle. This module is short on new theory and long on judgment: you already know the primitives;
here you learn to make the call, cite the standard, and own the consequences.

## Objective

Produce a small set of **Architecture Decision Records** for a service's cryptographic choices — one
ADR each for the AEAD cipher, the signature scheme, the password KDF (with concrete parameters), and
the secrets backend. Each ADR states the options, the honest trade-offs, the decision, the consequences
(including what you give up), and **what would change the decision** — and each cites the current
authoritative standard for that choice. The deliverable is the set of ADRs; their quality is the
defence, not the pick.

## The core idea

This is a **Decision / ADR** module: there is rarely a single universally-correct answer, only a choice
that is right *for a stated context* and that you can defend later. The construct is Michael Nygard's
**Architecture Decision Record** — a one-to-two-page document with a fixed skeleton: **Context** (the
forces at play), **Options** considered, the **Decision** (active voice — "we will use…"), and
**Consequences** (the results, positive *and* negative). For crypto we add one field Nygard's general
format doesn't name but that the domain demands: **"what would change this decision"** — the explicit
trigger (a broken primitive, a new standard, a performance ceiling, a compliance shift) that future-you
should watch for. That field is what turns an ADR from a tombstone into a living crypto-agility plan: it
is the thing module 11's post-quantum migration will read first. The single discipline that separates a
real ADR from an essay is that the Consequences and the negatives are as specific as the upsides — a
recommendation with only benefits is the tell of a junior engineer, or an AI draft nobody reviewed.

There are four canonical crypto decisions almost every service makes, and each has a *real* trade-off
and a *current* standard you must cite rather than assert:

- **AEAD cipher — AES-GCM vs ChaCha20-Poly1305.** Both are authenticated encryption with associated
  data; both are excellent. The real axis is *hardware*: AES-GCM is fastest where the CPU has AES-NI
  and a carryless-multiply instruction (most server and modern desktop x86/ARM), while
  ChaCha20-Poly1305 is constant-time in pure software and wins on hardware that lacks AES acceleration
  (older mobile, embedded, some IoT). The shared, decision-defining caveat: **both are catastrophically
  broken by nonce/IV reuse** — GCM in particular leaks the authentication key on a single repeated
  nonce under the same key (module 02's lesson). So the ADR's real *consequence* line isn't "we chose
  GCM," it's "we chose GCM **and** we use a counter/random-96-bit nonce we can prove is unique, per
  NIST SP 800-38D." The standard to cite: NIST SP 800-38D (GCM, including the uniqueness requirement)
  and RFC 8439 (ChaCha20-Poly1305).

- **Signature scheme — Ed25519 vs ECDSA vs RSA.** Ed25519 (EdDSA over Curve25519, RFC 8032) is the
  modern default: small keys and signatures, fast, deterministic (no per-signature nonce to leak — the
  flaw that bricked the Sony PS3 and has burned ECDSA implementations repeatedly), and hard to misuse.
  ECDSA is what you choose when an ecosystem or hardware module mandates it (and then you must use a
  deterministic-nonce or hedged variant). RSA is the choice you keep for *interoperability* with legacy
  systems and some HSMs/CAs that don't yet speak EdDSA, at the cost of large keys and slow signing. The
  decision pivots on a single question — "must this verify against existing/legacy verifiers, or are we
  greenfield?" — and the "what would change this" line is almost always the post-quantum trigger: none
  of these three survive a cryptographically-relevant quantum computer, so the ADR should name ML-DSA /
  the NIST PQC suite as the migration target it expects to record next.

- **Password KDF — Argon2id vs bcrypt vs scrypt, *with parameters*.** This is the decision where the
  *parameters are the decision*: "use Argon2id" with no cost factor is not an ADR, it's a slogan. The
  current standard is Argon2id (RFC 9106), and the practitioner trade-off is *memory-hardness vs your
  server budget* — Argon2id and scrypt are memory-hard (they cost an attacker GPU/ASIC RAM, not just
  cycles), bcrypt is not memory-hard but is battle-tested, ubiquitous, and constrained to a 72-byte
  input. The ADR must record concrete tuned parameters and the rule that you re-benchmark them on your
  hardware to hit a target verify time (~tens to a few hundred ms), citing OWASP's current minimums as
  the floor: Argon2id at m=19 MiB, t=2, p=1 (or the higher RFC 9106 profiles), bcrypt at work factor ≥
  10, scrypt at N=2¹⁷. "What would change this": a faster cracking landscape (raise the cost factors) or
  a platform that can't afford the memory (fall back to bcrypt, knowingly).

- **Secrets backend — Vault vs SOPS vs cloud KMS.** Not an algorithm choice but the same ADR shape, and
  the one this track already built in module 07. The axis is *runtime broker vs secrets-in-git vs
  managed envelope*: Vault gives dynamic, short-lived, audited secrets at the cost of running and
  unsealing a stateful service; SOPS encrypts values *in* the repo so GitOps stays git-only, at the cost
  of no rotation or audit trail of its own; cloud KMS (AWS/GCP/Azure) hands you a managed key store and
  envelope encryption at the cost of vendor lock-in and a key custodian you don't control. The decision
  follows the deployment model (GitOps-heavy → SOPS+age; dynamic DB creds and short leases → Vault;
  already all-in on one cloud → that cloud's KMS), and the honest consequence is always the ops/lock-in
  line the vendor's marketing omits.

Write each of these as its own ADR. The point of the format is that it *forces the honesty*: the
Consequences and "what would change this" sections are where you record what you gave up and the
condition under which today's right answer becomes tomorrow's migration ticket.

## Learn (~3 hrs)

**The ADR format (~45 min)**
- [Documenting Architecture Decisions — Michael Nygard (2011)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — the original ADR post, two pages, the source of the Context/Decision/Consequences skeleton the deliverable uses. Read it for *why* the format is deliberately tiny ("large documents are never kept up to date") and why Consequences carries the honest downsides.
- [joelparkerhenderson/architecture-decision-record (GitHub)](https://github.com/joelparkerhenderson/architecture-decision-record) — the canonical ADR reference repo: read the "What is an ADR" intro and the Nygard and MADR templates. Copy a template from here as your starting skeleton rather than inventing one; skim the worked examples to see the *tone* of a good Consequences section.

**The standards you must cite (~1.5 hrs — read the named sections only, these are references not tutorials)**
- [NIST SP 800-38D — GCM and GMAC](https://csrc.nist.gov/pubs/sp/800/38/d/final) — the authoritative GCM spec. You do not read it cover to cover: read §8 (the IV/nonce uniqueness requirement and the consequences of repetition). This is the standard your AES-GCM ADR cites for *why the nonce rule is the decision*.
- [RFC 8439 — ChaCha20 and Poly1305 for IETF Protocols](https://www.rfc-editor.org/rfc/rfc8439) — the ChaCha20-Poly1305 AEAD standard; read §2.8 (the AEAD construction) and the security-considerations section. Cite it as the alternative-AEAD reference in the same ADR.
- [RFC 8032 — Edwards-Curve Digital Signature Algorithm (EdDSA)](https://www.rfc-editor.org/rfc/rfc8032) — the Ed25519 standard. Read the introduction and §8 (security considerations, including why deterministic signatures sidestep the nonce-reuse class of failures). The standard your signature ADR cites.
- [RFC 9106 — Argon2 Memory-Hard Function for Password Hashing](https://www.rfc-editor.org/rfc/rfc9106) — the Argon2 standard. Read §4 (parameter choice) and §7.4 (the two RECOMMENDED parameter profiles). Your password-KDF ADR cites this for the *parameters*, not just the algorithm name.

**Turning the standard into a defensible default (~45 min)**
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) — the practitioner translation of RFC 9106 into concrete minimums (Argon2id m=19 MiB/t=2/p=1, scrypt N=2¹⁷, bcrypt work factor ≥ 10) and the order to prefer them in. Read it as the "current minimum" floor your KDF ADR must meet or beat — and note the re-benchmark-on-your-hardware advice.

## Key concepts

- The ADR is the artifact: **Context** (forces) → **Options** → **Decision** (active voice, "we will…") → **Consequences** (positive *and* negative) → **"what would change this"** (the crypto-agility trigger).
- The crypto-specific field is **"what would change this decision"** — a broken primitive, a new standard (PQC), a perf ceiling, a compliance shift — and it is what module 11's migration reads first.
- **AEAD:** AES-GCM (fast with AES-NI) vs ChaCha20-Poly1305 (constant-time in software); both die on nonce reuse — the *consequence* line is the nonce-uniqueness guarantee, cited to NIST SP 800-38D / RFC 8439.
- **Signatures:** Ed25519 (modern default, deterministic, RFC 8032) vs ECDSA (when mandated) vs RSA (legacy interop); the pivot is greenfield-vs-legacy, and PQC is the "what would change this".
- **Password KDF:** Argon2id (RFC 9106) with *concrete tuned parameters* — the parameters are the decision; bcrypt/scrypt as documented fallbacks, OWASP minimums as the floor.
- **Secrets backend:** Vault (runtime broker) vs SOPS+age (secrets-in-git) vs cloud KMS (managed envelope) — decided by deployment model; the consequence is always the ops/lock-in line.
- **A recommendation with only upsides is the tell of an unreviewed ADR** — the negatives must be as specific as the positives.

## AI acceleration

An AI model is genuinely strong at this task's first draft: ask it to populate the ADR skeleton and the
options/trade-offs table for each of the four decisions, and it will produce a fluent, well-structured
starting point in seconds. That fluency is exactly the trap. This is the Type-14-adjacent caution the
whole track has been building toward: **a model will state crypto "facts" with total confidence and get
the load-bearing detail wrong** — it will recommend AES-GCM without the nonce-uniqueness consequence,
quote Argon2id parameters that are years out of date, or claim RSA is "post-quantum safe." Your job is
not to write the ADR from scratch; it is to *verify every claim against the standard you cited*. For
each line the model wrote, open the actual RFC/SP/cheat-sheet section and confirm it — does the GCM ADR
cite SP 800-38D §8 for the nonce rule, do the Argon2id parameters meet the RFC 9106 / OWASP floor, does
the "what would change this" field name a real trigger? The deliverable earns trust only when the
citation checks out. **AI drafts → you verify every claim against the standard → you own the decision.**
