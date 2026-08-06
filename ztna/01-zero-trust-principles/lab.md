# Lab 01 — Zero Trust Gap Analysis: from a flat-perimeter breach to a roadmap

> **Hands-on lab.** Environment: `plaintext-labs/ztna/01-zero-trust-principles`.
> Objective: **derive the ZT tenets from a real breach and map a firm to the five NIST pillars.**
> Target: **~60–90 min** for the analysis, one finish line. This is a **document-analysis lab — no
> containers.**

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The breach has TWO load-bearing failures**, not one. | "No MFA" is the open door; the **flat interior** is what made it fatal. |
| 2 | **Unit of access = the request, not the session.** | A VPN sells the whole interior for one login; ZT re-checks every request. |
| 3 | **Verify explicitly = identity AND device.** | Identity-only can't tell a stolen credential on a managed box from one on a compromised box. |
| 4 | **Assume breach → minimize blast radius.** | Least privilege + segmentation, so one foothold ≠ the whole network. |
| 5 | **Five NIST 800-207 pillars:** identity · device · network · app/workload · data. | Every gap you write must tie to one pillar + a tenet or CISA level. |
| 6 | **CISA maturity: Traditional → Advanced → Optimal.** | "Traditional" is where Colonial (and most firms) sit — name the level, don't just say "bad." |

*(If you can explain all six cold at the end — especially #1 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [reveal section](README.md#the-reveal-inside-trusted-is-the-bug) and the
> [five-pillars map](README.md#the-five-pillars-youll-map-against).

---

## Warm-up — answer before you read the firm's file (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. If the Colonial attacker had **your** firm's VPN credential, name the **two** things that would have
   to be true for one login to become the whole network. (Hint: one is about the door, one is about the
   room behind it.)
2. "We enforce MFA on the VPN." Which **pillar** does that improve, and which **three pillars** does it
   leave completely untouched?

---

## Setup

The scenario and seed data live in the companion `plaintext-labs` repo. **No containers** — `make demo`
just prints your brief.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/01-zero-trust-principles
make demo
```

> **▸ On track if:** `make demo` prints the *"Lab 01 — Zero Trust Gap Analysis"* banner, the **five
> NIST pillars**, and a spoiler-tagged list of expected gap categories. The one seed file you reason
> *about* is **`data/corp-access-map.md`** — the fictional firm you're assessing.

> **Authorization note.** This is a paper exercise over a *fictional* firm and *public* breach
> reporting. You are not attacking any system. (Later modules in this track stand up real services you
> *do* attack — there the rule binds: only test systems you own or have explicit written permission to
> test.)

---

## Build it — read a little, do a little

### Step 1 — Autopsy the real breach first (the source of the whole rubric)

**Concept (30 sec):** Flight-card #1. Colonial is *entry → foothold → spread*, and the third step is
the one write-ups miss. Reconstruct the chain in your own words and pin **one** tenet to each step.

**Do it:** from the [module's Colonial section](README.md#the-case-colonial-pipeline-april-2021) and
the two primary sources it links (Blount's Senate testimony; CISA/FBI **AA21-131A**), write the
three-step chain. For each step name the single ZT tenet that would have broken it.

> **▸ On track if:** your step-1 tenet is *verify explicitly* (no MFA), and your step-3 tenet is
> *assume breach / minimize blast radius* (flat interior) — **not** another "MFA" restatement. If both
> your failures are about the login, re-read flight-card #1.

### Step 2 — Predict, then read the firm's access map

**Concept (30 sec):** Flight-card #2. "Implicit trust by location" is the smell — every place the firm
grants reach because you're *on the network* is a per-request decision that isn't happening.

**Do it:** before opening the file, write one sentence — *"If the Colonial attacker had our credential,
how far would they get here?"* Then read **`data/corp-access-map.md`** and mark every place trust is
granted **by location** (e.g. "once on VPN, can reach any server" = a network-pillar gap at
*Traditional*). Note whether your prediction was too optimistic.

> **▸ On track if:** you've flagged at least the split-tunnel VPN onto a flat internal network, MFA
> only at the VPN edge, unmanaged contractor devices, and shared Domain-Admin service accounts — each
> tagged with the pillar it belongs to.

### Step 3 — Map the firm to the five pillars (your turn — this is the objective)

**Concept (30 sec):** Flight-card #5 + #6. Each pillar gets a current-state paragraph tied to a
specific **NIST 800-207 tenet** *or* **CISA maturity level** — the tie is what makes it an assessment,
not an opinion.

**Do it:** for identity · device · network · application/workload · data, write a one-paragraph
assessment and name the tenet/level. *Example:* "Identity — **Traditional**: MFA at the VPN edge, not
the app layer. NIST 800-207 Tenet 2 requires per-session identity, continuously authenticated — not
just at login."

> **▸ On track if:** all five pillars have a paragraph, and each cites a specific tenet **or** a named
> CISA level — no pillar is left as a bare adjective ("weak"). Cross-check against the `make demo`
> spoiler list *after* you've written yours.

### Step 4 — Top three gaps + a first-90-days roadmap

**Do it (assemble it — you have the pillars now):** pick the **three** gaps where one compromised
account/device does the most damage; justify each with a realistic, **Colonial-shaped** attack path
(reused password → no MFA → VPN → flat network → shared Domain-Admin SA → everything). Then write a
priority-ordered roadmap of 3–5 initiatives: each names the pillar, the target maturity change
(Traditional → Advanced), and the concrete tool/control. Tie at least one initiative straight to the
Colonial failure (kill legacy/standing accounts; enforce MFA + device posture at the *resource*).

> **▸ On track if:** each of your top-three gaps reads as an attack *path*, not a statement — a reader
> can trace credential → resource — and every roadmap item has a pillar + a maturity target + a named tool.

---

## Prove the control (your finish line)

Assemble `gap-analysis.md` with these sections, then run the one check that proves the rubric is sound:

> *Executive Summary · Colonial Autopsy (the lesson) · Pillar-by-Pillar Assessment · Top Risks ·
> 90-Day Roadmap.*

**The proof:** encode the **Colonial** posture into your own rubric (`mfa_at_resource: false`,
`legacy_accounts_present: true`, `micro_segmentation: false`) and confirm it scores **Traditional**
across identity, device, and network. *If your rubric disagrees with the breach, one of them is wrong —
fix it.* That agreement is what makes the analysis credible.

---

## Recall check — close the doc, answer from memory (3 min)

1. The two load-bearing failures in Colonial — which is the door, which is the room, and which tenet kills each?
2. What does "verify explicitly" add beyond "require a password," and why isn't identity alone enough?
3. Name the five pillars and the three CISA maturity levels without looking.

Missed one? Re-run the step that built it, or pull the [module reveal](README.md#the-reveal-inside-trusted-is-the-bug) — then re-answer.

---

## Deliverables

- **`gap-analysis.md`** — the completed pillar gap-analysis + roadmap. A portfolio artifact: it shows
  you can take a *real* breach apart, derive the principles it violated, read an enterprise access
  architecture, map it to a standards framework, and produce a risk-prioritized roadmap.

*Do not commit any credential or network detail beyond the fictional scenario.*

## Automate & own it

**Required.** Write a short Python or Bash script (`score-zt.py` / `score-zt.sh`) that reads a YAML
description of access controls (e.g. `{ mfa_at_perimeter_only: true, mfa_at_resource: false,
legacy_accounts_present: true, edr_coverage: 0.75, micro_segmentation: false }`) and prints a maturity
score (Traditional / Advanced / Optimal) per NIST pillar from your rubric. Run it against the firm —
then, as the sanity check from the finish line, encode the **Colonial** posture and confirm it scores
*Traditional* across identity, device, and network.

Have a model draft it from your rubric — then **read every line** and verify the scoring matches your
hand-written assessment before committing. A script that scores the firm (or Colonial) differently from
your written analysis is broken, no matter how clean the syntax. Commit both `gap-analysis.md` and
`score-zt.py`.

## Definition of done (`zt-principles` ✅)

- [ ] The Colonial chain is reconstructed in three steps, each mapped to a tenet, with the
  **flat-interior / blast-radius** failure named explicitly (not just "no MFA").
- [ ] All five NIST pillars have an assessment tied to a specific tenet or CISA maturity level.
- [ ] The top three gaps each read as a realistic, Colonial-shaped attack *path*.
- [ ] The roadmap has ≥3 priority-ordered initiatives with named tooling and a maturity-level target.
- [ ] `score-zt.py` scores the Colonial posture *Traditional* across identity/device/network — agreeing with your prose.
- [ ] `gap-analysis.md` + `score-zt.py` are committed; you can explain all six flight-card facts cold.

## Connects forward

- **Module 02 — Identity as the Control Plane** closes the identity gap: a real access broker
  (Keycloak/OIDC) with per-application auth, not a single VPN MFA checkpoint.
- **Module 03 — Device Trust & Posture** closes the device gap Colonial's legacy account had no concept of.
- **Module 10 — VPN → ZTNA Migration** is the direct sequel: it migrates the exact legacy-VPN-on-a-flat-network setup you just indicted — without an outage.

## Marketable proof

> "I can take a real lateral-movement breach apart, derive the Zero Trust tenets it violated, map an
> enterprise access architecture to NIST 800-207 and the CISA maturity model, identify the
> highest-risk gaps with realistic attack paths, and produce a prioritized migration roadmap."

## Stretch

- Add a second org profile (a 50-person all-SaaS startup) and run your scoring script against it. Does
  the same first-90-days advice apply? Where does it diverge, and why?
- Map your top three gaps to ATT&CK techniques (**T1078** Valid Accounts, **T1133** External Remote
  Services, **T1021** Lateral Movement) and tie each to the matching step in the Colonial chain or the
  CISA/FBI DarkSide advisory (AA21-131A).
