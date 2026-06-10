# Lab 11 — Defending Identity: Tiered Admin Model

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a design and analysis lab — no containers required.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/11-defending-identity
make demo   # print the defense control matrix
```

The `data/` directory contains:
- `defense-controls.md` — a matrix mapping each attack technique to the controls that prevent/detect it.
- The lab exercise: design a tiered admin model for Meridian and document it.

> Design work. No live attack targets involved.

## Scenario

Following the attack path demonstration (modules 02-08) and the hardening sprint (module 10), the Meridian CISO wants an architectural answer: not "patch this misconfiguration" but "redesign the administrative model so that compromising a Finance workstation cannot, even in principle, lead to domain admin." Your job: design and document the tiered admin model for Meridian, map every attack technique to the control that breaks it, and produce a GPO restriction specification that can be handed to the AD team for implementation.

## Do

1. [ ] **Study the defense control matrix.** Run `make demo` and read `data/defense-controls.md`. For each attack technique (Kerberoast, AS-REP roast, PTH, ACL abuse, golden ticket), there is a prevention control and a detection control. Understand the difference: prevention stops the technique; detection observes it. Which techniques have reliable prevention controls? Which rely primarily on detection?

2. [ ] **Design the Meridian tier structure.** Based on `data/meridian-domain.md`, assign every account, system, and service to a tier:
   - **Tier 0:** DCs, AD itself, PKI (if any). Accounts: who must be here? (`tallen`? `Administrator`?)
   - **Tier 1:** Servers (fs01, backup01, appserver01). Accounts: IT-Admins? svc-* accounts?
   - **Tier 2:** Workstations (WS-FIN-01 through WS-HR-05). Accounts: Finance-Users, HR-Users.

   Write the tier assignments in a table. The key question: which accounts are in the wrong tier today?

3. [ ] **Define the GPO restrictions.** For each tier boundary, specify the GPO settings that enforce it:
   - What is the "Deny log on locally" setting for Tier 0 accounts on Tier 2 systems?
   - What is the "Deny log on through Remote Desktop Services" setting?
   - Which accounts should be in Protected Users, and why?
   - Where should Authentication Policy Silos be applied?

4. [ ] **Map tiering to the PATH-001 attack path.** Go through each hop of PATH-001 (module 08) and decide, for each: does the tiered admin model stop this hop, and why or why not? Be precise about *what* tiering does and does not address — at least one hop is a pure credential attack, one is an ACL fix that tiering only contains, and one is broken outright by Tier 0 logon restrictions. For each hop record which it is and the residual control needed (e.g. gMSA, ACE removal).

5. [ ] **Design the JIT workflow.** Describe (in 3-5 paragraphs) how a Just-In-Time access workflow would work for Meridian: when `sgarcia` (an IT admin) needs to perform a task on the DC, what is the process? How long does the access last? What approvals are required? What happens at expiry?

6. [ ] **Write the Protected Users policy.** List every account that should be added to Protected Users in the Meridian domain, with a one-line justification for each. Be specific about the caveats: what breaks when you add an account (e.g., NTLM-dependent applications stop working for that account)?

## Success criteria — you're done when

- [ ] You have a complete tier assignment table for all Meridian accounts and systems.
- [ ] You have specified the GPO settings for each tier boundary (exact policy path and value).
- [ ] You have traced PATH-001 through the tiered model and identified at which hop the attack is stopped.
- [ ] You have a Protected Users candidate list with justifications.
- [ ] You have a JIT workflow description.

## Deliverables

`tiered-admin-design.md` — the complete architectural design: tier assignments, GPO specifications, the PATH-001 analysis, the JIT workflow, and the Protected Users policy. This is the capstone architectural deliverable for Track 06. Commit it.

## Automate & own it

**Required.** Write `tier-compliance-check.py` — a Python script (using ldap3) that queries the Meridian DC and checks:
1. Are any Tier 0 accounts (from a hardcoded list: `tallen`, `Administrator`) members of Protected Users?
2. Are any service accounts members of Domain Admins (immediate risk)?
3. Are any service accounts in Backup Operators (immediate risk)?

Output a pass/fail for each check. Have a model draft the LDAP group membership queries; you verify the filter logic. This is the continuous compliance check that should run nightly. Commit it.

## AI acceleration

Ask a model to compare the Microsoft "Enterprise Access Model" to the older "ESAE Tier Model" — what changed, what stayed the same, and what the practical differences are for a small-to-medium enterprise like Meridian Financial. The model's comparison is useful as a starting framework — but verify the current guidance by reading the Microsoft Docs links in the Learn section, since this area of security architecture has evolved significantly since 2020.

## Connects forward

This module is the architectural capstone for Track 06. The tiered model, the detection rules (module 09), and the hardening checklist (module 10) together form the "close the paths" deliverable that completes the track's attack-then-defend arc. The JIT workflow design connects directly to Track 11 — ZTNA (Zero Trust Network Architecture), where least-privilege access and time-bounded permissions are the foundation.

## Marketable proof

> "I design tiered Active Directory administrative models — tier assignments, GPO logon restrictions, Protected Users policy, and JIT access workflows — that structurally prevent credential theft attack paths, and I can map every control to the specific attack technique it eliminates."

## Stretch

- Research **Microsoft Entra Privileged Identity Management (PIM)** as a cloud-native JIT implementation. How does it complement an on-premises tiered model for a hybrid environment? What is the trust boundary between on-premises AD and Entra ID in a hybrid deployment?
- Design a **PAW specification** for Meridian: what hardware controls, what software restrictions, what network controls, and what GPO settings does a Tier 0 PAW need to be resistant to a Tier 2 compromise? (Hint: no internet, no email, no standard user applications, separate network VLAN, AppLocker whitelist.)
