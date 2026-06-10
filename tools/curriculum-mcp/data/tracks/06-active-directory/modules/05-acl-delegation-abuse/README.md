# Module 05 — ACL & Delegation Abuse

*Module concept · [Go to the hands-on lab →](lab.md)*


**Active Directory & Windows Security** — *the most dangerous attack paths in AD are not exploits — they are legitimate permissions given to the wrong principal.*

## Why this matters

ACL-based attack paths are the dominant finding in real-world red team engagements against mature AD environments — environments that have patched everything and think about Kerberos attacks. An organisation can have a strong password policy, LAPS deployed, Credential Guard on, and still be owned in two hops because a service account has `GenericWrite` on a high-privilege group. These misconfigurations are invisible in the standard "who's in Domain Admins" review and are only visible when you read the raw ACL entries on every object in the directory.

## Objective

Identify and exploit ACL misconfigurations (`GenericWrite`, `WriteDacl`, `WriteOwner`, `AllExtendedRights`) and delegation abuse (unconstrained and constrained delegation) in the Meridian domain, and trace the full privilege escalation path.

## The core idea

Every AD object — a user, group, computer, OU, or GPO — has a security descriptor with a DACL listing who can do what. Most access control discussion focuses on "who can log on to this server" or "who's in this group," but the DACL controls something more granular and more powerful: who can *modify* the object. The dangerous ACE types are not "Full Control" (which is obvious) but the targeted rights that allow specific operations: `GenericWrite` allows modifying most attributes; `WriteDacl` allows rewriting the object's entire permission set; `WriteOwner` allows taking ownership (which then lets you set any permissions); `AllExtendedRights` includes the right to read `ms-Mcs-AdmPwd` (LAPS password) or force password changes on users. A helpdesk account with `GenericWrite` on a security group can add any user to that group. A service account with `WriteDacl` on the Domain Admins group can grant itself membership at will.

**Delegation** in Active Directory is a separate but related attack surface. Unconstrained delegation means: any service running as this account will receive the TGT of any user who authenticates to it, stored in memory. If an attacker can authenticate any high-value account to a service running with unconstrained delegation — even by coercing the DC's machine account to authenticate (via printer spooler or petitpotam) — they receive that account's TGT and can impersonate it anywhere in the domain. Constrained delegation is safer — the service can only request tickets to specific target services — but it still allows impersonation of any user to those targets, which is dangerous if those targets are domain controllers.

Resource-Based Constrained Delegation (RBCD) is a newer mechanism that reverses where the delegation configuration lives: instead of the front-end service specifying what it can impersonate to, the back-end resource specifies which services can impersonate users to it. The attack consequence: if an attacker has `GenericWrite` on any computer object, they can set the `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute on that computer to allow an attacker-controlled account to impersonate any user to it — including local administrators — without being a Domain Admin.

The practical lesson is that BloodHound makes all of this tractable. The edges `GenericWrite`, `WriteDacl`, `WriteOwner`, `AllExtendedRights`, `AllowedToDelegate`, and `AllowedToAct` in the BloodHound graph represent exploitable relationships, and the graph's shortest-path queries find the multi-hop paths that are completely invisible in any tabular view. Every real AD assessment runs BloodHound; reading the graph is a core skill.

## Learn (~4 hrs)

**ACL abuse fundamentals**
- [ACL Abuse in Active Directory (The Hacker Recipes)](https://www.thehacker.recipes/ad/movement/dacl) — the most comprehensive practical reference for ACL abuse; covers GenericWrite, WriteDacl, WriteOwner, and AllExtendedRights with both PowerView and impacket equivalents.
- [T1222.001 — File and Directory Permissions Modification (MITRE ATT&CK)](https://attack.mitre.org/techniques/T1222/001/) and [T1484 — Domain Policy Modification (ATT&CK)](https://attack.mitre.org/techniques/T1484/) — the formal mapping for ACL modification techniques.

**Delegation attacks**
- [Unconstrained Delegation (adsecurity.org — Sean Metcalf)](https://adsecurity.org/?p=1667) — the original explanation of how unconstrained delegation works and how it is abused. Read the "TGT Harvesting" section carefully.
- [RBCD Attack (Elad Shamir, original research)](https://shenaniganslabs.io/2019/01/28/Wagging-the-Dog.html) — the paper that introduced RBCD abuse. Long but essential for understanding how GenericWrite on a computer object leads to full impersonation.

**BloodHound edge types**
- [BloodHound CE — Edge type documentation (GitHub)](https://github.com/SpecterOps/BloodHound/tree/main/docs) — the canonical definition of each edge type (GenericWrite, WriteDacl, AllowedToDelegate, AllowedToAct). Read the description and exploit path for each.

## Key concepts
- `GenericWrite` on a group = can add any member; on a user = can set attributes like `msDS-KeyCredentialLink` (shadow credentials).
- `WriteDacl` = can rewrite the object's ACL, granting yourself any right.
- `WriteOwner` = can take ownership, then write the DACL.
- `AllExtendedRights` on a user = can force password change; on a computer = can read LAPS password.
- Unconstrained delegation: any authenticating user's TGT is stored in service account's memory.
- Constrained delegation: service can impersonate any user to specific targets only.
- RBCD: back-end resource controls who can impersonate to it; GenericWrite on a computer enables the attack.
- BloodHound paths that include ACL edges are the primary finding in mature AD environments.

## AI acceleration

ACL abuse paths in BloodHound can be complex to narrate for a client report. Paste the graph path (nodes and edges) into a model and ask it to write a plain-English attack narrative: "Starting from [account], an attacker can..." The model is good at this — but verify each step by checking that the exploited edge is correctly documented in the BloodHound edge type docs before you put the narrative in a report.
