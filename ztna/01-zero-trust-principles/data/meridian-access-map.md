# Meridian Financial — Current Access Architecture

*Fictional scenario for Lab 01. Do not use for any purpose outside this curriculum.*

---

## Organization overview

- **Size:** ~800 employees; offices in Chicago (HQ), Dallas, and Denver
- **Remote workforce:** ~60% work remotely full-time or hybrid
- **Contractors:** ~120 contractors (legal, IT, data analytics) — all BYOD, no corporate device management
- **Regulated data:** PII, financial records, SWIFT transaction data; subject to SOX and PCI-DSS

---

## Remote access

| Control | Detail |
|---|---|
| VPN product | Cisco AnyConnect, split-tunnel |
| Authentication | AD username + password + Cisco Duo TOTP (MFA enforced at VPN login) |
| Network grant | Full access to the corporate data-centre /20 (`10.10.0.0/20`) upon successful VPN auth |
| Contractor access | Same VPN pool; contractors issued a separate AD account but land on the same /20 |
| Session duration | VPN sessions persist indefinitely; no re-authentication after initial connect |

**Gap indicators:**
- MFA is enforced once at VPN login, not at application access
- "On network" means access to all servers in the /20; no per-application segmentation
- Contractor BYOD devices are not checked for posture before being granted network access

---

## Identity and directory

| Control | Detail |
|---|---|
| Primary directory | Active Directory (on-prem, two domain controllers in Chicago datacenter) |
| Cloud sync | Azure Entra ID sync via Azure AD Connect; ~800 user accounts synced |
| SSO in pilot | Okta deployed to ~200 users for SaaS applications (Salesforce, Workday, Slack) |
| Application auth | Mixed: core banking via Kerberos, HR/CRM via SAML 2.0, some legacy apps via LDAP bind, three apps with embedded service-account credentials |
| Privileged accounts | Three service accounts with Domain Admin; shared credentials stored in a password-protected Excel sheet accessible to the application team (6 people) |
| MFA coverage | Enforced: VPN login, Okta-covered SaaS apps (~200 users). **Not enforced:** internal apps, core banking, RDP, SharePoint on-prem |
| Offboarding | Manual; average 4-day lag between termination and AD account disable |

**Gap indicators:**
- No single identity provider; Kerberos, SAML, LDAP, and embedded credentials coexist
- MFA not enforced for most internal access paths
- Shared Domain Admin service accounts are a lateral movement superhighway
- 4-day offboarding lag means terminated-employee access is a real risk window

---

## Endpoints and device management

| Control | Detail |
|---|---|
| Corporate laptops | ~680 domain-joined Windows 11 laptops issued by IT |
| EDR | CrowdStrike Falcon deployed to 510 of 680 corporate devices (~75%); deployment project stalled 8 months ago |
| Contractor devices | 120 personal laptops (mix of Windows/macOS); **no EDR, no MDM enrollment, no patch level check** |
| Patch management | WSUS for domain-joined Windows; average patch lag is 14 days for critical, 45 days for high |
| Device identity | No client certificates; device identity = domain join status. No device posture signal fed into access decisions |
| Disk encryption | BitLocker enforced on 70% of corporate laptops; no enforcement on contractors |

**Gap indicators:**
- 25% of corporate devices are not EDR-enrolled; contractors have zero coverage
- Device posture not evaluated at access time — a compromised, unpatched device is treated the same as a healthy one
- No certificate-based device identity; "device trust" relies entirely on domain join, which can be spoofed if an attacker has domain credentials

---

## Network architecture

| Control | Detail |
|---|---|
| Data-centre network | Flat /20 in Chicago datacenter; servers are VLAN-separated by environment (prod/dev/test) but all VLANs are reachable from the VPN-assigned segment |
| Firewall | Palo Alto PA-3220 at perimeter; minimal internal segmentation rules; default-allow within the /20 |
| Server-to-server | No East-West inspection; unrestricted within datacenter VLANs |
| Cloud connectivity | Azure ExpressRoute for AD Connect sync; S2S VPN to Azure for SharePoint; SaaS apps accessed directly over internet |
| Monitoring | NetFlow exported to SIEM; no DPI on internal traffic; no IDS/IPS on East-West |

**Gap indicators:**
- Flat internal network: lateral movement from a single compromised host can reach all servers
- No East-West inspection means ransomware or an insider can move laterally undetected
- Production and dev/test are reachable from the same VPN segment — separation is VLAN-only with no firewall enforcement

---

## Application access

| Control | Detail |
|---|---|
| Core banking | On-prem; accessible via Kerberos SSO from any machine on the corporate network or VPN; no additional MFA at login |
| CRM (Salesforce) | SaaS; Okta SSO for the 200 Okta-enrolled users; other users access directly with username/password |
| HR (Workday) | SaaS; Okta SSO; MFA enforced |
| SharePoint | Azure-hosted; accessible via Entra ID SSO; MFA enforced for this app only |
| Legacy reporting app | On-prem; LDAP auth; no MFA; accessible by all VPN users |
| SWIFT gateway | On-prem; dedicated workstations in Chicago; accessible to any Domain Admin account over RDP |

**Gap indicators:**
- Core banking and the SWIFT gateway are accessible to any VPN-authenticated user without additional auth
- Legacy app accessible to all 800 VPN users despite being needed by ~20 finance staff
- SWIFT gateway accessible via RDP to Domain Admin accounts — a credential compromise leads directly to financial transaction access

---

## Logging and visibility

| Control | Detail |
|---|---|
| Log sources | Windows Event Log (security events), Palo Alto firewall logs, Cisco AnyConnect logs, Azure Entra ID sign-in logs |
| SIEM | Splunk Cloud; 30-day retention; 4 detection rules active |
| Device health correlation | None — device signals (patch level, EDR health) are not correlated with access events |
| Insider threat monitoring | None |
| Privileged account monitoring | No alerting on Domain Admin account usage outside business hours |

**Gap indicators:**
- No device health signals fed into access decisions or correlated with SIEM
- Domain Admin usage is logged but not alerted on
- 4 active detection rules for an 800-person firm with SWIFT access is severely under-instrumented
