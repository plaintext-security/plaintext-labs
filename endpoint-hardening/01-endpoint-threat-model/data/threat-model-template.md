# Threat Model — Financial-Services Org Endpoints

**Author:** [Your name]
**Date:** [YYYY-MM-DD]
**Scope:** Finance analyst workstation (Windows 11) and payroll API server (Ubuntu 22.04)
**Methodology:** STRIDE

---

## 1. Assets

| Asset | Host | Value (L/M/H) | Adversary use |
|-------|------|---------------|---------------|
| Domain credentials (LSASS) | Workstation | H | Lateral movement, further compromise |
| Cached Outlook email (salary approvals) | Workstation | M | Fraud enablement, intelligence |
| Local salary Excel files | Workstation | H | Data exfiltration |
| Chrome saved passwords | Workstation | M | Account takeover |
| Citrix session tokens | Workstation | H | Pivot to VDI / core banking |
| | | | |
| PostgreSQL database password (plaintext) | App server | H | Direct DB access |
| TLS private key | App server | H | MITM, impersonation |
| CI/CD deploy SSH key | App server | M | Supply chain impact |
| Payroll API process (running) | App server | H | Financial manipulation |

*Add rows for any assets you identify that are missing from the initial list.*

---

## 2. Attack Paths

For each path: entry point → technique (ATT&CK ID) → intermediate step → target asset.

| # | Entry point | Technique | Step | Target asset | STRIDE category |
|---|------------|-----------|------|--------------|-----------------|
| 0 | Compromised VPN account, no MFA (**Colonial Pipeline 2021**) | T1078.002 (Valid Accounts: Domain) | Remote access as the former contractor → reach the workstation | Domain foothold | Spoofing / EoP |
| 1 | Phishing email | T1566.001 (Spearphishing Attachment) | Macro executes payload | LSASS credentials | Spoofing / EoP |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

*Path 0 is a worked example anchored to a real breach (Colonial Pipeline, May 2021 — DarkSide got
in via a single compromised VPN credential with no MFA on an inactive account). Fill in the rest
for: credential dumping (T1003.001), lateral movement via RDP (T1021.001), persistence via
scheduled task (T1053.005), privilege escalation via SUID (Linux), payroll API tampering.*

---

## 3. Mitigations

For each attack path above, list the mitigations that close or narrow it.

| Path # | Mitigation | CIS Control | ATT&CK Mitigation | Status |
|--------|-----------|-------------|-------------------|--------|
| 1 | Enable Windows Credential Guard | CIS Win 18.8.3.1 | M1043 | Not applied |
| | | | | |
| | | | | |

---

## 4. Prioritised Control Backlog

Rank the top five mitigations by: (attack paths closed × asset value).

| Priority | Control | Paths closed | Asset value protected | Module |
|----------|---------|-------------|----------------------|--------|
| 1 | | | | 02 or 03 |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

---

## 5. Residual Risk

After applying the top five controls, list the remaining high-value paths that are not closed
and document the accepted residual risk.

| Risk | Likelihood | Impact | Accepted by | Date |
|------|-----------|--------|-------------|------|
| | | | | |
