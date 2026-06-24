# ADR-NNNN: <short decision title>

*Status: Proposed | Accepted | Superseded*
*Date: YYYY-MM-DD*

> Copy this skeleton for each crypto decision. It is a Nygard/MADR-style ADR
> with one Plaintext addition — **"What would change this"** — the crypto-agility
> hook. `adr-lint.py` fails the build if any of the five sections below is
> missing or if the ADR cites no standard, so keep all five and cite the
> governing document (RFC / NIST SP 800 / OWASP) by section, not by name alone.

## Context

What service, what constraint, what forces are in play. The platform, the
threat, the compliance horizon — everything that bounds the choice.

## Options

The realistic options and the *axis* that distinguishes them (not a feature
table). For each: what it buys you and what it costs.

## Decision

The choice, stated plainly, for the specific path it governs. Cite the standard
that backs it (e.g. RFC 8439 §2.8, NIST SP 800-38D §8, RFC 9106 §7.4, the OWASP
Password Storage Cheat Sheet).

## Consequences

The honest trade-offs — including the **negatives** the vendor datasheet omits.
For an AEAD, state the nonce-uniqueness guarantee. For a KDF, the concrete tuned
parameters and the re-benchmark rule. Never list only upsides.

## What would change this

The concrete trigger(s) that would reopen this decision: a post-quantum
migration, a FIPS-140 requirement, new hardware, a benchmark regression. Write
the trigger *before* it fires — this is the crypto-agility discipline.
