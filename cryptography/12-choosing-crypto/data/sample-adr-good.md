# ADR-0001: AEAD cipher for note-body encryption at rest

*Status: Accepted*
*Date: 2026-06-22*

> Worked example ADR — passes `adr-lint.py`. Use it as the shape your own four
> ADRs should take, not as text to copy: your service, your constraints.

## Context

Meridian Notes encrypts note bodies at rest before they hit the datastore. The
primary path runs as Linux containers on modern x86-64 servers (AES-NI present);
a small slice of traffic terminates on older ARM edge devices without AES
hardware acceleration. We need one AEAD for the at-rest envelope. No FIPS-140
requirement today, but a federal customer is likely within two years.

## Options

The real axis is hardware acceleration vs constant-time software:

- **AES-256-GCM** — fastest where AES-NI exists (the x86-64 servers), the
  industry default, and FIPS-approvable. Its sharp edge is operational: GCM is
  catastrophic on nonce reuse.
- **ChaCha20-Poly1305** — constant-time in software with no special hardware, so
  it wins on the AES-NI-less ARM edge, and it is more forgiving of
  implementation mistakes. Not yet on the FIPS-approved list.

## Decision

Use **AES-256-GCM** for the primary x86-64 path, per **NIST SP 800-38D** (and
**RFC 8439** documents ChaCha20-Poly1305 as the fallback profile for the ARM
edge). AES-NI makes GCM both the fastest and the FIPS-forward choice for the
bulk of traffic.

## Consequences

- **Nonce-uniqueness guarantee (load-bearing):** every encryption uses a unique
  96-bit IV constructed as a per-key monotonic counter persisted in the KMS data
  key context; we never use random IVs at this volume. **NIST SP 800-38D §8**
  states why: a single nonce repetition under one key leaks the authentication
  subkey and breaks confidentiality of the colliding messages — not a graceful
  degradation, a total break.
- ARM edge devices pay a software-AES penalty; Consequences accepts this for the
  minority path, with ChaCha20-Poly1305 (RFC 8439) selectable there.
- A second cipher in the codebase is operational surface we must test on both.

## What would change this

- A confirmed **FIPS-140** requirement that excludes our GCM implementation, or
  that forces a validated module — revisit the whole envelope.
- The ARM edge becoming the *majority* of traffic — promote ChaCha20-Poly1305 to
  primary.
- Any inability to guarantee nonce uniqueness at scale — switch to a
  nonce-misuse-resistant AEAD (AES-GCM-SIV).
