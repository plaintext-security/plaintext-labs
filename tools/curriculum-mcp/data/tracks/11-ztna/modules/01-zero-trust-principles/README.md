# Module 01 — Zero Trust Principles

*Module concept · [Go to the hands-on lab →](lab.md)*


**Zero Trust Network Access** — *the perimeter didn't fail; it dissolved — and the model that replaced it starts by trusting nothing.*

## Why this matters

For most of network-security history, the working assumption was that everything inside the firewall
was relatively safe and everything outside was not. That model was workable when "inside" was a
data-centre you controlled and "outside" was the open internet. It stopped being workable the moment
applications moved to SaaS, infrastructure moved to cloud, and the workforce moved to home. Today
the average enterprise has no single perimeter worth defending — it has dozens of identity providers,
hundreds of SaaS apps, thousands of remote endpoints, and contractors who never touch the corporate
LAN. "Inside the network" no longer means anything coherent, and yet most access models still
behave as if it does. Zero Trust is the architectural response to that fact.

## Objective

Map Meridian Financial's current access patterns against the five pillars of the NIST SP 800-207
Zero Trust model, identify the gaps, and produce a written ZT gap analysis that a security architect
could use to prioritize a migration roadmap.

## The core idea

Zero Trust is not a product you buy, a firewall you configure, or a vendor checklist you pass. It is
a **posture change in who and what you extend implicit trust to by default** — and the answer under
ZT is: nobody, including your own employees on a machine you issued. That sounds paranoid until you
think about the incidents that define the last decade: adversaries living in flat networks for
months, lateral movement from a compromised contractor account, ransomware spreading across a VLAN
that had no reason to talk to anything else. In every one of those cases, the attacker was "inside"
— and the model extended them trust they never should have had.

The founding document is the 2014 Google BeyondCorp paper by Ward and Beyer. Google's insight was
deceptively simple: the VPN that puts you "on the network" is the wrong unit of access. The right
unit is **the individual request** — evaluated against the identity making it, the device it came
from, the sensitivity of the resource, and the context at that moment (time, location, anomaly
signals). Grant the minimum necessary for that request. Re-evaluate on the next one. This is what
Google called BeyondCorp and what NIST formalized in SP 800-207 as Zero Trust Architecture. It is
the same principle you already apply to database access in a well-run shop — least privilege, no
standing permissions — lifted to the network layer and applied universally.

NIST SP 800-207 organizes ZT around five pillars: **identity, device, network, application/workload,
and data**. In practice, identity and device are where most organizations start, because they are
also where most attackers start. Credential phishing is the leading initial access vector; once an
attacker has valid credentials, a flat network and an implicit-trust model mean they can reach almost
anything. A mature ZT identity pillar means every access request carries a verifiable identity claim
(a short-lived JWT, a FIDO2 assertion, an mTLS certificate), and the access decision is made at the
resource — not at the network perimeter. A mature device pillar means the device's posture (patch
level, EDR enrollment, disk encryption status) is checked at the time of the request and factored
into the decision, not assumed from the fact that it's on a "corporate" subnet.

There is a critical gotcha that trips up most first-pass ZT programs: **identity alone is not
enough**. A stolen credential on a trusted device is a serious incident; the same credential on an
unmanaged, compromised device is catastrophic — and a pure identity-only model can't tell the
difference. This is why the CISA Zero Trust Maturity Model (2023) distinguishes three maturity
levels — Traditional, Advanced, and Optimal — specifically for the device pillar. Moving from
Traditional to Advanced means binding the access decision to *both* identity and a device posture
signal. Most enterprises operating today are somewhere between Traditional and Advanced on device
trust, even when they think they've "done Zero Trust" because they have an SSO provider.

The second gotcha is **scope creep in the wrong direction**: Zero Trust is not a mandate to inspect
every packet or encrypt every internal connection. The goal is not maximum friction — it is
**minimizing blast radius**. Every access decision narrows what an attacker can do with a
compromised account or endpoint. Start with your highest-value applications and your broadest access
grants (administrative access, standing RDP sessions, shared service accounts) — those are the
places where a flat-trust model causes the most damage when it fails.

## Learn (~3 hrs)

**Foundations (~1.5 hrs)**
- [BeyondCorp: A New Approach to Enterprise Security (Ward & Beyer, 2014)](https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/) — the founding paper; 10 pages. Read it first. Everything in the ZT space is downstream of this work, and the practitioner vocabulary comes from here.
- [NIST SP 800-207: Zero Trust Architecture (2020)](https://csrc.nist.gov/pubs/sp/800/207/final) — the authoritative U.S. government specification. Read sections 1–3 (the abstract model and tenets) and section 7 (deployment scenarios). The rest is reference.

**Policy and maturity models (~1 hr)**
- [CISA Zero Trust Maturity Model v2.0 (2023)](https://www.cisa.gov/sites/default/files/2023-04/zero_trust_maturity_model_v2_508.pdf) — CISA's five-pillar maturity model. Read the executive summary and the maturity table for each pillar. This is the framework practitioners use to benchmark where an org actually stands.

**Mental model video (~30 min)**

## Key concepts

- Zero Trust is an access philosophy, not a product: trust nothing implicitly, verify every request, grant least privilege
- The perimeter model failed because the perimeter dissolved (remote work, SaaS, cloud, contractors)
- Five NIST 800-207 pillars: identity, device, network, application/workload, data
- BeyondCorp's unit of access: the individual request, not the network session
- CISA's three maturity levels: Traditional → Advanced → Optimal, per pillar
- Identity alone is insufficient — device posture must be bound to the access decision
- Goal is blast-radius minimization, not maximum friction

## AI acceleration

Describe Meridian's access patterns to a model and ask it to draft the gap analysis structure
against each NIST pillar. It will produce a reasonable skeleton quickly. **Your job** is to pressure-
test every finding against the actual BeyondCorp and NIST language — models occasionally conflate ZT
marketing language with the spec. Verify each gap claim is traceable to a specific NIST tenet or
CISA maturity level before committing the deliverable.
