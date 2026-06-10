# Lab 01 — Zero Trust Gap Analysis: Meridian Financial

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **document analysis lab** — no containers needed. The scenario and seed data live in the
companion [`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/01-zero-trust-principles
make demo      # prints the scenario summary and expected gap categories
```

The lab ships one seed file: `data/meridian-access-map.md` — a structured description of Meridian's
current access patterns, network layout, and identity posture. Read it before starting.

> Everything in this lab is fictional. No real systems are accessed.

## Scenario

Meridian Financial is a mid-size financial services firm — 800 employees, three offices, ~60%
remote. Their current access model:

- **Remote access:** Cisco AnyConnect VPN, split-tunnel, terminates on a flat /20 internal network.
  Once on VPN, employees can reach any server in the data-centre segment.
- **Identity:** Active Directory on-premises, synced to Azure Entra ID (Okta in pilot for ~200
  users). No MFA enforced for internal applications — only the VPN login itself requires MFA.
- **Applications:** Core banking on-prem, CRM and HR in SaaS (Salesforce, Workday), SharePoint on
  Azure. No consistent access broker — some apps authenticate via AD Kerberos, some via SAML, some
  via static credentials embedded in service accounts.
- **Devices:** Domain-joined Windows laptops issued by IT, plus ~120 contractor laptops that are
  personal (BYOD) and unmanaged. CrowdStrike Falcon deployed to ~75% of corporate devices;
  contractors have no EDR coverage.
- **Lateral movement controls:** No micro-segmentation inside the data-centre. Server-to-server
  traffic is not monitored. Three service accounts have Domain Admin privileges and are shared
  across multiple application teams.
- **Logging:** Windows Event Log forwarding to a Splunk instance. VPN logs ingested. No device
  health signals correlated with access decisions.

Your job: map this against the five NIST SP 800-207 pillars, apply the CISA maturity levels, and
produce a prioritized gap analysis with a recommended first-90-days roadmap.

## Do

1. [ ] Read `data/meridian-access-map.md` fully. Note every place where the description implies
   implicit trust is granted (e.g. "once on VPN, can reach any server" is a network pillar gap at
   Traditional maturity — there is no per-request access decision).

2. [ ] For each of the five NIST pillars (identity, device, network, application/workload, data),
   write a one-paragraph assessment of Meridian's current state. Reference the specific NIST
   800-207 tenet or CISA maturity level your assessment maps to. Example: "Identity — Traditional:
   MFA is enforced at the network perimeter (VPN) but not at the application layer. NIST 800-207
   Tenet 2 requires that access to enterprise resources be granted on a per-session basis with the
   identity continuously authenticated, not just at VPN login."

3. [ ] Identify the **top three gaps by risk**: the three gaps where a single compromised account
   or device would cause the most damage under the current model. Justify each in one paragraph
   with a realistic attack path (credential phishing → VPN MFA prompt fatigue → flat network
   lateral movement, for example).

4. [ ] Draft a **first-90-days roadmap** — three to five initiatives, in priority order. For each:
   the initiative, which pillar it addresses, the target maturity level change (Traditional →
   Advanced), and what tool or control closes the gap. Keep it realistic for a 800-person firm
   without a large security engineering team.

5. [ ] Format the deliverable as `gap-analysis.md` using the structure: Executive Summary,
   Pillar-by-Pillar Assessment, Top Risks, Roadmap.

## Success criteria — you're done when

- [ ] All five NIST pillars have a written assessment tied to a specific tenet or CISA maturity level.
- [ ] The top three gaps each have a realistic attack path, not a generic statement.
- [ ] The roadmap has ≥3 initiatives in priority order with tooling named.
- [ ] `gap-analysis.md` is written and ready to commit.

## Deliverables

`gap-analysis.md` — the completed ZT gap analysis. This is a portfolio artifact: it demonstrates
you can read an access architecture, map it to a standards framework, and produce a risk-prioritized
recommendation — the core skill of a security architect or ZT program lead.

Do not commit any credential or network detail that goes beyond the fictional scenario.

## Automate & own it

**Required.** Write a short Python or Bash script (`score-zt.py` or `score-zt.sh`) that reads a
YAML description of access controls (e.g. `input: { mfa_at_perimeter_only: true, edr_coverage: 0.75,
micro_segmentation: false, ... }`) and prints a maturity score (Traditional / Advanced / Optimal)
for each NIST pillar, based on your assessment rubric.

Have a model draft the script from your rubric — then **read every line** and verify the scoring
logic matches your hand-written assessment on the Meridian case before committing. A script that
scores Meridian incorrectly relative to your written analysis is broken, regardless of how
syntactically clean it is.

Commit both `gap-analysis.md` and `score-zt.py` to your portfolio repo.

## AI acceleration

A model can turn "Meridian has AnyConnect VPN with split tunnel and no MFA on internal apps" into a
reasonably structured gap analysis. Use it to bootstrap the pillar-by-pillar section. Then **verify
every claim against the NIST 800-207 tenet table and the CISA maturity levels** — models frequently
conflate marketing ZT language ("micro-segmentation is Zero Trust") with the standards-based framing.
The gap analysis earns credibility when every finding is traceable to a specific source.

## Connects forward

- Module 02 addresses the identity pillar gap directly: deploy Keycloak as a proper access broker
  with per-application OIDC flows, not a single VPN MFA checkpoint.
- Module 03 addresses the device pillar gap: headscale/Tailscale + device posture enforcement as
  an alternative to the flat-network AnyConnect model.
- Module 05 closes the application/workload pillar gap with Cloudflare Zero Trust application access.

## Marketable proof

> "I can read an enterprise access architecture, map it to NIST 800-207 and the CISA maturity
> model, identify the highest-risk gaps with realistic attack paths, and produce a prioritized
> migration roadmap — the deliverable a ZT program starts with."

## Stretch

- Add a second organization profile (e.g. a 50-person startup with everything in SaaS and no
  on-prem) and run your scoring script against it. Does the same first-90-days advice apply? Where
  does it diverge, and why?
- Map the top three gaps to specific ATT&CK techniques (e.g. T1078 Valid Accounts, T1021.001 RDP).
  Does the attack path you wrote reference a real adversary campaign? Link to a real threat report.
