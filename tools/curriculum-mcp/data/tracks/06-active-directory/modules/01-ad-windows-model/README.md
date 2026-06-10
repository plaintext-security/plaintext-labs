# Module 01 — AD & Windows Security Model

*Module concept · [Go to the hands-on lab →](lab.md)*


**Active Directory & Windows Security** — *before you can attack or defend a domain, you need an accurate map of how Windows decides "yes" or "no."*

## Why this matters

Every Kerberos attack, every ACL abuse, every pass-the-hash scenario in this track exploits a seam in the Windows security model that looks like a feature until someone weaponises it. Attackers who understand the model find those seams; defenders who understand the model close them systematically instead of whack-a-mole. This module builds that shared map: the vocabulary and the mental model that every later lab assumes you have.

## Objective

Describe how Windows authenticates a user, how it decides what that user can access, and how Active Directory structures those decisions across an enterprise — without looking at notes.

## The core idea

Windows security is built on two separable concerns: **authentication** (proving who you are) and **authorization** (deciding what you're allowed to do). They interact through a single object — the **access token** — that Windows creates when you log in and attaches to every process you start. The token carries your SID (a unique identifier), the SIDs of your groups, and a set of privilege flags. When your process tries to open a file, pipe, registry key, or AD object, Windows compares the token against the object's **security descriptor** — a structured list of who can do what (the DACL) and who gets told when (the SACL). Every access decision in the OS reduces to this: does the token satisfy any `ALLOW` ACE in the descriptor, and does no `DENY` ACE come first?

Active Directory extends this model to the domain. Instead of a local SAM database, a Domain Controller holds a replicated LDAP directory of every user, computer, group, and service account. Authentication flows through **Kerberos** (default since Windows 2000) or NTLM (fallback). In Kerberos, the Key Distribution Centre on the DC issues tickets: a **Ticket Granting Ticket (TGT)** proves who you are to the KDC, and **service tickets (TGS)** prove it to individual services. The critical insight: tickets are cryptographic blobs encrypted with the *service's* key, not the user's. The service decrypts it, reads your SID and group SIDs from the embedded PAC, and makes an access decision — exactly like a local token, but assembled from the ticket rather than the SAM.

The organisational unit that makes this manageable at enterprise scale is the **domain**. A domain is a single replication boundary and trust boundary: all DCs share the same directory, and every object in the directory is identified by its distinguished name under the domain's DNS root. Domains can be grouped into **forests** (a forest is the outermost security boundary; a domain is a management boundary inside it). Trust relationships — transitive within a forest, explicitly configured between forests — let a user in one domain authenticate to resources in another. Every misconfigured trust is a lateral-movement opportunity.

Two structural ideas that trip people up in practice: **groups vs. group types**, and **GPOs**. Security groups accumulate SIDs into a token — being a member of `Domain Admins` is simply having the Domain Admins SID in your token, nothing magical about it. Distribution groups carry no SID and have no security meaning. **Group Policy Objects** are settings pushed to computers and users by the DC; they define password policy, audit policy, software restrictions, logon scripts, and hundreds of security controls. GPOs are the enforcement mechanism for most hardening controls — and the most common place defenders find gaps, because a GPO applied to the wrong scope or with the wrong precedence silently does nothing.

## Learn (~4 hrs)

**The Windows security model**
- [Windows Internals, Part 1 — Security chapter overview (Microsoft Docs)](https://learn.microsoft.com/en-us/sysinternals/resources/windows-internals) — the authoritative reference; read the "Security" chapter intro (Chapter 7 in the book). Understand access tokens, security descriptors, and ACL evaluation order.
- [Access Tokens — Microsoft Docs](https://learn.microsoft.com/en-us/windows/win32/secauthz/access-tokens) — short and precise; this is the mechanism that every lateral-movement technique eventually subverts.

**Kerberos in practice**
- [Kerberos Authentication Explained (Computerphile, ~8 min)](https://www.youtube.com/watch?v=5N242XcKAsM) — the clearest visual walkthrough of TGT/TGS flow. Watch before reading the MSFT spec.
- [How Kerberos Works in Windows Environments (Microsoft Docs)](https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-authentication-overview) — maps the generic Kerberos RFCs to actual DC roles and ticket fields. Focus on the PAC structure and ticket encryption.

**Active Directory structure**
- [Active Directory Domain Services Overview (Microsoft Docs)](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview) — domains, forests, OUs, trusts, sites. The foundation for understanding why things are laid out the way they are.
- [Understanding AD Trusts (Microsoft Docs)](https://learn.microsoft.com/en-us/azure/active-directory-domain-services/concepts-forest-trust) — the trust types and what they allow/deny. A forest trust is not the same as a domain trust and the difference matters for attacks.

**Group Policy**
- [Group Policy Overview (Microsoft Docs)](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-overview) — GPO processing order, WMI filters, and precedence. Pay attention to LSDOU (Local, Site, Domain, OU) — it governs which policy wins.

## Key concepts
- Access token = your identity credential at the kernel level; attached to every process you own.
- Security descriptor = the object's policy; DACL contains ACEs that allow/deny access.
- Kerberos TGT proves identity to the KDC; TGS (service ticket) proves identity to a specific service.
- PAC (Privilege Attribute Certificate) carries group SIDs inside the ticket — it's how authorization data travels.
- Domain = replication boundary + Kerberos realm; forest = security boundary.
- Transitive trusts inside a forest mean compromise anywhere can reach everywhere.
- GPO = the enforcement mechanism; LSDOU precedence governs which policy wins.
- NTLM is the fallback — no KDC needed, which is why it's still exploitable decades later.

## AI acceleration

Ask a model to walk you through what happens step-by-step when a domain user opens a file share: what tickets are requested, what fields are inspected, and what the file server actually checks. Then verify each claim against the Microsoft Docs links above. This is a great use of AI as a Socratic tutor — it explains at your pace — but the AD security model has enough subtle details (PAC validation, unconstrained delegation side effects) that you must cross-check against primary sources before you rely on the answer.
