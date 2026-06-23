# Lab 01 — Zero Trust Gap Analysis: from a flat-perimeter breach to a roadmap

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

This is a **document-analysis lab** — no containers needed. The scenario and seed data live in the
companion [`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/01-zero-trust-principles
make demo      # prints the scenario summary and the seven NIST 800-207 tenets to map against
```

The lab ships two seed files:
- `data/access-map.md` — a structured description of a fictional firm's current access patterns,
  network layout, and identity posture (the org to assess). Read it before starting.
- `data/colonial-timeline.md` — a sourced, public timeline of the Colonial Pipeline 2021 breach
  (legacy VPN, no MFA, leaked password, flat interior), with citations to Blount's Senate testimony
  and the CISA/FBI DarkSide advisory. This is the real anchor you reason *from*.

> The firm in `access-map.md` is fictional. The Colonial Pipeline material is real and cited — treat
> it as your evidence file, not as illustration.

## Scenario

You're the first security architect at a mid-size financial services firm — ~800 employees, three
offices, ~60% remote. Leadership read about Colonial Pipeline and asked the obvious question: *"could
that happen to us?"* Your job is to answer it honestly. The firm's current access model
(full detail in `data/access-map.md`):

- **Remote access:** a split-tunnel VPN that terminates on a flat internal network. Once on VPN,
  employees can reach any server in the data-centre segment.
- **Identity:** on-prem Active Directory synced to a cloud IdP. MFA is enforced **only** on the VPN
  login itself — not on internal applications. Several legacy/service accounts exist with weak or
  unrotated passwords.
- **Applications:** core banking on-prem; CRM and HR in SaaS; no consistent access broker — some apps
  use Kerberos, some SAML, some static credentials in service accounts.
- **Devices:** domain-joined corporate laptops, plus ~120 *unmanaged* contractor (BYOD) laptops. EDR
  covers ~75% of corporate devices; contractors have none.
- **Lateral-movement controls:** no micro-segmentation inside the data-centre; server-to-server
  traffic is unmonitored; a few service accounts hold Domain Admin and are shared across teams.
- **Logging:** Windows Event Log + VPN logs forwarded to a SIEM. No device-health signal is
  correlated with access decisions.

> **Authorization note.** This is a paper exercise over a fictional firm and *public* breach
> reporting. You are not attacking any system. (Later modules in this track stand up real services
> you *do* attack — and there the rule binds: only test systems you own or have explicit written
> permission to test.)

## Do

1. [ ] **Autopsy the real breach first.** Read `data/colonial-timeline.md`. In your own words, write
   the three-step chain (entry → foothold → spread) and, for each step, name the **one** Zero Trust
   tenet that would have broken it. Hint: step 1 is *verify explicitly*; the step that turns one
   foothold into the whole network is *assume breach / minimize blast radius* — most write-ups miss
   this one and blame only the missing MFA.

2. [ ] **Predict, then check.** Before reading the firm's access map, write one sentence: *"If the
   Colonial attacker had our credentials, how far would they get?"* Then read `data/access-map.md`
   and mark every place the description grants **implicit trust by location** (e.g. "once on VPN, can
   reach any server" is a network-pillar gap at *Traditional* maturity — there is no per-request
   decision). Note whether your prediction was too optimistic.

3. [ ] **Map the firm to the five NIST pillars.** For each pillar (identity, device, network,
   application/workload, data), write a one-paragraph assessment of current state and tie it to a
   specific **NIST 800-207 tenet** or **CISA maturity level**. Example: "Identity — Traditional: MFA
   is enforced at the network edge (VPN) but not at the application layer. NIST 800-207 Tenet 2
   requires access granted per-session with identity continuously authenticated, not just at login."

4. [ ] **Top three gaps by risk** — the three where a single compromised account or device causes the
   most damage. Justify each in one paragraph with a realistic attack path that *mirrors Colonial*
   (e.g. reused password on a legacy account → no MFA → VPN session → flat network → Domain Admin
   service account → everything). Reference the matching pillar and tenet.

5. [ ] **First-90-days roadmap** — three to five initiatives, in priority order. For each: the
   initiative, the pillar it addresses, the target maturity-level change (Traditional → Advanced),
   and the specific tool/control that closes the gap. Keep it realistic for an 800-person firm
   without a large security-engineering team. (Tie at least one initiative directly to the Colonial
   failure: kill standing/legacy accounts and enforce MFA + device posture at the *resource*.)

6. [ ] **Format the deliverable** as `gap-analysis.md`: *Executive Summary · Colonial Autopsy
   (the lesson) · Pillar-by-Pillar Assessment · Top Risks · 90-Day Roadmap.*

## Success criteria — you're done when

- [ ] The Colonial chain is reconstructed in three steps, each mapped to a specific ZT tenet, with
  the flat-interior / blast-radius failure named explicitly (not just "no MFA").
- [ ] All five NIST pillars have a written assessment tied to a specific tenet or CISA maturity level.
- [ ] The top three gaps each have a realistic, Colonial-shaped attack path — not a generic statement.
- [ ] The roadmap has ≥3 initiatives in priority order with named tooling and a maturity-level target.
- [ ] `gap-analysis.md` is written and ready to commit.

## Deliverables

`gap-analysis.md` — the completed Zero-Trust pillar gap-analysis + roadmap. This is a portfolio
artifact: it demonstrates you can take a *real* breach apart, derive the principles it violated, read
an enterprise access architecture, map it to a standards framework, and produce a risk-prioritized
migration roadmap — the deliverable a Zero Trust program starts with.

Do not commit any credential or network detail beyond the fictional scenario.

## Automate & own it

**Required.** Write a short Python or Bash script (`score-zt.py` or `score-zt.sh`) that reads a YAML
description of access controls (e.g. `input: { mfa_at_perimeter_only: true, mfa_at_resource: false,
legacy_accounts_present: true, edr_coverage: 0.75, micro_segmentation: false, ... }`) and prints a
maturity score (Traditional / Advanced / Optimal) for each NIST pillar, based on your assessment
rubric. Run it against the firm — and as a sanity check, encode the **Colonial** posture
(`mfa_at_resource: false`, `legacy_accounts_present: true`, `micro_segmentation: false`) and confirm
your rubric scores it *Traditional* across identity, device, and network. If it doesn't, your rubric
disagrees with the breach — fix one of them.

Have a model draft the script from your rubric — then **read every line** and verify the scoring
logic matches your hand-written assessment before committing. A script that scores the firm (or
Colonial) incorrectly relative to your written analysis is broken, no matter how clean the syntax.

Commit both `gap-analysis.md` and `score-zt.py` to your portfolio repo.

## AI acceleration

A model can turn the access map into a reasonably structured gap analysis quickly — use it to
bootstrap the pillar-by-pillar section. Then **verify every claim against the NIST 800-207 tenet
table and the CISA maturity levels**: models frequently conflate marketing ZT language
("micro-segmentation *is* Zero Trust") with the standards-based framing, and they tend to retell
Colonial as "they forgot MFA" while missing the flat-interior failure that did the real damage. The
gap analysis earns credibility when every finding is traceable to a specific source.

## Connects forward

- **Module 02 — Identity as the Control Plane** addresses the identity gap directly: a proper access
  broker (Keycloak/OIDC) with per-application auth, not a single VPN MFA checkpoint.
- **Module 03 — Device Trust & Posture** addresses the device gap: device enrollment and posture
  bound to the access decision, the thing Colonial's legacy account had no concept of.
- **Module 05 — SASE & Cloud-Delivered ZT** closes the application/network gap with no-inbound-ports,
  identity-aware application access.
- **The VPN → ZTNA Migration module** is the direct sequel to this autopsy: it takes the exact
  legacy-VPN-on-a-flat-network setup you just indicted and migrates it to ZTNA *without an outage*.

## Marketable proof

> "I can take a real lateral-movement breach apart, derive the Zero Trust tenets it violated, map an
> enterprise access architecture to NIST 800-207 and the CISA maturity model, identify the
> highest-risk gaps with realistic attack paths, and produce a prioritized migration roadmap — the
> deliverable a ZT program starts with."

## Stretch

- Add a second org profile (a 50-person startup with everything in SaaS and no on-prem) and run your
  scoring script against it. Does the same first-90-days advice apply? Where does it diverge, and why?
- Map your top three gaps to specific ATT&CK techniques (e.g. **T1078** Valid Accounts, **T1133**
  External Remote Services, **T1021** Lateral Movement) and tie each to the matching step in the
  Colonial chain or the CISA/FBI DarkSide advisory (AA21-131A).
