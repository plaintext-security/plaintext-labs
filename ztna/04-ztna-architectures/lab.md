# Lab 04 — ZTNA Architecture Decision: score four patterns, defend one as an ADR

> **Hands-on lab.** Environment: `plaintext-labs/ztna/04-ztna-architectures`.
> Objective: **score four ZTNA patterns against a real bank's constraints and defend one pick as an
> Architecture Decision Record.** Target: **~90–120 min**, one finish line. This is a **design /
> document exercise — no containers.**

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The principle is fixed; the *delivery* is the decision.** | You're choosing a pattern for *this* org — not memorizing which product "is" Zero Trust. |
| 2 | **Three axes:** self-hosted vs cloud-delivered · OSS/self-run vs managed · threat model & blast radius. | Score ops burden against the **actual 3-engineer team**, not an idealized one. |
| 3 | **Blast radius = where the policy engine sits + what popping it buys.** | VPN concentrator = the whole flat interior (and it's a pre-auth internet box: Pulse/Ivanti CVEs). |
| 4 | **Four patterns:** VPN (perimeter) · reverse proxy (per request, HTTP/S only) · mesh (per connection, any protocol) · cloud edge (per session, continuous). | +hybrid. Each moves the decision — and the internet-facing surface — somewhere different. |
| 5 | **Consequences is the deliverable's proof.** | Upsides-only = a junior tell, or an unreviewed AI draft. Name the **upstream-bypass** path. |
| 6 | **The payments/SWIFT gateway is the filter.** | PCI/SOX demand per-request audit + posture — that constraint eliminates patterns that can't do it. |

*(If you can explain all six cold at the end — especially why #3 is a topology problem, not a patching one — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [four-pattern section](README.md#the-four-patterns) and the
> [case study on the VPN appliance](README.md#the-case-the-appliance-everyone-was-still-trusting).

---

## Warm-up — answer before you open the seed file (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. A regional bank keeps its VPN concentrator fully patched. Give the **one-sentence reason** that still
   doesn't make the VPN-appliance pattern safe. (Hint: think about *shape*, not the patch level.)
2. The bank must give a per-request **audit trail** for access to its payments/SWIFT gateway (PCI/SOX).
   Which **two** of the four patterns give you that natively, and which **two** don't?

---

## Setup

The scenario and seed data live in the companion `plaintext-labs` repo. **No containers** — `make demo`
just prints the constraint brief and points at the comparison file.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/04-ztna-architectures
make demo
```

> **▸ On track if:** `make demo` prints the *"Lab 04 — ZTNA Architecture Decision: Corp"* banner, the
> **Corp constraints summary** (60% SaaS / 30% on-prem / 10% Azure; 800 employees + 120 BYOD; 3 security
> engineers, no network team; Okta + CrowdStrike; PCI-DSS + SOX with a per-request-audited SWIFT gateway),
> and the five **patterns to evaluate**. The one seed file you reason *about* is
> **`data/architecture-comparison.md`** — traffic-flow, trust-model, and blast-radius notes for all four
> patterns. `make reset` is a no-op here (no containers).

> **Authorization note.** This is a paper exercise over a *fictional* bank ("Corp") and *public*
> vulnerability reporting. You are not attacking any system. (Later modules in this track stand up real
> services you *do* attack — there the rule binds: only test systems you own or have explicit written
> permission to test.)

---

## Build it — read a little, decide a little

### Step 1 — Anchor on the case, then read the four patterns

**Concept (30 sec):** Flight-card #3. Before you compare patterns, internalize *why the baseline is the
one to beat*: the VPN concentrator is a single internet-facing, pre-auth-reachable box in front of a flat
interior — the exact shape the Pulse (**CVE-2019-11510**) and Ivanti (**CVE-2023-46805 + CVE-2024-21887**)
mass-exploitations keep popping. That is a topology problem, not a patching one.

**Do it:** read **`data/architecture-comparison.md`** fully. For each of the four patterns, write one line:
*where does the access decision get made, and what is exposed to the internet pre-auth?* Mark the column
that best serves the highest-priority use case — the payments/SWIFT gateway needing per-request audit **and**
device posture.

> **▸ On track if:** your per-pattern line names the policy-engine location (perimeter / app layer / ACL /
> vendor edge) **and** the internet-facing surface — and you've flagged that the VPN and the raw mesh don't
> give you per-request audit on the gateway out of the box.

### Step 2 — Score all four patterns against Corp's constraints

**Concept (30 sec):** Flight-card #2. A score without a justification is an opinion. Score operational
complexity against the *real* team — 3 security engineers, no network function — not a hypothetical one.

**Do it:** build a scoring table in your ADR — one row per pattern (VPN, reverse proxy/Pomerium,
mesh/headscale, cloud edge/Cloudflare), columns for: **SaaS coverage · on-prem coverage · BYOD support ·
operational complexity (vs the 3-engineer team) · PCI/SOX per-request audit · time-to-first-value.** Use
Low/Med/High **with a one-line justification per cell — not just the letter.**

> **▸ On track if:** every cell has a reason, not just a grade; the ops-complexity column visibly reflects
> "no network team" (self-hosted mesh/proxy pay a toll there); and the audit column separates the patterns
> that log per request from the ones that don't.

### Step 3 — Write the ADR (Nygard: Context / Decision / Consequences)

**Concept (30 sec):** Flight-card #5. The Consequences section is the whole point of the format — it's where
you write down what you give up and what new risk you take on. Skip it and you have a sales slide.

**Do it:** write the ADR:
- **Status:** Proposed.
- **Context:** 2–3 sentences on what drives the decision (the gap-analysis finding, the constraints, PCI/SOX).
- **Decision:** which pattern (or hybrid) you recommend, stated as a clear position on the
  **self-hosted-vs-cloud-delivered** axis.
- **Consequences:** positive *and* negative — vendor dependency, ops burden, protocol scope, and the
  **upstream-bypass** path you must close. Do not skip the negatives.

> **▸ On track if:** the Decision takes an explicit stance on self-hosted-vs-cloud-delivered (not "it
> depends"), and the Consequences name at least one concrete downside *and* the bypass path for your pick.
> If Consequences reads like marketing, you're not done.

### Step 4 — The payments/SWIFT gateway attack-path paragraph

**Concept (30 sec):** Flight-card #6. This is the blast-radius defence of your decision, made concrete on the
one resource that matters most under PCI/SOX.

**Do it:** for your chosen pattern, write one paragraph on how gateway access works: what the user does, what
checks are made (identity, posture), what the audit trail looks like, and **what an attacker must compromise
to reach it** — contrasted with the current model where *Domain Admin + RDP = gateway*.

> **▸ On track if:** the paragraph ends on the attacker's required compromise (a specific token/device/posture
> combination), and it is visibly *harder* than "one credential" — that delta is your decision's value.

### Step 5 — The first 90-day deliverable

**Do it (assemble it — you have the pick now):** name the single highest-value action the 3-engineer team can
ship in 90 days under your recommended pattern. It must be concrete (not "evaluate vendors"), completable by
three people, and produce a *measurable* ZT improvement (e.g. "the SWIFT gateway is now behind per-request
auth with an audit log; direct RDP to it is firewalled off").

> **▸ On track if:** the 90-day item is a shippable outcome with a before/after you could measure — not a
> planning activity.

---

## Prove the control (your finish line)

Assemble `architecture-adr.md` with these sections, then run the one check that proves your judgment is sound:

> *Status · Context · Options + Scoring Table · Decision (on the self-hosted-vs-cloud axis) · Consequences
> (with the bypass path) · Payments-Gateway Attack Path · First 90 Days.*

**The proof:** run your `score-architecture.py` (below) against **Corp's** constraints and confirm its
top-ranked pattern **matches your ADR Decision**. Then run it against a *second, deliberately different*
profile (e.g. a 20-person all-SaaS startup with no on-prem and no compliance load) and confirm the ranking
*changes* in a way you can defend. *If the script's ranking disagrees with your written Decision, one of them
is wrong — fix it.* That agreement is what makes the recommendation credible rather than a preference.

---

## Recall check — close the doc, answer from memory (3 min)

1. Name the three trade-off axes, and why "self-hosted vs cloud-delivered" is not the same axis as "OSS/self-run vs managed."
2. For the same stolen credential, rank the four patterns by blast radius, largest to smallest.
3. Why is the VPN concentrator a *topology* problem an architect can't patch away — and which patterns change the shape?

Missed one? Re-run the step that built it, or pull the [four-pattern section](README.md#the-four-patterns) — then re-answer.

---

## Deliverables

- **`architecture-adr.md`** — the completed ADR, ready to present to the fictional CISO. A portfolio
  artifact: it shows you can evaluate competing architectures against real organizational constraints, score
  them against compliance and ops requirements, and produce a justified, *honest* recommendation. **This ADR
  is the template the rest of the track copies whenever a decision has to be defended** — keep it sharp.

*Do not commit any credential or network detail beyond the fictional scenario.*

## Automate & own it

**Required.** Write a Python script (`score-architecture.py`) that reads a YAML file describing an org's
constraints (e.g. `saas_percentage`, `on_prem_percentage`, `has_network_team`, `byod_count`,
`self_host_capacity`, `compliance_requires_per_request_audit`) and outputs a **ranked pattern
recommendation** with a brief justification per pattern. Have a model draft it — then **review the scoring
logic**: does it rank cloud-delivered lower when the org can't accept vendor dependency, rank self-hosted
lower when there's no team to run it, and promote the **hybrid** option for large, mixed estates?

Test it against **two** profiles — Corp, and the second one from the finish line — and verify the output
reflects sound architectural judgment, not just syntax. A script whose top pick disagrees with your written
ADR is broken, however clean the code. Commit both `architecture-adr.md` and `score-architecture.py`.
**AI drafts → you review every line → you own the ranking it produces.**

## Definition of done (`ztna-architectures` ✅)

- [ ] The scoring table has all four patterns and all six columns, every cell **justified** (not a bare grade).
- [ ] The ADR has all three Nygard sections; Consequences carries real negatives **and** names the upstream-bypass path.
- [ ] The Decision takes and defends an explicit position on **self-hosted vs cloud-delivered**.
- [ ] The payments/SWIFT-gateway paragraph covers authentication, posture, audit, and the attacker's required compromise.
- [ ] The 90-day deliverable is concrete, completable by 3 engineers, and measurable.
- [ ] `score-architecture.py`'s top pick for Corp **agrees** with your ADR Decision, and the ranking shifts sensibly on the second profile.
- [ ] Both files committed; you can explain all six flight-card facts cold.

## Connects forward

- **Module 05 — SASE & Cloud-Delivered Zero Trust** implements the cloud-edge pattern for real with
  Cloudflare Tunnel + Access — the hands-on proof of what this ADR described at the design level.
- **Module 06 — Identity-Aware Access** implements the self-hosted reverse-proxy pattern (Pomerium) — the
  other end of the axis you decided here.
- **Module 10 — VPN → ZTNA Migration** executes the strangler-fig cutover *away* from the exact
  internet-facing concentrator this module indicted — without an outage.

## Marketable proof

> "I can evaluate competing ZTNA architectures against real organizational constraints, score them against
> compliance and operational requirements, and produce an Architecture Decision Record with honest
> trade-offs — the deliverable a security architect produces before a ZT procurement decision."

## Stretch

- Add the **hybrid** (cloud edge for web/SaaS + headscale for infrastructure) as its own scoring row and ADR
  option. Does it beat either single-vendor pick on Corp's constraints — and what new failure mode does
  running *two* control planes introduce?
- Add a "prior art" section citing a real public ZT deployment (Google BeyondCorp; Cloudflare's own internal
  migration; a CISA pilot report) and how a similar org resolved the self-hosted-vs-cloud-delivered call.
- Map the current-model attack path you contrasted in Step 4 to ATT&CK: **T1133** External Remote Services,
  **T1078** Valid Accounts, **T1021** Remote Services — and tie the External-Remote-Services technique to the
  Pulse/Ivanti appliance CVEs from the case study.
