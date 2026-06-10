# Module 05 — TLS Deep Dive

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *TLS is the applied cryptography you interact with hundreds of times per day — reading the handshake tells you everything about a connection's actual security.*

## Why this matters

TLS protects nearly all internet traffic, and it is the single most widely deployed cryptographic protocol in existence. It is also one of the most frequently misconfigured: TLS 1.0 and 1.1 are deprecated but still found in production, weak cipher suites coexist with strong ones, and certificate configurations fail in ways that undermine the authenticity guarantee completely. Auditing a TLS configuration is a day-one skill for a security engineer — knowing what `testssl.sh` reports and what each finding means for actual risk is the practitioner competency this module builds.

## Objective

Configure a local nginx server with both a weak and a strong TLS configuration, scan both with `testssl.sh`, and interpret the findings — connecting each to the underlying cryptographic property it tests.

## The core idea

A TLS session establishes three properties: the server's identity (verified via the certificate chain), a shared secret (negotiated via a key exchange), and a secure channel (encrypted and authenticated using that shared secret). The TLS handshake is the negotiation that establishes all three. In TLS 1.3, the handshake is simplified and the protocol mandates: ECDHE for key exchange (forward secrecy), AEAD cipher suites only (no CBC, no stream ciphers), and SHA-256 or better for the hash function. Every handshake in TLS 1.3 is forward-secret and authenticated by construction. TLS 1.2 is configurable — and therefore misconfigurable.

Cipher suite selection in TLS 1.2 is the primary source of audit findings. A cipher suite is a four-algorithm package: key exchange + authentication + bulk encryption + MAC. `TLS_RSA_WITH_AES_128_CBC_SHA` uses static RSA key exchange (no forward secrecy), AES-128-CBC (no authentication, vulnerable to padding oracle), and SHA-1 MAC (deprecated). `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384` uses ECDHE (forward secrecy), AES-256-GCM (authenticated encryption), and SHA-384. The first suite appears on the server, an audit tool flags it, and a fix requires removing it from the cipher list. Understanding the cipher suite string is the skill that lets you fix the finding rather than just report it.

Certificate configuration problems are a distinct category. A self-signed certificate fails the authenticity check — the client can verify the cryptographic signature but cannot verify that the signing CA is trustworthy. A certificate with an expired `notAfter` date fails the validity check. A certificate whose `subjectAltName` doesn't include the hostname the client connected to fails the identity check. A certificate signed with SHA-1 (deprecated signature algorithm) may be rejected by modern browsers. Each of these is a TLS audit finding with a specific remediation that has nothing to do with cipher suites. `testssl.sh` checks all of them in a single scan.

The distinction between protocol version, cipher suite, and certificate is the mental model that makes a TLS audit readable. `testssl.sh` outputs all three categories of findings, and a practitioner who reads the output can classify each finding, assess its severity (is this a theoretical weakness or an active attack vector?), and propose the specific configuration change that fixes it. This is the applied skill — not TLS trivia, but the ability to connect a scanner finding to a concrete configuration change.

## Learn (~5 hrs)

**TLS internals**
- [The Illustrated TLS 1.3 Connection (Josh Davies)](https://tls13.xargs.org/) — an interactive byte-by-byte breakdown of a real TLS 1.3 handshake; read the entire page (~1 hr). This is the clearest deep-dive on TLS that exists.
- [RFC 8446 — TLS 1.3 (IETF)](https://www.rfc-editor.org/rfc/rfc8446) — Sections 1–4 (introduction, record layer, handshake) and Appendix C (implementation notes); read for the normative requirement understanding.

**testssl.sh**
- [testssl.sh documentation (drwetter)](https://testssl.sh/) — read the README and the output format section; understand what each category of check means.
- [testssl.sh on GitHub](https://github.com/testssl/testssl.sh) — browse the `doc/` directory for cipher suite interpretation guidance.

**TLS configuration best practices**
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/) — the tool that generates nginx/Apache/HAProxy TLS configs for modern/intermediate/old profiles; understand what each profile means and when to use each.
- [SSL Labs grading criteria](https://github.com/ssllabs/research/wiki/SSL-Server-Rating-Guide) — how A+/A/B grades map to specific cipher suite and certificate findings.

## Key concepts

- TLS handshake establishes: server identity (certificate chain), shared secret (key exchange), secure channel (AEAD encryption).
- TLS 1.3: ECDHE + AEAD only — forward secrecy and authenticated encryption by construction.
- Cipher suite string: key exchange + authentication + bulk encryption + MAC — each component maps to a security property.
- Certificate findings are separate from cipher suite findings: validity, trust chain, CN/SAN, signature algorithm.
- `testssl.sh` classifies findings by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO) — map each to a specific property.

## AI acceleration

Paste a `testssl.sh` finding into an AI and ask it to explain: what cryptographic property the finding tests, what an attacker could do if this finding is exploited, and the nginx configuration change that fixes it. Then verify the nginx config change against the [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/) — does it appear in the modern profile? AI explains the finding; the Mozilla generator is the configuration authority.
