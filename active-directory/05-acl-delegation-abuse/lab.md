# Lab 05 — ACL & Delegation Abuse

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/05-acl-delegation-abuse
make up      # start Samba4 DC + attacker container
make demo    # identify ACL misconfigs and demonstrate exploitation
make shell   # interactive shell
make down
```

The environment includes a Samba4 DC with the Meridian misconfigurations pre-seeded:
- `svc-deploy` has `GenericWrite` on `IT-Admins` group.
- `Finance-Managers` has `GenericWrite` on `Finance-Users` group.
- `svc-backup` has unconstrained delegation.
- `data/acl-findings.json` — a BloodHound-shaped JSON showing the ACL abuse paths.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Scenario

You've obtained credentials for `jsmith` and identified via BloodHound that `svc-deploy` has `GenericWrite` on `IT-Admins`, and that `IT-Admins` members have local admin rights on the DC. If you can compromise `svc-deploy`, you can add `jsmith` to `IT-Admins` and move to domain admin. Your goal: identify the misconfigurations via LDAP, verify them, and demonstrate the exploitation chain.

## Do

1. [ ] **Query ACLs via ldapsearch.** As `jsmith`, read the `nTSecurityDescriptor` on the `IT-Admins` group and work out who holds `GenericWrite` or `WriteDacl`. The raw SDDL is hard to read by eye — `data/acl-findings.json` has the interpreted version to check against.

2. [ ] **Read the BloodHound ACL findings.** From `data/acl-findings.json`, answer: which principal has `GenericWrite` on `IT-Admins`, what does that right let you do to the group, and what is the next hop once `jsmith` is a member?

3. [ ] **Simulate the GenericWrite exploit.** Using the `svc-deploy` credential you cracked in module 03, exercise the `GenericWrite` to add `jsmith` to `IT-Admins` (Impacket's group/ACL tooling, or `samba-tool` from inside the DC container for the lab demo). Verify the new membership via LDAP.

4. [ ] **Identify unconstrained delegation.** Query for accounts with the unconstrained-delegation `userAccountControl` bit set. Which account appears besides the DCs, and why does `svc-backup` holding unconstrained delegation create a TGT-theft risk?

5. [ ] **Map the full escalation path.** From `data/acl-findings.json`, trace `jsmith` → `Domain Admins` through the ACL edges (write it as `jsmith -[MemberOf]-> Finance-Users -[…]-> Domain Admins`). How many ACL hops?

6. [ ] **Identify the defensive fix.** For each misconfiguration you found, note the remediation: which ACE should be removed, on which object, by whom?

## Success criteria — you're done when

- [ ] You have queried the ACL on IT-Admins and identified the `GenericWrite` holder.
- [ ] You have demonstrated (or traced in the JSON) the group membership modification exploit.
- [ ] You have identified the unconstrained delegation account via LDAP.
- [ ] You have written the full escalation chain from jsmith to Domain Admins with ATT&CK technique IDs.
- [ ] You have written the remediation for each misconfiguration.

## Deliverables

`acl-abuse-report.md` — the misconfigurations found (with the LDAP evidence), the exploitation chain, ATT&CK mappings (T1484.001 for group modification, T1134.001 for token impersonation via delegation), and remediations. Commit it alongside `acl-findings.json` (the pre-generated data is fine to commit — it's seed data, not a live secret).

## Automate & own it

**Required.** Write `acl-audit.py` — a Python script using `ldap3` or `impacket`'s LDAP classes that connects to the DC and dumps all ACEs on the 10 highest-risk groups (Domain Admins, IT-Admins, etc.) and flags any non-default principals with write rights. Have a model draft the ACL parsing logic; you verify the ACE type parsing against Microsoft's security descriptor documentation. This is the automated ACL audit you'd run on every engagement. Commit it.

## AI acceleration

Paste the raw ACL JSON from step 1's ldapsearch (the `nTSecurityDescriptor` attribute) into a model and ask it to identify every ACE that grants write-class rights to a non-default principal. The model is good at parsing SDDL format but will sometimes misidentify built-in SIDs — cross-check against Microsoft's well-known SID reference.

## Connects forward

The ACL misconfigurations identified here feed directly into the BloodHound path analysis in module 08 and the hardening checklist in module 10. The audit script you write here becomes the basis for the continuous ACL monitoring setup in module 11.

## Marketable proof

> "I identify and exploit ACL misconfigurations in Active Directory — GenericWrite, WriteDacl, unconstrained delegation — and produce a prioritised remediation report with the full attack chain and ATT&CK mapping."

## Stretch

- Research **shadow credentials** (T1556.007): if you have `GenericWrite` on a user, you can set `msDS-KeyCredentialLink` to add a certificate credential you control, then authenticate as that user via PKINIT. Trace how this works and why it bypasses password-based detection.
- Write a BloodHound Cypher query that finds all paths where a non-admin user has `WriteDacl` on any group that has `AdminTo` rights on a computer.
