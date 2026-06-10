# Lab 10 — Auditing Applied-Crypto Failures

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/cryptography/10-auditing-crypto-failures
make up        # start three nginx instances with different TLS configs + testssl.sh
make demo      # scan all three configs, show the scoring delta between them
make shell     # drop into the testssl container
make down      # stop when done
```

> Everything runs locally. Three nginx servers on the Docker bridge network.

## Scenario

Meridian Financial has engaged you for a crypto posture audit of three internal services:
a legacy payment gateway (TLS 1.0, weak ciphers), a modernised API (TLS 1.2, mixed ciphers),
and the new microservice endpoint (TLS 1.3, strong config). Your deliverable: a structured
audit report mapping each finding to an OWASP failure category, a severity rating in context,
and a specific remediation.

## Do

1. [ ] `make demo` — watch testssl.sh scan all three servers. Note the finding count and
   severity distribution for each. This is the before/after matrix showing what "strong TLS
   configuration" looks like compared to a weak one.

2. [ ] `make shell` and scan each of the three servers (`nginx-legacy`, `nginx-modern`,
   `nginx-strong`) with `testssl.sh`, writing each result to its own JSON file.

3. [ ] Parse the three JSON files for severity counts (jq over the `.severity` field) and build
   a comparison table: server × severity level × finding count.

4. [ ] For each CRITICAL or HIGH finding in the legacy server, write one row in your audit
   report:
   - **Finding**: the testssl.sh finding name and ID.
   - **OWASP category**: which A02 subcategory it maps to (weak algorithm, missing auth,
     expired cert, etc.).
   - **Severity in context**: HIGH/CRITICAL/MEDIUM — with justification based on the service's
     network exposure and data sensitivity.
   - **Current state**: the specific nginx directive that causes the finding.
   - **Recommended state**: the corrected directive.
   - **Re-test method**: the specific testssl.sh check that confirms the fix.

5. [ ] Identify one finding from the legacy server that the modern server has also fixed —
   and one that the modern server still has. What does this tell you about the value of
   incremental TLS hardening vs full migration to TLS 1.3?

6. [ ] Confirm the strong server has no HIGH or CRITICAL findings — count them in its JSON
   output. If any remain, identify the root cause.

## Success criteria — you're done when

- [ ] You have a severity comparison table across all three servers.
- [ ] You have a structured finding table for the legacy server's HIGH/CRITICAL issues.
- [ ] Each finding maps to an OWASP failure category.
- [ ] The strong server has zero HIGH/CRITICAL findings.

## Deliverables

`crypto-audit-report.md` — your comparison table + finding table for the legacy server, with
OWASP mappings, contextual severity, and remediation. Commit it.

## Automate & own it

**Required.** Write a Python script `audit-score.py` that: takes a testssl.sh JSON output
file, counts findings by severity, and outputs a risk score (CRITICAL×10 + HIGH×5 + MEDIUM×1).
Compare scores across the three servers. Wire it into a CI check that fails if the score
exceeds a threshold. Have an AI draft the score formula; you verify it produces higher scores
for more severe configurations and lower scores for the strong server.

## AI acceleration

For each HIGH/CRITICAL finding in your legacy audit report, ask an AI: "Map this testssl.sh
finding to the OWASP Top 10 A02 Cryptographic Failures subcategory. Which specific failure
pattern is this?" Verify the mapping against the [OWASP A02 page](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/)
before including it in the report. AI drafts the mapping; OWASP is the authority.

## Connects forward

This module closes the cryptography track. The audit report format you produced here —
finding, OWASP category, contextual severity, remediation — is the same format used in the
track capstone audit of a complete system. The track capstone asks you to audit TLS, certificates,
secrets, and email authentication as an integrated assessment and produce a single remediation
backlog from all findings.

## Marketable proof

> "I ran a structured applied-cryptography audit across three TLS configurations using testssl.sh,
> mapped each finding to OWASP A02 Cryptographic Failures categories, assigned contextual
> severity, and produced a prioritised remediation report with specific nginx directives."

## Stretch

- Add a fourth target: a server with a self-signed certificate and no OCSP stapling. Add it
  to the comparison matrix and identify the new finding categories it introduces (certificate
  trust, missing stapling). How does the self-signed finding change if this is an internal-only
  service with a custom trust anchor?
- Research `sslyze`: how does it compare to testssl.sh, what Python API does it expose, and
  can you write a Python script that uses sslyze to automate the same audit checks? Build a
  one-page comparison of the two tools' strengths.
