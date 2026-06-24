# Corp — Active Directory Domain Specification

> **Fictional environment for training purposes only.**
> This document describes the Corp AD domain used throughout Track 06.
> All names, IP addresses, and configurations are invented.

---

## Forest & Domain Topology

| Property | Value |
|----------|-------|
| Forest root domain | `CORP.LOCAL` |
| NetBIOS name | `CORP` |
| Forest functional level | Windows Server 2016 |
| Domain functional level | Windows Server 2016 |
| External trusts | None |
| Child domains | None |

The forest contains a single domain: `CORP.LOCAL`. There are no child domains and no external trusts. All Kerberos tickets are issued by the DC in this domain. A single forest means a single Kerberos realm and a single schema.

---

## Domain Controllers

| Hostname | IP | Role |
|----------|----|------|
| `dc01.corp.local` | 10.10.0.10 | PDC Emulator, RID Master, Infrastructure Master |
| `dc02.corp.local` | 10.10.0.11 | Schema Master, Domain Naming Master (secondary DC) |

Both DCs run Windows Server 2019 Standard. `dc01` is the PDC emulator and the preferred KDC for most clients. The KRBTGT account password was last reset **3 years ago** (a known risk — golden ticket persistence lives as long as this hash is valid).

---

## Organisational Unit Structure

```
CORP.LOCAL
├── Domain Controllers (built-in)
├── Corp
│   ├── Finance
│   │   ├── Users          (14 user accounts)
│   │   └── Computers      (8 workstations: WS-FIN-01 through WS-FIN-08)
│   ├── IT
│   │   ├── Users          (7 user accounts — sysadmins and helpdesk)
│   │   └── Computers      (3 workstations + 2 servers: FS01, WSUS01)
│   └── HR
│       ├── Users          (9 user accounts)
│       └── Computers      (5 workstations: WS-HR-01 through WS-HR-05)
└── Service Accounts
    └── (6 managed service accounts — see below)
```

---

## User Accounts

### Finance OU

| Username | Display Name | Notes |
|----------|-------------|-------|
| `jsmith` | John Smith | **Initial foothold account.** Finance analyst. Member of Finance-Users group only. |
| `amurphy` | Alice Murphy | Finance manager. Member of Finance-Users, Finance-Managers. |
| `bwilson` | Bob Wilson | AP clerk. Member of Finance-Users. |
| `clee` | Carol Lee | Payroll. Member of Finance-Users, Payroll-Access. |
| `dthomas` | David Thomas | Finance-Users only. |
| `efoster` | Emma Foster | Finance-Users only. |
| `gharris` | Grace Harris | Finance-Users only. |
| `hjohnson` | Henry Johnson | Finance-Users only. |
| `ijones` | Iris Jones | Finance-Users only. |
| `jkim` | James Kim | Finance-Users only. |
| `klopes` | Karen Lopes | Finance-Users only. |
| `lmartin` | Liam Martin | Finance-Users only. |
| `mnguyen` | Mia Nguyen | Finance-Users only. |
| `npark` | Nathan Park | Finance-Users only. |

### IT OU

| Username | Display Name | Notes |
|----------|-------------|-------|
| `tallen` | Tom Allen | **IT admin.** Member of Domain Admins, IT-Admins. |
| `sgarcia` | Sara Garcia | Sysadmin. Member of IT-Admins. |
| `rrodriguez` | Ryan Rodriguez | Helpdesk. Member of Helpdesk-Staff. Can reset passwords for Finance and HR OUs. |
| `pmartinez` | Paula Martinez | Sysadmin. Member of IT-Admins. |
| `qwalker` | Quinn Walker | Helpdesk. Member of Helpdesk-Staff. |
| `ubrown` | Uma Brown | Junior IT. Member of IT-Staff. |
| `vdavis` | Vera Davis | Junior IT. Member of IT-Staff. |

### HR OU

| Username | Display Name | Notes |
|----------|-------------|-------|
| `wevans` | Will Evans | HR Manager. Member of HR-Users, HR-Managers. |
| `xtaylor` | Xena Taylor | HR. Member of HR-Users. |
| `yadams` | Yara Adams | HR. Member of HR-Users. |
| `zclark` | Zoe Clark | HR. Member of HR-Users. |
| `abaker` | Adam Baker | HR. Member of HR-Users. |
| `bscott` | Beth Scott | HR. Member of HR-Users. |
| `chill` | Chris Hill | HR. Member of HR-Users. |
| `dmitchell` | Dana Mitchell | HR. Member of HR-Users. |
| `ewhite` | Eli White | HR. Member of HR-Users. |

---

## Service Accounts (Service Accounts OU)

| Username | SPN | Password age | Notes |
|----------|-----|-------------|-------|
| `svc-mssql` | `MSSQLSvc/db01.corp.local:1433` | 2 years | SQL Server service account. Member of Domain Users only, but has `db_owner` on the financial DB. **Kerberoastable.** |
| `svc-backup` | `BackupSvc/backup01.corp.local` | 18 months | Backup agent. Member of Backup-Operators. **Kerberoastable.** |
| `svc-web` | `HTTP/intranet.corp.local` | 6 months | IIS app pool. Member of Domain Users. **Kerberoastable.** |
| `svc-legacy` | `LegacySvc/appserver01.corp.local` | 3 years | Legacy app. **No pre-authentication required (AS-REP roastable).** Member of Domain Users. |
| `svc-monitor` | `MonitorSvc/siem01.corp.local` | 1 year | SIEM integration. **No pre-authentication required (AS-REP roastable).** |
| `svc-deploy` | None | 8 months | Deployment automation. Member of IT-Admins. **Has GenericWrite on IT-Admins group (misconfiguration).** |

---

## Security Groups

| Group | Type | Members | Notes |
|-------|------|---------|-------|
| `Domain Admins` | Security, Global | `tallen`, `Administrator` | Highest privilege. Full control of domain. |
| `Enterprise Admins` | Security, Universal | `Administrator` | Forest-level admin. Only used during DCPromo. |
| `Schema Admins` | Security, Universal | (empty) | Should be empty — it is here. |
| `IT-Admins` | Security, Global | `tallen`, `sgarcia`, `pmartinez`, `svc-deploy` | Local admin on all servers. |
| `IT-Staff` | Security, Global | `ubrown`, `vdavis` | Read access to IT shares. |
| `Helpdesk-Staff` | Security, Global | `rrodriguez`, `qwalker` | Can reset passwords in Finance and HR OUs (delegated). |
| `Finance-Users` | Security, Global | All Finance OU users | Read/write to Finance file share. |
| `Finance-Managers` | Security, Global | `amurphy` | Approve access requests. Has `GenericWrite` on Finance-Users group. |
| `Payroll-Access` | Security, Global | `clee` | Access to payroll application. |
| `HR-Users` | Security, Global | All HR OU users | Read/write to HR file share. |
| `HR-Managers` | Security, Global | `wevans` | HR share admin. |
| `Backup-Operators` | Security, Builtin | `svc-backup` | Can back up and restore files on DCs (built-in — high privilege). |

---

## File Servers & Shares

| Server | Share | Access |
|--------|-------|--------|
| `fs01.corp.local` | `\\fs01\Finance` | Finance-Users (read/write) |
| `fs01.corp.local` | `\\fs01\HR` | HR-Users (read/write) |
| `fs01.corp.local` | `\\fs01\IT` | IT-Admins (read/write), IT-Staff (read) |
| `fs01.corp.local` | `\\fs01\Shared` | Authenticated Users (read) |

`fs01` is also accessible via SMB with NTLM authentication (SMB signing is **not required** — a known risk).

---

## Group Policy Objects

| GPO | Linked to | Key settings |
|-----|-----------|-------------|
| Default Domain Policy | Domain root | Password policy: 12 chars min, 90-day max age, complexity enabled |
| Workstation Baseline | Corp OU | Firewall ON, Defender enabled, audit policy (logon, object access) |
| Finance Workstation Policy | Corp/Finance/Computers | AppLocker (basic), USB disabled |
| IT Hardening Policy | Corp/IT/Computers | Credential Guard enabled, LAPS deployed |
| **[MISSING]** | Corp/HR/Computers | No hardening GPO applied — inherits only Workstation Baseline |
| **[MISSING]** | Service Accounts OU | No fine-grained password policy — subject to default 90-day, 12-char policy only |

**GPO gaps:**
- HR workstations have no AppLocker and no USB restriction — weaker than Finance workstations.
- Service accounts have no Fine-Grained Password Policy (FGPP) — they should have a stricter policy (e.g., 20+ char, no expiry with managed accounts) but fall under the default domain policy.
- No `Deny log on locally` or `Deny log on through RDP` restriction applied to service accounts across the domain — they could be used for interactive logon.

---

## Delegation Configuration

| Account | Delegation type | Allowed services |
|---------|----------------|-----------------|
| `svc-backup` | **Unconstrained delegation** | (any) — legacy configuration |
| `svc-mssql` | Constrained delegation | `MSSQLSvc/db01.corp.local:1433` |
| `dc01`, `dc02` | Unconstrained (DCs always have this) | N/A |

**Risk:** `svc-backup` has unconstrained delegation. Any user who authenticates to this service will have their TGT stored in memory on the backup server — a classic persistence/escalation vector.

---

## NTLM Fallback Surfaces

| Service | Reason NTLM accepted |
|---------|---------------------|
| `\\fs01\*` (SMB) | SMB signing not required; NTLM not disabled |
| `http://intranet.corp.local` | IIS configured for Windows Authentication (NTLM + Negotiate) |
| `\\dc01\SYSVOL`, `\\dc01\NETLOGON` | NTLM fallback enabled by default |
| Legacy app on `appserver01` | Application hardcoded for NTLM; Kerberos not supported |

---

## Key Risk Summary

1. **KRBTGT hash not rotated in 3 years** — any golden ticket created from a previous krbtgt hash is still valid.
2. **Three Kerberoastable service accounts** with multi-year-old passwords.
3. **Two AS-REP roastable accounts** (`svc-legacy`, `svc-monitor`).
4. **svc-backup has unconstrained delegation** — TGT theft vector.
5. **svc-deploy has GenericWrite on IT-Admins** — can add any user to IT-Admins.
6. **Finance-Managers has GenericWrite on Finance-Users** — can add members to the group.
7. **Helpdesk-Staff can reset passwords for Finance and HR OUs** — helpdesk compromise = Finance account takeover.
8. **SMB signing not required on fs01** — NTLM relay risk.
9. **HR workstations lack AppLocker** — easier code execution.
10. **Service accounts not in Protected Users** — eligible for Kerberos delegation and NTLM auth.
