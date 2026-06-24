# Lab 12 — Choosing Your Crypto: writing the ADRs

*Type 11 · Decision / ADR. [← Back to the module concept](README.md)*

**Type 11 · Decision / ADR.** You are handed a new service and its constraints, and you must make
its four core cryptographic choices — AEAD cipher, signature scheme, password KDF, secrets backend —
and *defend each one as an Architecture Decision Record*: options, honest trade-offs, the decision,
the consequences, and what would change the decision, each citing the current standard. The
deliverable is the set of ADRs. No grader; you verify your own work against the success criteria below
and against the standards themselves.

> **Lab environment: to be built & validated.** This is primarily a writing/decision artifact and
> needs almost no environment. The only runnable piece is the **Automate & own it** linter (below);
> if a `plaintext-labs/cryptography/12-choosing-crypto/` Docker/Make scaffold is added later, it is
> **to be built and validated** (`make up && make demo && make down` green on a Linux runner) before
> it earns a `.ci-demo` marker. Until then, treat this as a local writing exercise — Python 3 is the
> only dependency for the linter.

## Setup

This is a **decision/writing exercise** — no containers required to produce the deliverable. You need:

- A text editor and a place to commit Markdown (your own portfolio repo).
- The four standards open in tabs (you will cite them, so you must read them): NIST SP 800-38D §8,
  RFC 8439, RFC 8032, RFC 9106 §7.4, and the OWASP Password Storage Cheat Sheet — all linked from the
  [module concept](README.md).
- Python 3 for the **Automate & own it** linter.

Start from a real ADR template (copy Nygard's or MADR from the
[joelparkerhenderson/architecture-decision-record](https://github.com/joelparkerhenderson/architecture-decision-record)
repo) rather than inventing a skeleton.

> This is a document and design exercise. No real systems or secrets are accessed.

## Scenario

You are the security engineer bootstrapping **"Corp Notes"**, a new multi-tenant note-taking
backend the team is building greenfield. The constraints are real:

- **Platform:** Runs as Linux containers on modern x86-64 servers (AES-NI present). A small slice of
  traffic terminates on older ARM edge devices without AES acceleration.
- **What needs crypto:**
  - Note bodies are **encrypted at rest** before they hit the datastore (you choose the AEAD).
  - The service issues **signed tokens** to clients and signs its own software releases (you choose the
    signature scheme). There is one legacy partner that can only verify RSA signatures.
  - Users authenticate with **passwords** (you choose the KDF and its parameters).
  - The service needs **database credentials and an API key at runtime**, and the team runs everything
    through GitOps (you choose the secrets backend).
- **Team:** 3 engineers, no dedicated platform team. Cloud-agnostic for now (no single-cloud lock-in
  mandate yet).
- **Compliance:** No FIPS-140 requirement today, but a federal customer is "likely within two years."
- **Forward pressure:** Leadership has read the post-quantum headlines and wants to know the migration
  story for anything long-lived.

## Do

1. [ ] **Pick the template and the fields.** Copy an ADR template and confirm it has all five fields
   this track requires: **Context · Options · Decision · Consequences · What would change this**. Add
   the last field if the template lacks it — it is the crypto-agility hook.

2. [ ] **Write ADR-001 — AEAD cipher (AES-GCM vs ChaCha20-Poly1305).** State the options and the real
   axis (hardware acceleration vs constant-time software). Make the **decision** for the *primary*
   x86-64 path and address the ARM-edge slice in Consequences. **The load-bearing consequence is the
   nonce-uniqueness guarantee** — write down exactly how you guarantee a unique IV and cite **NIST SP
   800-38D §8** for why repetition is catastrophic. "What would change this": name the trigger.

3. [ ] **Write ADR-002 — signature scheme (Ed25519 vs ECDSA vs RSA).** Decide for the token/release
   path and *explicitly* handle the legacy RSA-only partner (does the whole service follow them, or do
   you dual-issue?). Cite **RFC 8032** for Ed25519. In "what would change this", name the post-quantum
   trigger and the migration target you expect to record next (the NIST PQC signature suite).

4. [ ] **Write ADR-003 — password KDF (Argon2id vs bcrypt vs scrypt), *with parameters*.** A KDF ADR
   with no cost factor is incomplete. Record concrete tuned parameters at or above the OWASP floor
   (Argon2id m≥19 MiB, t≥2, p=1; or a higher RFC 9106 §7.4 profile), cite **RFC 9106** and the **OWASP
   Password Storage Cheat Sheet**, and write the re-benchmark rule (target verify time on *your*
   hardware) into Consequences.

5. [ ] **Write ADR-004 — secrets backend (Vault vs SOPS+age vs cloud KMS).** Decide against the GitOps
   + cloud-agnostic + 3-engineer constraints. The honest Consequences line is the ops/lock-in cost the
   chosen tool's marketing omits. Tie back to what you built in module 07.

6. [ ] **Cross-check the "likely federal customer" against every ADR.** A future FIPS-140 requirement
   touches at least the KDF and possibly the AEAD/signature choices. Add a one-line note to each
   affected ADR's "what would change this" — this is the discipline of writing the trigger *before* it
   fires.

7. [ ] **Run your linter (next section) over the four ADRs** and fix anything it flags until all four
   pass.

## Success criteria — you're done when

- [ ] Four ADRs exist (AEAD, signature, KDF, secrets backend), each with all five fields populated.
- [ ] **Every ADR cites a specific current standard** (SP 800-38D / RFC 8439 / RFC 8032 / RFC 9106 /
  OWASP) — by document *and* the relevant section, not a bare name.
- [ ] The AES-GCM ADR's Consequences section states the **nonce-uniqueness guarantee** explicitly.
- [ ] The KDF ADR records **concrete parameters** meeting or beating the OWASP floor, plus the
  re-benchmark rule.
- [ ] Every ADR's **Consequences** lists real negatives (not only upsides) and **"what would change
  this"** names a concrete trigger.
- [ ] The signature and KDF ADRs name the post-quantum / FIPS triggers respectively.

*(Honor system — no grader. Check your own ADRs against the list and against the standards you cited;
the test is whether a reviewer who knows the RFCs could be talked out of any decision. If a
Consequences section reads like a vendor datasheet, you're not done.)*

## Deliverables

`adr/` — a directory of four Markdown ADRs (`0001-aead-cipher.md`, `0002-signature-scheme.md`,
`0003-password-kdf.md`, `0004-secrets-backend.md`), committed to your own portfolio repo. This is a
portfolio artifact: it demonstrates you can make applied-crypto decisions against real constraints,
cite the governing standard, and record honest consequences and a crypto-agility trigger — the exact
skill the track capstone grades. Lab artifacts (any benchmark output, throwaway keys) stay out of the
commit.

## Automate & own it

**Required.** Write a small linter — `adr-lint.py` (Python 3, no dependencies) — that reads each ADR
Markdown file and **fails** (non-zero exit, with the reason) if an ADR:

- is missing any of the five required sections (Context / Options / Decision / Consequences / What
  would change this), or
- contains no citation of a recognised standard (a regex for `RFC \d+`, `SP 800-\d+`, or `OWASP`), or
- has an empty Consequences or "What would change this" section.

This is the **Judgment-as-Code** move: you are encoding "every crypto decision must cite a standard and
own its consequences" as a check that *fails the build*, so the discipline survives the next tired
Friday. Have a model draft the linter, then **review every line** — does the section-detection actually
match your headings? Does the standard regex reject a plausible-looking ADR that names "AES" but cites
no document? Run it over your four ADRs *and* over a deliberately broken ADR (drop the citation, empty
the Consequences) to prove it fails on the bad input, not just passes on the good. **AI drafts → you
review every line → you own the gate.**

## AI acceleration

Models are excellent at populating ADR skeletons and options tables from a prose brief — use one to
draft all four, fast. Then do the thing this whole track has been training: **verify every crypto claim
against the standard you cited.** Open SP 800-38D §8 and confirm the nonce rule the model wrote; open
RFC 9106 §7.4 and confirm the Argon2id parameters aren't a hallucinated or stale set; check that the
model didn't quietly claim RSA is post-quantum safe. Ask it explicitly for the *negative* consequences
of each decision — a draft that lists only benefits is not being honest with you. The ADR earns trust
when its citations check out and its negatives are as specific as its positives.

## Connects forward

- Module 11 (PQC & Crypto-Agility Migration) reads the **"what would change this"** field of these
  ADRs first — the signature and AEAD ADRs you wrote here are the inventory and the trigger list that a
  post-quantum migration starts from. An ADR that named the PQC trigger is a migration that's already
  half-planned.
- The track **capstone** grades "cites the standard for each decision" — these ADRs are the artifact
  that satisfies it. Reuse the linter as the capstone's pre-submission gate.

## Marketable proof

> "I can make a service's core cryptographic choices — AEAD, signatures, password KDF with concrete
> parameters, secrets backend — and defend each one as an Architecture Decision Record that cites the
> governing standard, records honest trade-offs, and names the trigger that would change the decision.
> I encode that 'cite-the-standard' discipline as a linter that fails the build."

## Stretch

- Add **ADR-005 — TLS configuration profile** (cipher suites, minimum version, key-exchange groups),
  citing the relevant Mozilla SSL Configuration guidance and your module 05 work.
- Extend `adr-lint.py` to *warn* (not fail) when a long-lived asymmetric decision (RSA/ECDSA/Ed25519)
  has a "what would change this" field that does **not** mention post-quantum — a crypto-agility
  nudge baked into the gate.
