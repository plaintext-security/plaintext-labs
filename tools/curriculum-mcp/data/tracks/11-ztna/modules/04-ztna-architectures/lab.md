# Lab 04 — ZTNA Architecture Decision: Meridian Financial

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **design exercise** — no containers needed. The scenario materials live in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/04-ztna-architectures
make demo      # prints the Meridian requirements and the scenario brief
```

The lab ships one seed file: `data/architecture-comparison.md` — a structured comparison of the
four ZTNA patterns with traffic flow diagrams, trust model descriptions, and blast-radius analysis.
Read it before starting the ADR exercise.

> This is a document and design exercise. No real systems are accessed.

## Scenario

Meridian's security team has completed the ZT gap analysis (Lab 01) and must now recommend a
delivery architecture to the CISO. The constraints are real:

- **Applications:** 60% SaaS (Salesforce, Workday, Slack), 30% on-premises (core banking,
  legacy reporting, SWIFT gateway), 10% Azure-hosted (SharePoint, some APIs).
- **Users:** 800 employees (60% remote), 120 contractors (all BYOD). Okta for SSO; Entra ID sync.
- **Devices:** 75% CrowdStrike-enrolled corporate laptops; 25% corporate unmanaged; 120 BYOD.
- **Team:** 3 security engineers, no network engineering team. No dedicated SD-WAN infrastructure.
- **Budget constraint:** Cannot replace core banking application or re-architect its auth model in
  the next 18 months.
- **Compliance:** PCI-DSS and SOX; the SWIFT gateway access must be auditable per-request.
- **Timeline:** Must show measurable ZT progress within 6 months; full migration in 24 months.

The security team is evaluating: Cloudflare Zero Trust (cloud edge) vs. Pomerium (reverse proxy
self-hosted) vs. headscale (network mesh) vs. no change (VPN improvement). A fourth option —
hybrid (Cloudflare for SaaS/web + headscale for infrastructure) — has also been raised.

## Do

1. [ ] Read `data/architecture-comparison.md` fully. For each pattern, note the column that most
   closely maps to Meridian's highest-priority use case (protecting the SWIFT gateway with
   per-request audit and device posture).

2. [ ] **Score each pattern against Meridian's constraints.** Build a scoring table in your ADR:
   one row per pattern, columns for: SaaS coverage, on-prem coverage, BYOD support, operational
   complexity, PCI/SOX audit capability, and time-to-first-value. Use a simple Low/Med/High
   scoring (with a one-line justification per cell — not just the score).

3. [ ] **Write the ADR.** Use the Michael Nygard ADR format:
   - **Status:** Proposed
   - **Context:** 2–3 sentences on what is driving the decision (the gap analysis finding, the
     constraints, the compliance requirements)
   - **Decision:** Which pattern (or hybrid) you recommend, and why
   - **Consequences:** Both positive and negative — including what you give up and what new risks
     the chosen pattern introduces. Do not skip the negatives.

4. [ ] **Specifically address the SWIFT gateway.** Whatever pattern you choose, write a paragraph
   describing exactly how SWIFT gateway access would work under it: what the user does, what checks
   are made, what the audit trail looks like, and what an attacker needs to compromise to gain
   unauthorized access (vs. the current model where Domain Admin + RDP = SWIFT access).

5. [ ] **Identify the first 90-day deliverable.** What is the single highest-value action
   Meridian's 3-engineer team can take in the first 90 days under your recommended pattern? It
   should be concrete (not "evaluate vendors"), completable with 3 engineers, and produce a
   measurable ZT improvement.

## Success criteria — you're done when

- [ ] The scoring table has all four patterns and all six columns with justified scores.
- [ ] The ADR has all three sections (Context / Decision / Consequences) with honest negatives.
- [ ] The SWIFT gateway paragraph is present and addresses authentication, posture, and audit.
- [ ] The 90-day deliverable is specific and completable.

## Deliverables

`architecture-adr.md` — the completed ADR, ready to present to the fictional Meridian CISO. This
is a portfolio artifact: it demonstrates you can evaluate competing architectures against real
organizational constraints and produce a justified, honest recommendation.

## Automate & own it

**Required.** Write a Python script (`score-architecture.py`) that reads a YAML file describing an
organization's constraints (e.g. `saas_percentage`, `has_network_team`, `byod_count`,
`compliance_requirements`) and produces a recommended pattern ranking with brief justifications.
Have a model draft it; **review the scoring logic** — does it correctly rank Cloudflare Zero Trust
lower when the organization cannot afford vendor dependency? Does it correctly promote the hybrid
option for large, mixed environments? Test it against two different fictional org profiles and
verify the output reflects sound architectural judgment, not just syntactic correctness.

## AI acceleration

Models are excellent at populating ADR templates and comparison tables from prose descriptions.
Use one to draft the scoring table from your notes on the Meridian constraints. Then **audit the
Consequences section** — ask it specifically: "What are the negative consequences of this
decision? What new risks does it introduce?" A model that only lists benefits is not being honest
with you. The ADR earns trust when the negatives are as specific as the positives.

## Connects forward

- Module 05 (SASE & Cloud-Delivered Zero Trust) implements the cloud-edge pattern in practice using
  Cloudflare Zero Trust — the pattern you may have recommended here. The lab is the hands-on proof
  of what the ADR described at the design level.

## Marketable proof

> "I can evaluate competing ZTNA architectures against real organizational constraints, score them
> against compliance and operational requirements, and produce an Architecture Decision Record that
> includes honest trade-offs — the deliverable a security architect produces before a ZT
> procurement decision."

## Stretch

- Find a real public ZT deployment case study (Google BeyondCorp, Cloudflare's own internal ZT
  migration at https://cloudflare.com/case-studies/, a government CISA pilot report) and add a
  "prior art" section to your ADR citing how a similar organization resolved this decision.
- Model the hybrid architecture (Cloudflare for web/SaaS + headscale for infrastructure access)
  as a separate ADR option with its own scoring row. Does it score better or worse than either
  single-vendor option on the Meridian constraints?
