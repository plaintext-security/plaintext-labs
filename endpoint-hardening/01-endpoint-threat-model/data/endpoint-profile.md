# Endpoint Profile — Financial-Services Org

These two hosts are representative of a mid-size financial-services firm's pre-hardening estate.
They are modelled on the kind of endpoints that real breaches have started from — see the
**Real-world anchor** at the bottom.

## Host A: Finance Analyst Workstation

**Hardware:** Dell Latitude 5540, Intel Core i7, 16 GB RAM, 512 GB NVMe SSD, TPM 2.0 present.

**OS:** Windows 11 Enterprise (23H2), domain-joined to `corp.example.internal`.

**Software installed:**
- Microsoft 365 Apps (Word, Excel, Outlook, Teams) — version current
- Citrix Workspace — connects to VDI environment for core banking application
- Cisco AnyConnect VPN client — split-tunnel configuration
- Chrome 124 (default browser)
- Adobe Acrobat Reader
- 7-Zip
- Python 3.11 (IT-deployed for report automation scripts)
- Git for Windows (user-installed, not in IT policy)

**Network position:**
- Primary interface: corporate LAN, VLAN 10 (Finance), /24 subnet
- VPN: split-tunnel (only `10.0.0.0/8` goes through VPN when remote)
- SMB share access: `\\fileserver01\Finance` (financial reports, salary data)
- RDP access: permitted to `db-reporting01.corp.example.internal` (read-only)
- Internet: outbound HTTP/HTTPS permitted (proxy: `proxy.example.internal:8080`)

**Data held locally:**
- Cached Outlook OST (email including payroll approval chains)
- Excel models with employee salary data (periodically downloaded from share)
- Citrix session tokens cached in memory during business hours
- Chrome saved passwords (LastPass not deployed; native Chrome password manager)
- VPN credentials cached in Windows Credential Manager
- Domain credentials cached in LSASS

**Authentication:**
- Domain password (complexity enforced: 12 chars, 90-day rotation — rarely enforced)
- **No MFA for local machine or VPN** (MFA deployed only for O365)
- Local administrator account: disabled per policy (periodically re-enabled by user IT tickets)
- Note: at least one VPN account is for a *former* contractor and was never disabled

**Current hardening state:**
- Windows Defender enabled, definitions current
- Bitlocker enabled on OS drive (recovery key escrowed in AD)
- Windows Firewall: default settings, no custom rules
- No CIS benchmark applied
- SMB signing: not enforced
- PowerShell: Execution Policy set to `RemoteSigned` (bypassable)

---

## Host B: Linux Application Server

**Hardware:** VMware virtual machine, 4 vCPUs, 8 GB RAM, 100 GB virtual disk.
**Hypervisor host:** `esx01.corp.example.internal` (ESXi 8.0)

**OS:** Ubuntu 22.04 LTS, kernel 5.15.0-102-generic.

**Role:** Internal payroll calculation API. Receives POST requests from the Citrix session
backend; returns salary and deduction calculations. Connects to PostgreSQL database on
`db01.corp.example.internal:5432`.

**Network position:**
- Interface: corporate LAN, VLAN 20 (Servers), /24 subnet
- Inbound: TCP 8443 from VLAN 10 (Finance) and VLAN 30 (Citrix backend)
- Outbound: TCP 5432 to `db01.corp.example.internal`
- Outbound: TCP 443 to package mirrors (quarterly maintenance window)
- SSH: TCP 22 from `jumphost01.corp.example.internal` only (via firewall rule)

**Software:**
- Python 3.10 (payroll API: `/opt/payroll-api/`, runs as user `payroll`)
- PostgreSQL client libraries (`libpq5`)
- nginx 1.24 (reverse proxy, terminates TLS for the API)
- OpenSSH 8.9 (`sshd` running)
- auditd (installed, minimal configuration — default rules only)
- osquery (not installed)
- Wazuh agent (not installed)

**Credentials on host:**
- Service account `payroll` (no login shell, runs the API process)
- Database password in `/opt/payroll-api/config/db.conf` (plaintext)
- nginx TLS private key in `/etc/ssl/private/payroll-api.key` (permissions: 640, root:ssl-cert)
- Automated deploy key: `/home/deploy/.ssh/id_ed25519` (used by CI/CD pipeline)

**Current hardening state:**
- UFW enabled with rules for VLAN 10, 20, 30 access
- No CIS benchmark applied
- Root login: permitted via SSH (key-based only)
- Password authentication via SSH: disabled
- `sudo`: `deploy` user has `NOPASSWD: /usr/bin/systemctl restart payroll`
- SUID binaries: default Ubuntu set (not audited)
- auditd: running, default rules (no privileged command auditing)
- No AppArmor profiles loaded for `python3` or `nginx`

---

## Notes for the threat model exercise

Both hosts are representative of the organization's current pre-hardening state. The threat
model should consider:

1. **Threat actor classes:** opportunistic ransomware (commodity malware, phishing), targeted
   financially-motivated intrusion (wire fraud, data exfiltration), and insider threat
   (employee with legitimate access abusing it).

2. **Crown jewels:** salary data, payroll calculation API (financial manipulation potential),
   domain credentials (lateral movement), banking credentials (VDI session theft).

3. **Initial access assumptions:** phishing email landing a payload on the workstation, or a
   reused/leaked credential on a remote-access account, are the most realistic initial access
   vectors. Supply-chain compromise of a Python package is a realistic vector for the
   application server.

---

## Real-world anchor — Colonial Pipeline (2021)

This profile's `No MFA for VPN` weakness and `former contractor's VPN account never disabled`
are not invented hypotheticals. The **Colonial Pipeline ransomware attack (May 2021)**, attributed
to the DarkSide group, began exactly this way: the attackers got in using a single compromised
password for an **inactive VPN account that did not have multi-factor authentication enabled**.
That one missing control — an endpoint/remote-access authentication weakness, not a software CVE —
led to a six-day shutdown of the largest US fuel pipeline.

When you trace attack paths for Host A, treat the VPN/MFA gap as a **named, real** initial-access
vector (ATT&CK **T1078 Valid Accounts**, sub-technique **T1078.002 Domain Accounts**), and the
post-access credential theft as **T1003.001 (OS Credential Dumping: LSASS Memory)**. Your top-five
backlog should make "the Colonial Pipeline path" one of the first things you close.

Reference: CISA / public reporting on the Colonial Pipeline incident; MITRE ATT&CK T1078, T1003.001.
