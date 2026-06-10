# Lab 06 — PKI & Certificate Management

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/06-pki-certificates
make up        # start step-ca container
make demo      # init CA, issue leaf cert, verify chain, show OCSP revocation
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally. No internet connection required.

## Scenario

Meridian Financial is deploying mutual TLS (mTLS) between its internal microservices. Your
job: stand up a private CA with `step-ca`, issue service certificates, verify the chain, and
demonstrate certificate revocation — the complete PKI lifecycle for an mTLS programme.

## Do

1. [ ] `make demo` — watch the full sequence: CA initialisation, leaf certificate issuance,
   chain verification, OCSP query, and revocation. Note the certificate fields printed at
   each step.

2. [ ] `make shell` and issue a leaf certificate from the running CA with `step ca certificate`
   (you'll need the CA URL, the root cert, and a provisioner). Inspect the issued cert with
   `step certificate inspect` / `openssl x509`: what is the default validity period, and what
   SAN was included?

3. [ ] Verify the leaf against the root (`step certificate verify`) and confirm it passes.
   Then corrupt a byte of the PEM and verify again — what error does chain verification produce,
   and what does that tell you about how the signature is checked?

4. [ ] Revoke the leaf certificate through the CA, then query its status to confirm the
   revocation took effect. What status is returned, and what serial number identifies the
   revoked cert?

5. [ ] Issue a second certificate with a deliberately short validity window (a few minutes) and
   read back its `notAfter`. Why do short-lived certificates reduce reliance on revocation
   infrastructure?

6. [ ] Inspect the root CA certificate and identify: the `basicConstraints` extension (CA:TRUE),
   the `keyUsage` extension (keyCertSign, cRLSign), and the self-signed signature. Write a
   one-paragraph explanation of why these extensions distinguish a CA certificate from a leaf.

## Success criteria — you're done when

- [ ] You issued a leaf certificate and verified the chain against the root CA.
- [ ] You confirmed that a corrupted certificate fails chain verification.
- [ ] You revoked a certificate and confirmed the OCSP response shows "revoked".
- [ ] You issued a short-lived (5-minute) certificate and can explain why it reduces revocation dependence.

## Deliverables

`pki-analysis.md` — the certificate fields (SAN, validity, basicConstraints) from your leaf
cert, the revocation evidence (serial number + OCSP response), and the short-lived certificate
argument. Commit it.

## Automate & own it

**Required.** Write a shell script `cert-expiry-check.sh` that: takes a certificate file as
argument, reads the `notAfter` date with `openssl x509 -noout -enddate`, and exits non-zero
if the certificate expires within 30 days. Have an AI draft the date arithmetic in bash or
Python; you verify the exit code is correct for both "expiring soon" and "valid for 6 months"
cases.

## AI acceleration

Ask an AI: "What does the X.509 basicConstraints extension do, and why is `CA:FALSE` on a
leaf certificate important for preventing mis-issuance?" Verify the answer against RFC 5280
Section 4.2.1.9. Then check your issued leaf certificate to confirm `CA:FALSE` is set
(`openssl x509 -text -in /tmp/leaf.crt -noout | grep "CA:"`).

## Connects forward

The private CA you stood up here is the trust anchor for the mTLS configuration that the
track capstone deploys. Module 10 (Auditing Applied-Crypto Failures) includes certificate
audit checks — expired certificates, weak signature algorithms, missing OCSP stapling — as a
structured finding category.

## Marketable proof

> "I stood up a step-ca private CA, issued and revoked certificates, verified the chain, and
> demonstrated OCSP-based revocation — the PKI lifecycle for an internal mTLS programme."

## Stretch

- Configure an ACME provisioner in step-ca and use `certbot` (or `step` in ACME mode) to
  automatically issue and renew a certificate. This is the automation pattern that eliminates
  manual certificate management.
- Research Certificate Transparency (CT): what is a CT log, why does Chrome require certificates
  to be CT-logged, and what is the security benefit? Look up `step-ca`'s CT integration.
