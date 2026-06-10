# Cryptography, PKI & Secrets capstone — grading rubric

Self/peer/reviewer rubric for the Track 08 capstone. **Proficient is the bar to
ship; exemplary is the portfolio piece.** Score each dimension independently.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **TLS configuration** | Ran `testssl.sh`, didn't interpret | Weak protocols/ciphers identified and explained, with the standard each violates | Re-tested after the fix; cites RFC 8446 / current NIST guidance per decision |
| **Certificate hygiene** | Checked expiry only | Chain, key strength, SAN, revocation reviewed against RFC 5280 | Issuance/renewal automated (step-ca/ACME); short-lived certs or rotation shown |
| **Secrets handling** | Found a secret, no remediation | Leaked/poorly-stored secrets found and moved to proper storage | History scrubbed, rotation done, detection wired to prevent recurrence |
| **Email auth** | Checked one of SPF/DKIM/DMARC | All three assessed with the policy gaps named | Recommends an enforce-mode rollout path with the risk of each step |
| **Audit report** | Findings without before/after | Each finding has evidence, a fix, and a re-test proving it | Severity-ranked, tool output attached; every claim has a test behind it |

## What "done" means

- [ ] Every dimension is at least **Proficient**.
- [ ] The deliverable is reproducible from what you committed.
- [ ] No secrets, captures, keys, or heavy artifacts in git history.
- [ ] Audit a system you own (a lab service, your own domain's DNS). Never commit private keys — the repo `.gitignore` blocks `*.pem`/`*.key`.
