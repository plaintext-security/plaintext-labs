# Corp — Defense Control Matrix

> Maps each attack technique from modules 03-08 to its prevention and detection controls.
> Use this matrix to drive your tiered admin model design and GPO specification.

---

## Control Matrix

| ATT&CK ID | Technique | Module | Prevention Control | Detection Control | Architectural Fix |
|-----------|-----------|--------|-------------------|-------------------|-------------------|
| T1558.003 | Kerberoasting | 03 | Migrate service accounts to gMSA (120-char random passwords); add to Protected Users (no RC4) | Event 4769 with TicketEncryptionType=0x17 from non-DC source | gMSA eliminates the attack entirely — no crackable password |
| T1558.004 | AS-REP Roasting | 03 | Remove DONT_REQUIRE_PREAUTH flag from all accounts | Event 4768 with PreAuthType=0 from non-DC | Enforce pre-authentication across all accounts via FGPP |
| T1550.002 | Pass-the-Hash | 04 | Protected Users (no NTLM auth); Credential Guard (virtualises LSASS); tiering (hash never co-located with attack surface) | Event 4624 Type 3 with AuthPackage=NTLM from unexpected source | Credential Guard prevents LSASS dump; tiering prevents co-location |
| T1003.006 | DCSync | 04 | Restrict DS-Replication rights to DC machine accounts + approved sync services only | Event 4662 with DS-Replication-Get-Changes-All from non-DC account | Audit domain object ACL on schedule; alert on any new grantee |
| T1021.002 | SMB Lateral Movement | 06 | SMB signing required (blocks relay); LAPS (unique local admin per host); tiering (Tier 2 hosts can't admin each other) | Event 7045 (service installed) + 4624 Type 3 on target from unusual source | SMB signing + LAPS + tiering together eliminate the common lateral movement path |
| T1047 | WMI Lateral Movement | 06 | Host firewall rules blocking DCOM from non-admin subnets; tiering (Tier 2 can't admin Tier 1/0) | Event 4688 (process creation) with WmiPrvSE.exe as parent + unusual command line | Firewall + tiering; WMI is harder to block than SMB but the credential co-location issue is the same |
| T1558.001 | Golden Ticket | 07 | Rotate krbtgt twice; Protected Users (4h TGT lifetime); Authentication Policy Silos (restrict TGT issuance host) | Event 4769 with anomalous PAC or unusual ticket lifetime; behavioural anomaly on account that hasn't logged in before | Authentication Policy Silos restrict which hosts Tier 0 accounts can use — even a golden ticket can't grant access to a host from which the account is banned |
| T1558.002 | Silver Ticket | 07 | Protect service account credentials (gMSA); no KDC contact means no 4769 signal — prevention is the only reliable control | Event 4624 anomaly (no corresponding 4769 for the session); advanced: KDC PAC validation | gMSA eliminates the crackable service account hash; no hash = no silver ticket |
| T1484.001 | ACL Abuse (GenericWrite) | 05 | Audit and remove non-default write ACEs on privileged groups; use JIT for group management | Event 4728 (member added to security-enabled global group) | JIT access + ACL audit on schedule; automated alerts on privileged group membership changes |
| T1134.001 | Token Impersonation (Delegation) | 05 | Remove unconstrained delegation; use constrained delegation only where required; Protected Users cannot be delegated | Unusual computer-to-computer authentication (unconstrained delegation coercion) | Constrained delegation is acceptable; unconstrained is the structural risk |

---

## Prevention vs. Detection by Attack Phase

### Initial Access to Domain Credential
| Attack | Can be Prevented? | Prevention | Detection |
|--------|------------------|------------|-----------|
| Kerberoasting | Yes (gMSA) | gMSA / Protected Users | 4769 RC4 |
| AS-REP Roast | Yes (pre-auth flag) | Remove DONT_REQUIRE_PREAUTH | 4768 PreAuthType=0 |

### Credential Replay / Lateral Movement
| Attack | Can be Prevented? | Prevention | Detection |
|--------|------------------|------------|-----------|
| Pass-the-Hash (NTLM) | Largely yes | Protected Users + Credential Guard | 4624 Type 3 NTLM |
| Pass-the-Ticket | Partially | Protected Users (short TGT life) | Anomalous 4769 source |
| PTH via psexec | Partially | SMB signing + LAPS | 4624 Type 3 + 7045 |
| PTH via wmiexec | Partially | DCOM firewall rules | 4688 under WmiPrvSE.exe |

### Privilege Escalation
| Attack | Can be Prevented? | Prevention | Detection |
|--------|------------------|------------|-----------|
| GenericWrite ACL abuse | Yes (ACL fix) | Remove non-default ACEs | 4728 group membership change |
| Unconstrained delegation | Yes (convert to constrained) | Remove delegation flag | TGT theft events |
| DCSync rights | Yes (ACL audit) | Restrict DS-Replication grants | 4662 non-DC replication |

### Persistence
| Attack | Can be Prevented? | Prevention | Detection |
|--------|------------------|------------|-----------|
| Golden ticket | Partial (krbtgt rotation) | Auth Policy Silos; rotate krbtgt | PAC anomaly; anomalous 4768 |
| Silver ticket | Yes (gMSA) | gMSA eliminates crackable hash | No reliable signal (no KDC contact) |
| DCSync rights | Yes (ACL audit) | Audit and revoke | 4662 |
| AdminSDHolder abuse | Yes (AdminSDHolder audit) | Audit and remove non-default ACEs | ACL diff on AdminSDHolder |

---

## Tiered Admin Model — Control Coverage

### What tiering prevents (architecturally)
1. **Credential co-location:** Tier 0 credentials never appear in LSASS on Tier 2 hosts. A compromised Finance workstation cannot contain a domain admin hash.
2. **Lateral movement to Tier 0:** GPO logon restrictions prevent non-Tier-0 accounts from authenticating to DCs, even with a valid credential.
3. **DA-credential-in-memory exposure:** PAWs are used only for Tier 0 tasks; no internet, no email, no untrusted code execution on the device holding DA credentials.

### What tiering does NOT prevent (still needs patching)
1. **Kerberoasting:** Credential attacks on service accounts in any tier — still requires gMSA.
2. **AS-REP roasting:** Still requires the pre-auth flag to be set.
3. **ACL misconfigurations:** Tiering doesn't remove a GenericWrite ACE — that's a direct remediation.
4. **Lateral movement within a tier:** A Finance workstation compromise can still pivot to other Finance workstations — intra-tier segmentation is a separate network control.

---

## GPO Specification — Tier Logon Restrictions

### Tier 0 accounts (tallen, Administrator, krbtgt)
Apply to: **All Tier 1 and Tier 2 computers** via a domain-wide GPO with exceptions for DCs.

| Policy Path | Setting | Value |
|-------------|---------|-------|
| `Computer Configuration\Policies\Windows Settings\Security Settings\Local Policies\User Rights Assignment\Deny log on locally` | Add Tier 0 account group | `CORP\Tier0-Admins` |
| `Computer Configuration\Policies\Windows Settings\Security Settings\Local Policies\User Rights Assignment\Deny log on through Remote Desktop Services` | Add Tier 0 account group | `CORP\Tier0-Admins` |

### Tier 1 accounts (IT-Admins sgarcia, pmartinez)
Apply to: **All Tier 2 computers** (Finance, HR workstations).

| Policy Path | Setting | Value |
|-------------|---------|-------|
| Deny log on locally | Tier 1 admin group | `CORP\Tier1-Admins` |
| Deny log on through RDS | Tier 1 admin group | `CORP\Tier1-Admins` |

### Protected Users — add these accounts
| Account | Justification |
|---------|--------------|
| `tallen` | DA account — no NTLM, no delegation, 4h TGT |
| `Administrator` | Built-in DA — no NTLM, short TGT |
| `svc-backup` | High-privilege service account in Backup Operators — remove delegation risk |
| `svc-mssql` | Kerberoastable — Protected Users removes RC4 eligibility |
| `svc-backup` | Unconstrained delegation — Protected Users blocks delegation entirely |

**Caution before adding:** Verify that no application authenticates to these accounts via NTLM or requires delegation — Protected Users breaks both. Test in a lab before production.
