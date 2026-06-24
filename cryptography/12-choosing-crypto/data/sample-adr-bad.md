# ADR-0003: Password KDF

*Status: Accepted*
*Date: 2026-06-22*

> Deliberately BROKEN example — `adr-lint.py` must FAIL this file. It exists so
> you can prove the gate fires on bad input, not just passes on good. It trips
> three checks: no standard cited, an empty Consequences section, and a missing
> "What would change this" section.

## Context

Corp Notes authenticates users with passwords, so we need a password hashing
KDF.

## Options

Argon2id, bcrypt, scrypt. Argon2id is the modern recommendation.

## Decision

Use Argon2id. It's the current best practice and won the Password Hashing
Competition, so it's the obvious pick.

## Consequences
