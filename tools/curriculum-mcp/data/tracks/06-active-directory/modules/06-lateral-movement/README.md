# Module 06 — Lateral Movement

*Module concept · [Go to the hands-on lab →](lab.md)*


**Active Directory & Windows Security** — *getting domain admin is not the goal; reaching the data is — and data rarely lives on the first machine you land on.*

## Why this matters

Lateral movement is the phase where a breach becomes a crisis. An attacker with a single compromised workstation is contained; an attacker who has moved to three servers and a domain controller is an incident. The techniques in this module — SMB exec, WMI exec, and CrackMapExec-style host discovery — are the mechanisms used in every significant Windows intrusion documented in the past decade, from APT campaigns to ransomware pre-staging. Understanding them is how defenders build the network segmentation, host telemetry, and alert logic that actually contains a breach.

## Objective

Enumerate live hosts and their SMB signing status using CrackMapExec (netexec), perform lateral movement via impacket `psexec.py`/`wmiexec.py`, and explain the artefact differences between each execution method.

## The core idea

Lateral movement in a Windows domain fundamentally relies on three things: a credential (password hash, Kerberos ticket, or plaintext), a protocol that accepts it (SMB, WMI/DCOM, WinRM, RDP), and a remote execution primitive that the protocol enables (service creation, WMI process, PowerShell remoting, GUI session). The attacker's choice of technique is driven by what artefacts it leaves, not by which one "works" — they all work in a poorly defended environment.

**SMB** is the most abused because it is universally open on Windows networks for file sharing and domain authentication. The impacket `psexec.py` technique creates a random-named service binary in `ADMIN$` (C:\Windows), starts it, and communicates via a named pipe. It leaves the binary on disk (briefly), creates a Service Control Manager event (Event 7045 — "A new service was installed"), and leaves a Logon Type 3 event (4624) with the source IP. `smbexec.py` avoids the binary drop by executing commands via a temporary share and service, but still leaves the service creation event. `wmiexec.py` uses DCOM/WMI — it creates a `win32_process` object and reads the output via a share — leaving a different event profile: Event 4688 (process creation) rather than 7045.

**SMB signing** is the network-level control that prevents NTLM relay attacks, which are lateral movement's close cousin. When SMB signing is required, every SMB packet must be signed with the session key, preventing a man-in-the-middle from relaying an authenticated session from host A to host B. When signing is not required (the default for workstations, even today), an attacker on the network can relay NTLM authentication from one machine to another and execute as that machine's credential without ever cracking anything. `CrackMapExec`/`netexec` has a flag to enumerate SMB signing status across a subnet in seconds — this is a standard finding in any penetration test.

**CrackMapExec (netexec)** is the operational tool for lateral movement at scale. It wraps the underlying impacket protocols into a single interface, accepts multiple target formats (CIDR ranges, host lists), and supports credential spraying, hash-based authentication, module execution (running commands, dumping SAM, executing BloodHound collection) across dozens of hosts simultaneously. A single `nxc smb 10.10.0.0/24 -u jsmith -p Welcome1!` tells you which hosts are alive, their OS version, their domain membership, and whether they have SMB signing enabled. This is the operational scanning pattern a real attacker uses to map the environment quickly after initial access.

## Learn (~3 hrs)

**SMB and Windows remote execution**
- [T1021.002 — SMB/Windows Admin Shares (MITRE ATT&CK)](https://attack.mitre.org/techniques/T1021/002/) — the technique, with procedure examples from real APT campaigns. Note the artefact differences listed in the detection section.
- [T1047 — WMI (MITRE ATT&CK)](https://attack.mitre.org/techniques/T1047/) — WMI as an execution primitive; why it's popular (available everywhere, frequently not monitored as carefully as SMB).

**NetExec / CrackMapExec**
- [NetExec (GitHub — Pennyw0rth)](https://github.com/Pennyw0rth/NetExec) — the maintained fork of CrackMapExec. Read the wiki's SMB module section. Key flags: `--smb-signing`, `-H` (pass hash), `--local-auth` (local account vs domain).

**Impacket lateral movement tools**
- [Impacket examples (GitHub)](https://github.com/fortra/impacket/tree/master/examples) — read the docstrings for `psexec.py`, `smbexec.py`, and `wmiexec.py`. Each docstring explains the mechanism and the artefacts.

**SMB relay**
- [NTLM Relay Attacks (byt3bl33d3r)](https://byt3bl33d3r.github.io/practical-guide-to-ntlm-relaying-in-2017-aka-getting-a-foothold-in-under-5-minutes.html) — the practical guide to NTLM relay, which explains why SMB signing matters and what it prevents.

## Key concepts
- Lateral movement = credential + protocol + execution primitive.
- `psexec.py` → service binary in ADMIN$ (Event 7045, Logon Type 3 4624).
- `smbexec.py` → temporary service, no binary drop (Event 7045, different named pipe).
- `wmiexec.py` → WMI/DCOM process creation (Event 4688, no Service Manager event).
- SMB signing required: prevents NTLM relay (critical control for workstation subnets).
- `nxc smb <subnet>` enumerates live hosts, OS, signing status in seconds.
- Every execution method leaves a Logon Type 3 (network logon) event on the target.

## AI acceleration

Ask a model to compare the Windows event IDs generated by `psexec.py`, `smbexec.py`, and `wmiexec.py` for the same lateral movement action. Cross-check each claim against the impacket source code and Microsoft's event ID documentation. This is a good AI use case (event/artefact comparison across tool variants) — but the model will sometimes conflate the tools' artefacts, so verification is essential.
