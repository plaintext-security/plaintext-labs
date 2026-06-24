# Lab 12 — Tiering a Brownfield Domain

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/12-brownfield-tiering
make up           # start the Samba DC + the tiering tools container
make corroborate  # verify the flat baseline fixture against the LIVE DC (ldap3): rosters + SPN surface
make before       # re-walk PATH-001 on the flat domain — prove it reaches Domain Admin (t=0)
make demo         # full story: PATH-001 open on the flat domain, then dead after tiering in waves
make shell        # interactive shell in the tools container
make down
```

How this lab is honest about what is and isn't live: the **directory facts** the model rests on —
who is in Domain Admins / Backup Operators, which accounts carry an SPN — are read **live off the DC**
by `make corroborate` (`corroborate-live.py`, ldap3). What stays *modelled* is GPO Deny-logon
**enforcement**: Samba does not enforce client-side `SeDenyInteractiveLogonRight` (that lives in the
Windows LSA on a domain-joined client these labs don't ship), so the wave gate evaluates the
logon-rights graph for reachability. The judgement it encodes — a *failed* attack scores PASS, a
*still-working* one scores FAIL — is identical to the real-DC case. See `VALIDATION.md`.

The lab provides:
- A Samba4 DC (the same image built in Module 02) reachable at `dc01.corp.local` / `10.10.0.10`, carrying the real accounts/groups/SPNs PATH-001 depends on.
- A tools container with `samba-tool`, `ldapsearch`, and `ldap3`.
- `corroborate-live.py` — reads the live privileged-group rosters and SPN surface off the DC and checks them against `data/baseline.json`.
- `data/baseline.json` — the **flat brownfield state** graph: `tallen` (Domain Admin) logs on everywhere including Finance workstations; `svc-backup` logs on interactively; nothing is tiered.
- `data/waves.json` — the staged migration (pilot OU → Protected Users → widen), each wave with its no-lockout assertions and the PATH-001 hop it must close.
- `data/path-001.json` — the primary attack path from Module 08, hop by hop, so you know which hop each wave must close.

> **Authorization.** Everything here runs against your own lab domain only. Never apply these GPO/logon
> changes to a domain you do not own or have explicit written permission to modify — a mis-scoped
> Deny-logon GPO locks real administrators out of production.

## Scenario

You are the AD security lead for the `corp.local` domain. Module 11 produced the tiered-admin **design** on paper. Module 08 produced **PATH-001** — the low-priv-to-Domain-Admin path that works *because* `tallen` (a DA) logs into Finance workstations, so a compromised workstation yields a DA credential. The CISO has signed off on the design. Now you must **deploy it on the live domain without an outage**: no admin gets locked out, and at each step you prove the relevant hop of PATH-001 is now dead. The whole company logs into this domain every morning. A big-bang GPO link at the root is off the table — it would deny logons company-wide the instant it replicates and you would be debugging a lockout live.

## Do

1. [ ] **Corroborate the baseline against the live DC, then capture the flat "before."** First run `make corroborate` — it reads the real Domain Admins / Backup Operators rosters and the SPN surface off `dc01.corp.local` via ldap3 and confirms `data/baseline.json` describes the domain that's actually running (if it doesn't, the rest of the lab is reasoning about a fiction). Then run `make before` / `make demo`: record the brownfield reality you're migrating from — which privileged accounts (`tallen`, `sgarcia`, `svc-backup`) can log on where today — and *prove the attack works now* by re-walking the PATH-001 hop that depends on a DA credential being harvestable from a Finance workstation. This is your t=0 proof that the path is open. Save it as `proof/before.md`.

2. [ ] **Predict the big-bang failure, then write the staged plan.** *Before* touching anything: in one paragraph, state what breaks if you link `Deny log on through Remote Desktop Services` + `Deny log on locally` for Tier 0 accounts at the **domain root** right now (which legitimate logons die, why you can't tell intended-deny from lockout, why there's no incremental rollback). Then write `migration-runbook.md` — the wave plan: order the waves by blast radius (lowest-risk pilot first), name every account each wave touches, and define the per-wave proof and rollback.

3. [ ] **Build the tier scaffold beside the flat domain.** Create the Tier 0 / Tier 1 / Tier 2 OUs and the tiering security groups with `samba-tool ou create` / `samba-tool group add`. Do **not** move production accounts yet and do **not** link any restriction GPO. Goal: the new structure stands *beside* the running flat domain, changing nothing for anyone.

4. [ ] **Wave 1 — pilot the Deny-logon restriction to ONE OU.** Author the Tier 0 Deny-logon restriction (the `SeDenyRemoteInteractiveLogonRight` / `SeDenyInteractiveLogonRight` user-rights settings for the Tier 0 accounts), and apply it **scoped to a single pilot OU** (the Finance pilot workstations) only — via GPO link + security-group filter, not at the root. *Goal:* `tallen` can no longer log on to the pilot Finance host, but is untouched everywhere else.

5. [ ] **Prove Wave 1 — both assertions.** Run the two-part proof and record it in `proof/wave-1.md`:
   - **(a) No admin locked out:** every admin still does their job via the *correct* tiered path — `tallen` can still administer from the Tier 0 jump host; non-Tier-0 admins on the pilot OU are unaffected. Test the legitimate logon paths and show they succeed.
   - **(b) Attack path dead:** re-walk the PATH-001 hop from step 1 against the pilot host — dumping it must now yield **no DA credential**. Show the `secretsdump.py` output that previously gave `tallen`'s material now gives nothing.

   If (a) fails, **roll back wave 1** (unlink the GPO from the pilot OU), confirm the admin can log on again, debug the scope, and re-run. Do not proceed until both assertions hold.

6. [ ] **Wave 2 — Protected Users for the Tier 0 accounts.** Add the Tier 0 accounts to **Protected Users** (`samba-tool group addmembers "Protected Users" tallen ...`). *Goal:* close the Kerberos surface for those accounts. Then prove Wave 2 in `proof/wave-2.md`: **(a)** the account still authenticates for its legitimate Kerberos logons (watch the caveat — any NTLM/RC4-dependent path for that account now breaks; confirm none of its real tasks rely on one); **(b)** the attack is dead — the AS-REP roast / Kerberoast against that account (the relevant PATH-001 hop) now **fails**. Roll back (remove from Protected Users) if (a) regresses.

7. [ ] **Widen the scope wave by wave; prove each.** Extend the Deny-logon GPO link from the pilot OU to the remaining Tier 2 OUs (Finance → HR → IT workstations), one wave at a time, repeating the step-5 two-part proof for each and keeping the per-wave rollback ready. Record each in `proof/wave-N.md`.

8. [ ] **Close it out (the irreversible step, taken last).** Only once the last wave is proven across, widen the restriction to the whole Tier 2 scope and **retire the flat behavior**: confirm no Tier 0 account retains interactive/RDP logon on any Tier 2 host. Re-walk **all of PATH-001 end to end** and show it dies. Write `proof/after.md`: the full attack path now fails, and a no-lockout summary across every wave.

## Success criteria — you're done when

- [ ] You captured a `proof/before.md` showing PATH-001's DA-credential hop **working** on the flat domain.
- [ ] `migration-runbook.md` orders the waves by blast radius, names every account per wave, and defines the per-wave proof + rollback.
- [ ] The Deny-logon restriction was rolled out **scoped per OU/wave**, never linked big-bang at the root.
- [ ] Every wave has a `proof/wave-N.md` asserting **both** *no admin locked out* **and** *attack-path-dead*.
- [ ] You exercised at least one **rollback** (or documented the tested rollback step and that no wave required it).
- [ ] `proof/after.md` shows PATH-001 dies end-to-end with no admin locked out across any wave.

## Deliverables

`migration-runbook.md` (the staged wave plan, blast-radius ordering, per-wave proof + rollback) + the `proof/` directory (`before.md`, `wave-1.md` … `wave-N.md`, `after.md` — the measured no-lockout-AND-attack-dead evidence per wave). Commit these. Lab artifacts (dumps, tickets, hashes) stay out of commits.

## Automate & own it

**Required.** Write `wave-check.py` — a Python script (ldap3 + a thin wrapper over the attack re-walk) that, given a wave's spec, runs the **two-part proof automatically**: it (1) checks the legitimate-logon paths for every account in the wave (the "no lockout" half — e.g. confirms the account still resolves and is not denied on its intended host), and (2) re-runs the wave's targeted PATH-001 hop and asserts it now **fails** (the "attack dead" half), emitting a clean pass/fail JSON per assertion. Have a model draft the LDAP queries and the subprocess wiring; **you** verify the filter strings, the `userAccountControl`/Protected-Users membership checks, and — critically — that a *failed* attack is scored as pass and a *still-working* attack is scored as fail (the model will routinely invert this). This is the per-wave gate the runbook calls. Commit it.

## AI acceleration

Ask a model to draft `migration-runbook.md` and the `samba-tool` / GPO commands for each wave. It will reliably hand you a **big-bang** plan — link the Deny-logon GPO at the domain root, add every account to Protected Users at once — because that is the simplest thing to express and it carries none of the operational fear of locking out the admin team. Reject that: you own the wave ordering (blast-radius first), the pilot-OU scoping, and the coordination list. The judgment the model cannot do is spotting the service account that *silently logs on interactively* and will break, and verifying **both** proof assertions — asked to "confirm the migration worked," a model checks the admin can log on from the jump host and calls it done, missing both the lockout it caused elsewhere and the flat path it left open. Make it draft; you confirm no-lockout AND attack-dead, per wave.

## Connects forward

The staged-rollout discipline (pilot → wave → prove → widen, with per-step rollback) is the same strangler-fig pattern Track 11 (ZTNA) applies to VPN→ZTNA migration — same shape, different control plane. The `wave-check.py` two-part gate becomes the seed for Module 13's drift detector: once the tiered state is deployed, the question shifts from "did we get here without breaking it" to "does it *stay* here" — Module 13 re-runs the same kind of check on a schedule and alerts when the tiering you just rolled out decays.

## Marketable proof

> "I migrate live Active Directory domains from a flat admin model to a tiered one without an outage — staging Deny-logon GPOs to a pilot OU, moving privileged accounts into Protected Users in waves, and proving at each step that no administrator is locked out *and* that the targeted credential-theft attack path is now dead, with a tested per-wave rollback."

## Stretch

- Add a **coexistence dashboard**: a small script that reports, at any moment during the migration, what percentage of Tier 0 accounts are still flat (retain Tier 2 logon rights) vs. migrated — the shrinking "un-tiered surface" curve that proves strangler-fig progress to a CISO.
- Research **Authentication Policy Silos** as the wave *after* Protected Users: design (don't necessarily deploy on Samba4) how you would stage a silo that restricts Tier 0 accounts to obtaining TGTs only from approved Tier 0 hosts, and what the per-wave lockout risk and proof would be.
