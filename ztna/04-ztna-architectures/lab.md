# Lab 04 — ZTNA Architecture Decision (ADR)

*Type 11 · Decision / ADR. [← Back to the module concept](README.md)*

**Type 11 · Decision / ADR.** You are handed a real constraint set and four competing ZTNA
architectures, and you must *choose one and defend it* — score the options, pick, and write the honest
consequences in an Architecture Decision Record. The deliverable is the ADR itself: the central call is
**self-hosted vs. cloud-delivered**, and the grade is the defence, not the pick. No grader; you verify
your own work against the observable success criteria below.

## Setup

This is a **design exercise** — no containers needed. The scenario materials live in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/04-ztna-architectures
make demo      # prints the constraint set and the scenario brief
```

The lab ships one seed file: `data/architecture-comparison.md` — a structured comparison of the
four ZTNA patterns with traffic-flow diagrams, trust-model descriptions, and blast-radius analysis.
Read it before starting the ADR exercise.

> This is a document and design exercise. No real systems are accessed.

## Scenario

A regional bank's security team has completed the ZT gap analysis (Lab 01) and must now recommend a
delivery architecture to the CISO. The constraints are real:

- **Applications:** 60% SaaS (CRM, HR, chat), 30% on-premises (core banking, legacy reporting, a
  payments/SWIFT gateway), 10% public-cloud-hosted (document store, some APIs).
- **Users:** 800 employees (60% remote), 120 contractors (all BYOD). Okta for SSO; Entra ID sync.
- **Devices:** 75% EDR-enrolled corporate laptops; 25% corporate unmanaged; 120 BYOD.
- **Team:** 3 security engineers, no network engineering team. No dedicated SD-WAN infrastructure.
- **Budget / scope constraint:** Cannot replace the core banking application or re-architect its auth
  model in the next 18 months.
- **Compliance:** PCI-DSS and SOX; the payments gateway access must be auditable per-request.
- **Timeline:** Must show measurable ZT progress within 6 months; full migration in 24 months.

The team is evaluating: Cloudflare Zero Trust (cloud edge) vs. Pomerium (reverse proxy, self-hosted)
vs. headscale (network mesh, self-hosted) vs. no change (VPN improvement). A fifth option — a hybrid
(cloud edge for SaaS/web + headscale for infrastructure) — has also been raised. The defining axis
across these is **self-hosted vs. cloud-delivered**: defend where you land on it.

## Do

1. [ ] Read `data/architecture-comparison.md` fully. For each pattern, note the column that most
   closely maps to the highest-priority use case (protecting the payments gateway with per-request
   audit and device posture).

2. [ ] **Score each pattern against the constraints.** Build a scoring table in your ADR: one row per
   pattern, columns for: SaaS coverage, on-prem coverage, BYOD support, operational complexity (scored
   against the *actual* 3-engineer team), PCI/SOX audit capability, and time-to-first-value. Use a
   simple Low/Med/High scoring **with a one-line justification per cell — not just the score.**

3. [ ] **Write the ADR** in Michael Nygard format:
   - **Status:** Proposed
   - **Context:** 2–3 sentences on what is driving the decision (the gap-analysis finding, the
     constraints, the compliance requirements).
   - **Decision:** Which pattern (or hybrid) you recommend, and why — stated as a clear position on the
     self-hosted-vs-cloud-delivered axis.
   - **Consequences:** Both positive and negative — including what you give up and what new risks the
     chosen pattern introduces (vendor dependency, ops burden, protocol scope, bypass paths). **Do not
     skip the negatives** — this section is the point of the format.

4. [ ] **Specifically address the payments gateway (the attack-path paragraph).** Whatever pattern you
   choose, write a paragraph describing exactly how payments-gateway access works under it: what the
   user does, what checks are made, what the audit trail looks like, and **what an attacker must
   compromise to gain unauthorized access** — contrasted with the current model where Domain Admin +
   RDP = gateway access. This is the blast-radius defence of your decision.

5. [ ] **Identify the first 90-day deliverable.** What is the single highest-value action the
   3-engineer team can take in the first 90 days under your recommended pattern? It must be concrete
   (not "evaluate vendors"), completable with 3 engineers, and produce a measurable ZT improvement.

## Success criteria — you're done when

- [ ] The scoring table has all four patterns and all six columns with **justified** scores.
- [ ] The ADR has all three sections (Context / Decision / Consequences) with honest negatives.
- [ ] The Decision explicitly takes and defends a position on **self-hosted vs. cloud-delivered**.
- [ ] The payments-gateway paragraph is present and addresses authentication, posture, audit, and the
  attacker's required compromise.
- [ ] The 90-day deliverable is specific and completable by the 3-engineer team.

*(Honor system — no grader. Check your own ADR against the list above; the test is whether a CISO
could be talked out of it. If the Consequences read like marketing, you're not done.)*

## Deliverables

`architecture-adr.md` — the completed ADR, ready to present to the fictional CISO. This is a portfolio
artifact: it demonstrates you can evaluate competing architectures against real organizational
constraints and produce a justified, honest recommendation. **This ADR is the template the rest of the
track copies whenever a decision has to be defended** — keep it sharp.

## Automate & own it

**Required.** Write a Python script (`score-architecture.py`) that reads a YAML file describing an
organization's constraints (e.g. `saas_percentage`, `has_network_team`, `byod_count`,
`self_host_capacity`, `compliance_requirements`) and produces a recommended pattern ranking with brief
justifications. Have a model draft it; **review the scoring logic** — does it correctly rank
cloud-delivered options lower when the organization cannot accept vendor dependency, and rank
self-hosted options lower when there is no team to run them? Does it correctly promote the hybrid option
for large, mixed environments? Test it against two different fictional org profiles and verify the
output reflects sound architectural judgment, not just syntactic correctness. **AI drafts → you review
every line → you own the ranking it produces.**

## AI acceleration

Models are excellent at populating ADR templates and comparison tables from prose descriptions. Use one
to draft the scoring table from your notes on the constraints. Then **audit the Consequences section** —
ask it specifically: "What are the negative consequences of this decision? What new risks does it
introduce?" A model that only lists benefits is not being honest with you. The ADR earns trust when the
negatives are as specific as the positives.

## Connects forward

- Module 05 (SASE & Cloud-Delivered Zero Trust) implements the cloud-edge pattern in practice using
  Cloudflare Tunnel + Access — the pattern you may have recommended here. The lab is the hands-on proof
  of what this ADR described at the design level.
- Module 06 (Identity-Aware Access) implements the self-hosted reverse-proxy pattern (Pomerium) — the
  other side of the self-hosted-vs-cloud-delivered axis you decided here.

## Marketable proof

> "I can evaluate competing ZTNA architectures against real organizational constraints, score them
> against compliance and operational requirements, and produce an Architecture Decision Record that
> includes honest trade-offs — the deliverable a security architect produces before a ZT procurement
> decision."

## Stretch

- Find a real public ZT deployment case study (Google BeyondCorp, Cloudflare's own internal ZT
  migration, a government CISA pilot report) and add a "prior art" section to your ADR citing how a
  similar organization resolved the self-hosted-vs-cloud-delivered decision.
- Model the hybrid architecture (cloud edge for web/SaaS + headscale for infrastructure access) as a
  separate ADR option with its own scoring row. Does it score better or worse than either single-vendor
  option on these constraints?
