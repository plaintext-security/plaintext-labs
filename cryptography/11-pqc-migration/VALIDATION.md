# Validation — Module 11 (PQC Migration)

This env was scaffolded without a Docker run (the author cannot run Docker). It
follows the repo conventions but **has not been executed**; validate it before
the module counts as done, and only then consider a `.ci-demo` marker.

## One-line validation

```bash
make up && make demo && make down
```

`make demo` is deterministic: it resets to the classical baseline, shows the
modern client on classical (the verify gate is expected to fail there), runs
`make migrate`, then runs the fail-closed `make verify` (modern must negotiate
`X25519MLKEM768`, legacy must stay classical, both must return HTTP 200) and a
final before/after inventory.

## Host prerequisite the maintainer MUST confirm

**OpenSSL >= 3.5 with native ML-KEM in the server + modern client images.**
The base image for both is `alpine:3.22`, which ships OpenSSL 3.5.x (ML-KEM
native — no third-party provider). A build without ML-KEM is the exact
silent-fallback failure this lab teaches, so confirm it explicitly:

```bash
# Inside the modern client, this must negotiate the hybrid group — NOT fall back:
docker compose exec modern sh -c \
  'echo Q | openssl version && echo Q | openssl s_client -connect server:443 -tls1_3 -groups X25519MLKEM768 2>&1 | grep -i "Negotiated TLS1.3 group"'
# Expect: OpenSSL 3.5.x  and  "Negotiated TLS1.3 group: X25519MLKEM768" (after `make migrate`)
```

The legacy client is `alpine:3.18` (OpenSSL 3.1.x, no ML-KEM) on purpose — it
must NOT be able to offer the hybrid group; that contrast is the interop proof.

## Fallback if `alpine:3.22` / OpenSSL 3.5 is unavailable

If your registry/proxy cannot pull `alpine:3.22`, or its OpenSSL turns out to
lack ML-KEM, fall back to **OpenSSL 3.0–3.4 + oqs-provider**:

- Use `openquantumsafe/oqs-ossl3` (or build openssl 3.x with the OQS provider
  loaded via `openssl.cnf`) for the server and modern client images.
- With oqs-provider the hybrid group is commonly named `X25519MLKEM768` (newer
  oqs-provider) or historically `x25519_mlkem768` / `x25519_kyber768` — confirm
  the exact id with `openssl list -kem-algorithms` / `-groups` and adjust the
  group strings in `data/nginx-hybrid.conf`, `data/handshake-check.sh`, and
  `data/crypto-inventory.sh` accordingly.

With `alpine:3.22` no provider is needed; prefer that path.

## Do NOT add `.ci-demo`

Not added by design. Add it only once `make up && make demo && make down` is
green on a Linux runner AND the runner's OpenSSL genuinely negotiates
`X25519MLKEM768` (verified per the prerequisite above).
