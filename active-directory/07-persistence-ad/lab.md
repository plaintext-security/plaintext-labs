# Lab 07 — Persistence in Active Directory

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/07-persistence-ad
make up      # start Samba4 DC + attacker
make demo    # demonstrate golden ticket creation + DCSync persistence
make shell   # interactive shell
make down
```

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Scenario

You have achieved domain admin access on Meridian (modules 04-06). Before the blue team discovers the breach, you want to establish persistence mechanisms that survive password resets and account remediation. Your goal: forge a golden ticket, forge a silver ticket for the MSSQL service, demonstrate DCSync persistence rights, and document what incident response must do to genuinely remove each persistence method.

## Do

1. [ ] **Extract the krbtgt hash.** With your domain-admin credential, DCSync just the `krbtgt` account and record its NT hash. You also need the domain SID — find it in the dump output or via an RPC LSA query.

2. [ ] **Forge a golden ticket.** Forge a TGT for a Domain Admin that need not exist in the directory. (What does the golden ticket require beyond the krbtgt hash and domain SID? Which group RID grants Domain Admins?) Note the resulting ticket-cache artefact.

3. [ ] **Use the golden ticket.** Load the forged ticket into your credential cache and use it to perform a DA-only action against the DC. Does the domain need to be reachable for the ticket to be *issued*? Answer in your notes, and explain why.

4. [ ] **Forge a silver ticket.** Using the MSSQL service account's hash, forge a service ticket for the MSSQL SPN impersonating a privileged user. Why does this ticket generate no Event 4769 on the DC?

5. [ ] **Add DCSync rights.** As an attacker with DA, grant replication rights to a low-privilege account as a persistence mechanism, then verify that account can now DCSync. (Which ACE/extended right must you write on the domain object? Which Impacket tool edits a DACL?)

6. [ ] **Write the remediation checklist.** For each persistence method, write down: what specific action removes it, and what can the attacker still do before the remediation takes effect? (One of these methods survives a *single* krbtgt rotation — work out which, and why two rotations are required.)

## Success criteria — you're done when

- [ ] You have forged a golden ticket for a non-existent user and used it for DC access.
- [ ] You have forged a silver ticket for the MSSQL SPN without KDC contact.
- [ ] You have added (and verified) DCSync rights to a low-privilege account.
- [ ] You have written the specific remediation steps for each persistence method, including the "rotate krbtgt twice" requirement.

## Deliverables

`persistence-report.md` — the persistence methods demonstrated, the artefacts generated (ticket filenames, not the actual hashes), the ATT&CK technique IDs (T1558.001, T1558.002, T1003.006), and a remediation checklist for each. Commit it.

## Automate & own it

**Required.** Write `persistence-audit.py` — a script that queries the domain object's ACL (using `ldap3`) and reports any non-default principals with `DS-Replication-Get-Changes-All` rights, and queries AdminSDHolder's ACL for non-default ACEs. Have a model draft the ACL parsing; you verify the GUID for `DS-Replication-Get-Changes-All` (`1131f6ad-...`) against the Microsoft documentation. This is the automated persistence check that incident responders should run after every engagement. Commit it.

## AI acceleration

Ask a model to write a complete golden ticket attack narrative for a client report — one that explains to a non-technical executive why "we reset the attacker's password" is not sufficient remediation. The model's output will likely be good; your job is to verify the technical claims (double krbtgt rotation, AdminSDHolder propagation timer, outstanding ticket validity) against primary sources before putting it in a deliverable.

## Connects forward

The golden ticket detection (Event 4769 with anomalous PAC, Event 4768 anomalies) is the basis for Sigma rules in module 09. The DCSync rights audit script you write here is part of the hardening-as-code in module 10. The full remediation checklist is the foundation for the defender's response playbook in module 11.

## Marketable proof

> "I demonstrate and explain active directory persistence mechanisms — golden tickets, silver tickets, DCSync rights — including what incident response must do to genuinely remove each one, not just lock out the attacker's user account."

## Stretch

- Research **AdminSDHolder abuse**: an attacker with DA can add themselves to the AdminSDHolder object's ACL, which propagates to all protected groups every 60 minutes. How would you detect this? What does the ACL diff look like before and after?
- Look into **skeleton key** attacks: a persistence mechanism where a malware patches LSASS on the DC so any account accepts a specific "master" password. Why does this not survive a DC reboot?
