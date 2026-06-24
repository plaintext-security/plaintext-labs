# Corp — AD Hardening Checklist (CIS-Aligned)

> Annotate each item with: **Compliant** / **Non-compliant** / **N/A** and your evidence.

---

## 1. Account & Credential Hygiene

| # | Control | CIS Ref | Corp Status | Evidence |
|---|---------|---------|-----------------|---------|
| 1.1 | Kerberoastable service accounts have passwords > 25 characters and rotated within 12 months | CIS L1 | **Non-compliant** | svc-mssql: 2yr old, svc-backup: 18mo, svc-web: 6mo — all potentially crackable |
| 1.2 | All service accounts use gMSA or MSA where technically feasible | CIS L2 | **Non-compliant** | No gMSA deployed; all service accounts are regular user accounts |
| 1.3 | No accounts have DONT_REQUIRE_PREAUTH set | CIS L1 | **Non-compliant** | svc-legacy, svc-monitor both have this flag |
| 1.4 | KRBTGT password rotated within the past 180 days | CIS L1 | **Non-compliant** | KRBTGT hash not rotated in 3 years |
| 1.5 | High-privilege accounts (DA, EA, SA) are members of Protected Users security group | CIS L2 | **Non-compliant** | tallen not in Protected Users; Administrator not in Protected Users |
| 1.6 | Service accounts are not members of privileged groups (DA, EA) | CIS L1 | **Non-compliant** | svc-backup in Backup Operators (high-privilege built-in) |

---

## 2. Delegation Configuration

| # | Control | CIS Ref | Corp Status | Evidence |
|---|---------|---------|-----------------|---------|
| 2.1 | No non-DC accounts have unconstrained delegation | CIS L1 | **Non-compliant** | svc-backup has unconstrained delegation |
| 2.2 | All constrained delegation uses protocol transition only where required | CIS L2 | **Compliant** | svc-mssql uses standard constrained delegation |
| 2.3 | DCs use unconstrained delegation only (expected behaviour) | N/A | N/A | DC-level delegation is expected and acceptable |
| 2.4 | No computer objects have msDS-AllowedToActOnBehalfOfOtherIdentity set to non-admin accounts | CIS L2 | **Compliant** | No RBCD misconfiguration detected |

---

## 3. Privileged Access

| # | Control | CIS Ref | Corp Status | Evidence |
|---|---------|---------|-----------------|---------|
| 3.1 | Domain Admins group has fewer than 5 members | CIS L1 | **Compliant** | DA: tallen, Administrator (2 members) |
| 3.2 | Enterprise Admins group is empty except during forest operations | CIS L1 | **Compliant** | EA: Administrator only |
| 3.3 | Schema Admins group is empty | CIS L1 | **Compliant** | SA: empty |
| 3.4 | No regular user accounts are in Backup Operators | CIS L1 | **Non-compliant** | svc-backup (service account) is in Backup Operators |
| 3.5 | LAPS is deployed on all workstations | CIS L1 | **Non-compliant** | LAPS only on IT computers; Finance and HR workstations lack LAPS |
| 3.6 | Tiered admin model enforced — Tier 0 (DC) admins do not log on to Tier 1/2 systems | CIS L2 | **Non-compliant** | No tiering enforced; tallen (DA) has no logon restrictions |

---

## 4. ACL / Permission Model

| # | Control | CIS Ref | Corp Status | Evidence |
|---|---------|---------|-----------------|---------|
| 4.1 | No non-admin accounts have GenericWrite on privileged groups | CIS L1 | **Non-compliant** | svc-deploy has GenericWrite on IT-Admins |
| 4.2 | No non-admin accounts have WriteDacl on the domain object | CIS L1 | **Compliant** | No non-admin WriteDacl detected |
| 4.3 | DS-Replication-Get-Changes-All rights on domain object granted only to DCs and Azure AD Connect | CIS L1 | **Compliant** | Replication rights: DC machine accounts only (at baseline — check after engagement) |
| 4.4 | AdminSDHolder ACL reviewed and non-default ACEs removed | CIS L2 | **Unknown** | AdminSDHolder ACL not audited in this engagement |
| 4.5 | Password reset delegation scoped to specific accounts only | CIS L1 | **Non-compliant** | Helpdesk-Staff can reset any Finance or HR OU user |

---

## 5. Audit Policy

| # | Control | CIS Ref | Corp Status | Evidence |
|---|---------|---------|-----------------|---------|
| 5.1 | Audit Kerberos Service Ticket Operations: Success | CIS L1 | **Unknown** | Not verified in current GPO config |
| 5.2 | Audit Kerberos Authentication Service: Success and Failure | CIS L1 | **Unknown** | Not verified |
| 5.3 | Audit Directory Service Access: Success | CIS L1 | **Unknown** | Required for DCSync detection (Event 4662) |
| 5.4 | Audit Logon: Success and Failure | CIS L1 | **Partially compliant** | Workstation Baseline GPO enables logon auditing on workstations; not confirmed on servers |
| 5.5 | Audit Account Management: Success | CIS L1 | **Unknown** | Required for group membership changes (Event 4728) |

---

## 6. GPO Hardening

| # | Control | CIS Ref | Corp Status | Evidence |
|---|---------|---------|-----------------|---------|
| 6.1 | SMB signing required on all servers and DCs | CIS L1 | **Non-compliant** | fs01 does not require SMB signing |
| 6.2 | SMB signing required on all workstations | CIS L2 | **Non-compliant** | No GPO enforces workstation signing |
| 6.3 | LM and NTLM authentication restricted (NTLMv2 minimum) | CIS L1 | **Unknown** | Network security: LAN Manager Authentication Level not confirmed |
| 6.4 | LDAP signing required | CIS L1 | **Unknown** | Domain controller LDAP server signing requirements not confirmed |
| 6.5 | Fine-Grained Password Policy for service accounts: 25+ chars | CIS L1 | **Non-compliant** | No FGPP deployed; service accounts subject to default 12-char policy |
| 6.6 | AppLocker or Windows Defender Application Control on all workstations | CIS L2 | **Partially compliant** | AppLocker on Finance workstations; missing on HR workstations |

---

## Scoring Summary

| Category | Controls | Compliant | Non-compliant | Unknown | Score |
|----------|----------|-----------|---------------|---------|-------|
| Account & Credential Hygiene | 6 | 0 | 6 | 0 | 0% |
| Delegation Configuration | 4 | 2 | 1 | 0 | 50% |
| Privileged Access | 6 | 2 | 4 | 0 | 33% |
| ACL / Permission Model | 5 | 2 | 2 | 1 | 40% |
| Audit Policy | 5 | 0 | 0 | 5 | Unknown |
| GPO Hardening | 6 | 0 | 3 | 3 | 0% |
| **Total** | **32** | **6** | **16** | **9** | **~21%** |

**Overall posture: HIGH RISK**

---

## Top 5 Remediations (by path-breaking impact)

1. **Migrate service accounts to gMSA** — eliminates Kerberoasting for svc-mssql, svc-backup, svc-web; breaks PATH-001 step 1 and PATH-003 step 1.
2. **Remove DONT_REQUIRE_PREAUTH from svc-legacy and svc-monitor** — eliminates AS-REP roasting; breaks PATH-002 step 1.
3. **Remove GenericWrite ACE on IT-Admins for svc-deploy** — breaks PATH-001 step 3 (the critical escalation hop).
4. **Convert svc-backup to constrained delegation** — eliminates TGT theft; breaks PATH-003 step 2.
5. **Enable SMB signing on all systems** — eliminates NTLM relay (complementary to PTH prevention).
