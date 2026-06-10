# Module 06 — PKI & Certificate Management

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *Certificates solve the "who are you talking to" problem — the chain of trust is only as strong as the weakest CA in it.*

## Why this matters

Public Key Infrastructure is the mechanism by which TLS's authenticity guarantee works. Without a PKI, a server can prove it has a keypair but cannot prove it is the server you intended to connect to — a man-in-the-middle attacker could substitute their own keypair. The certificate chain answers the "is this the right server?" question by linking the server's public key to a trusted authority's signature. Understanding how certificate chains work, how CAs issue and revoke certificates, and how to run a private CA is essential for engineers who operate TLS services, code-signing pipelines, or mutual TLS (mTLS) authentication.

## Objective

Use `step-ca` to initialise a private Certificate Authority, issue a leaf certificate, verify the chain, and demonstrate OCSP-based revocation — showing the complete certificate lifecycle that a production PKI programme operates.

## The core idea

A certificate chain is a delegation of trust. At the root is a self-signed CA certificate — the trust anchor, whose public key is distributed to clients out-of-band (in a browser's trust store, in an OS keychain, or in a TLS client's configuration). The root CA signs intermediate CA certificates; the intermediate CA signs leaf (end-entity) certificates. This three-tier structure separates the high-value root CA (which can be offline and air-gapped) from the operational intermediate CA (which issues certificates day-to-day), limiting the blast radius of a CA private key compromise.

Certificate fields matter for security. The `subjectAltName` extension (SAN) carries the hostname(s) the certificate is valid for — the Common Name (CN) is deprecated for hostname validation and ignored by modern TLS implementations. The `notBefore` and `notAfter` fields bound the validity period; a certificate with a 10-year validity is a certificate whose private key needs to be kept secret for 10 years, which is why best practice has moved toward 90-day certificates (as Let's Encrypt uses). The `basicConstraints` extension with `CA:TRUE` marks a certificate as a CA certificate capable of signing others — a leaf certificate without this constraint cannot be used as a CA, which is why a stolen leaf certificate cannot be used to sign arbitrary certificates.

Revocation is the mechanism for invalidating a certificate before its `notAfter` date. Two protocols exist. CRL (Certificate Revocation List) is a signed list of revoked serial numbers distributed by the CA and cached by clients. OCSP (Online Certificate Status Protocol) is a real-time query: the client sends the certificate's serial number to the CA's OCSP responder and receives a signed "good" or "revoked" response. OCSP Stapling moves the OCSP query to the server — the server periodically fetches and caches the OCSP response and staples it to the TLS handshake, eliminating the privacy and latency issues of client-side OCSP queries. In practice, revocation is imperfect: CRL caching, OCSP soft-fail (browsers continue if OCSP is unreachable), and the lack of universal OCSP stapling deployment mean revocation is not a reliable last line of defence — which is why short-lived certificates and automated renewal are the modern answer.

Running a private CA with `step-ca` is the practical equivalent of what every PKI-using organisation should have: an internal CA for mTLS between services, for developer certificate issuance, and for internal HTTPS without depending on a public CA's pricing or policies. `step-ca` is an ACME-compatible CA server — internal services can use `certbot` or any ACME client to obtain and auto-renew certificates from it, the same workflow as Let's Encrypt but with a private trust anchor.

## Learn (~4 hrs)

**PKI and X.509**
- [Everything you should know about certificates and PKI but are too afraid to ask (SmallStep blog)](https://smallstep.com/blog/everything-pki/) — the clearest conceptual treatment of the certificate chain, extensions, and trust model available; read the full post (~45 min).
- [RFC 5280 — X.509 PKI Certificate and CRL Profile](https://www.rfc-editor.org/rfc/rfc5280) — Sections 4.1–4.2 (certificate structure and extensions) and Section 6 (path validation); the normative reference.

**step-ca**
- [step-ca documentation — Getting Started](https://smallstep.com/docs/step-ca/) — read the Installation, Initialisation, and Certificate Issuance sections.
- [step CLI documentation](https://smallstep.com/docs/step-cli/) — the command-line tool for interacting with step-ca; read the `step ca certificate` and `step certificate inspect` commands.

**Revocation**

## Key concepts

- Certificate chain: root CA (offline, trust anchor) → intermediate CA (operational) → leaf certificate (end-entity).
- SAN (subjectAltName) is the hostname validation field; CN is deprecated for this purpose.
- Short validity periods + automated renewal > long-lived certificates + revocation.
- OCSP Stapling: server fetches and caches OCSP response, staples it to TLS handshake — eliminates client-side OCSP queries.
- step-ca: ACME-compatible private CA; same automated renewal workflow as Let's Encrypt.

## AI acceleration

Ask an AI to explain what each field in an X.509 certificate does (paste the output of `openssl x509 -text -in cert.pem -noout`). Use the explanation to understand each extension before the lab. Verify the extension descriptions against RFC 5280 Section 4.2 — does the model's description match the RFC's normative requirement?
