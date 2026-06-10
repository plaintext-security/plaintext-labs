# Module 10 — Auditing Applied-Crypto Failures

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 08 — Cryptography, PKI & Secrets]** — *Applied cryptography fails in patterns — knowing the pattern tells you exactly where to look in an audit.*

## Why this matters

Cryptography Failures is #2 on the OWASP Top 10 (2021). The failures are not mathematical — the algorithms themselves are sound. They are implementation and configuration failures: using the wrong mode, reusing a nonce, hardcoding a key, generating an IV from a predictable source, trusting an expired certificate. These failures are predictable precisely because the set of ways to misapply well-understood primitives is finite and documented. A practitioner who knows the failure taxonomy can audit a system's cryptographic posture methodically — not by guessing, but by running through the known failure categories and confirming or ruling out each one.

## Objective

Run `testssl.sh` against a matrix of TLS configurations with varying weakness levels, score the findings, map each finding to an OWASP or NIST failure category, and produce a structured audit report — the deliverable of a real applied-crypto assessment.

## The core idea

Applied cryptography auditing has two distinct layers. The configuration audit checks what algorithms, modes, and protocols are configured — this is what testssl.sh, OpenSSL s_client, and cipher suite scanners do. The implementation audit checks how those algorithms are used in code — this requires source review, dynamic analysis, or both. Both layers produce findings in the OWASP Cryptographic Storage Cheat Sheet's taxonomy: insufficient algorithm (MD5, DES), missing authentication (CBC without MAC), weak key derivation (password used directly as key), nonce reuse, hardcoded key or IV, missing certificate validation, expired or untrusted certificates. Each category maps to a specific audit check and a specific remediation.

The finding severity in a crypto audit is not just about the CVSS score of the algorithm. Context matters enormously. A TLS 1.0 cipher suite on a server that is only accessible from an internal network segment with no adversaries capable of a BEAST attack is a LOW finding in practice, even though TLS 1.0 is deprecated. The same cipher suite on an internet-facing login endpoint is CRITICAL. An expired certificate on an internal health-check endpoint is MEDIUM; the same expiry on the public API that customer applications talk to is HIGH because it causes client errors and may be a sign of certificate lifecycle failure. Assigning severity requires understanding the network exposure, the sensitivity of the data in transit, and the exploitability of the finding in context.

The remediation delta is the practitioner output that distinguishes an audit from a vulnerability scan dump. For each finding, the audit documents: current state (what is configured), recommended state (what the finding requires), effort estimate (a two-line nginx config change vs a code change requiring redeployment), and re-test method (how to confirm the fix). An audit report that only lists findings is half-done; the delta report that pairs each finding with its specific fix is what enables the engineering team to act without another meeting.

The cumulative picture — all three TLS configurations audited, findings tallied, severity distribution charted — is also the mechanism for prioritisation. A system with one CRITICAL (TLS 1.0 on an internet endpoint) and twenty LOW findings (deprecated ciphers on internal services) has a clear remediation priority: fix the CRITICAL first, schedule the LOWs in the next hardening sprint. The crypto audit's output is a prioritised remediation backlog, not a pass/fail judgment.

## Learn (~4 hrs)

**OWASP Cryptographic Failure taxonomy**
- [OWASP Top 10 — A02:2021 Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/) — the canonical failure taxonomy; read the full entry including the example attack scenarios.
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) — the practitioner reference for storage-layer failures; read the full page.

**testssl.sh (revisit from module 05)**
- [testssl.sh GitHub — Severity Rating Documentation](https://github.com/testssl/testssl.sh) — read the README section on severity ratings; understand how the tool assigns CRITICAL, HIGH, MEDIUM, LOW, and INFO severity to each finding.

**NIST guidance on cryptographic algorithm deprecation**
- [NIST SP 800-131A Rev 2 — Transitioning the Use of Cryptographic Algorithms](https://csrc.nist.gov/pubs/sp/800/131/a/r2/final) — the authoritative list of deprecated and disallowed algorithms; read Tables 1–4 for the algorithm transition schedule.

**Applied crypto failure case studies**
- [Moxie Marlinspike — SSL and the Future of Authenticity (DEF CON 19)](https://www.youtube.com/watch?v=Z7Wl2FW2TcA) — a practitioner talk on real-world PKI and TLS failures; ~50 min; explains why the "padlock" is not what users think it is.

## Key concepts

- Applied crypto fails in finite, documented patterns: wrong mode, nonce reuse, hardcoded key, missing auth, weak KDF, expired/untrusted cert.
- Configuration audit (testssl.sh, cipher scanner) vs implementation audit (code review, dynamic analysis) — both are required.
- Severity depends on context: network exposure, data sensitivity, exploitability — not just the CVSS score of the algorithm.
- Remediation delta: current state, recommended state, effort estimate, re-test method — for each finding.
- The audit output is a prioritised backlog, not a pass/fail.

## AI acceleration

For each finding in your testssl.sh output, ask an AI: "What is this TLS finding, which OWASP
cryptographic failure category does it map to, and what is the specific nginx or server
configuration that fixes it?" Use the answer to write the "recommended state" and "re-test
method" columns in your audit table. Verify the fix against the Mozilla SSL Configuration
Generator — does the generated config match the AI's recommendation?
