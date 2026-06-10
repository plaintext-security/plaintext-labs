# Track 08 — Cryptography, PKI & Secrets: Capstone starter

> **Capstone scaffold — not a solution.** This is the skeleton for the Cryptography, PKI & Secrets
> capstone: a place to build the deliverable, plus the acceptance rubric you grade yourself
> against. The full prose, phase projects, and the rendered rubric live in the curriculum:
> [`tracks/08-cryptography/`](https://github.com/plaintext-security/plaintext/tree/main/tracks/08-cryptography).

## The capstone

Audit a small system's crypto posture: TLS configuration, certificate hygiene, secrets handling, and SPF/DKIM/DMARC — then fix each finding and re-test.

## What you build

1. A crypto-posture audit covering TLS config, certificate hygiene, secrets handling, and SPF/DKIM/DMARC.
2. A fix for each finding, expressed concretely (config, rotation, policy).
3. A re-test proving each fix, with before/after evidence.

## Layout

Drop your work under `submission/` (gitignored heavy artifacts stay out — see the repo
`.gitignore`). A suggested shape:

```
cryptography/capstone/
├── README.md          # this file — brief + acceptance criteria
├── rubric.md          # the grading rubric (also the ai_rubric source)
├── grade.yaml         # `make grade` — advisory rubric check
├── Makefile           # `make grade`
└── submission/        # YOUR work goes here
    submission/audit-report.md           # findings, fixes, before/after evidence
    submission/tls/                      # testssl.sh output before/after
    submission/certs/                    # chain review notes (no private keys)
    submission/email-auth.md             # SPF/DKIM/DMARC assessment
```

## How to use it

```bash
# from the repo root
cd cryptography/capstone
# ... build your deliverable under submission/ ...
make grade          # advisory self-check against the rubric
```

`make grade` is **advisory** — this capstone is a portfolio artifact judged by a human (you,
a peer, or a reviewer) against [`rubric.md`](rubric.md), not auto-graded. Set `AI_GRADER_CMD`
to get draft LLM feedback (see `../../scripts/README.md`).

## Acceptance criteria

**Proficient is the bar to ship; exemplary is the portfolio piece.** Grade every dimension
honestly — a strong report in one column doesn't excuse a gap in another.

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **TLS configuration** | Ran `testssl.sh`, didn't interpret | Weak protocols/ciphers identified and explained, with the standard each violates | Re-tested after the fix; cites RFC 8446 / current NIST guidance per decision |
| **Certificate hygiene** | Checked expiry only | Chain, key strength, SAN, revocation reviewed against RFC 5280 | Issuance/renewal automated (step-ca/ACME); short-lived certs or rotation shown |
| **Secrets handling** | Found a secret, no remediation | Leaked/poorly-stored secrets found and moved to proper storage | History scrubbed, rotation done, detection wired to prevent recurrence |
| **Email auth** | Checked one of SPF/DKIM/DMARC | All three assessed with the policy gaps named | Recommends an enforce-mode rollout path with the risk of each step |
| **Audit report** | Findings without before/after | Each finding has evidence, a fix, and a re-test proving it | Severity-ranked, tool output attached; every claim has a test behind it |

> Audit a system you own (a lab service, your own domain's DNS). Never commit private keys — the repo `.gitignore` blocks `*.pem`/`*.key`.
