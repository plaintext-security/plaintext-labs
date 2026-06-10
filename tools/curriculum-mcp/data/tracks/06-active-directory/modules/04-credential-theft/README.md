# Module 04 — Credential Theft & Replay

*Module concept · [Go to the hands-on lab →](lab.md)*


**Active Directory & Windows Security** — *a password hash is not a password, but in Windows it is often just as good.*

## Why this matters

Pass-the-hash (PTH) is one of the most durable attack techniques in Windows environments because it exploits a fundamental property of the NTLM authentication protocol, not a bug in any single product. Every major Windows lateral movement campaign — from NotPetya to the SolarWinds intrusion — has relied on some form of credential theft and replay. The defence requires understanding exactly when NTLM can and cannot be used as a replay credential, and why some architectures completely remove that surface while others leave it intact by design.

## Objective

Extract NTLM hashes from a Windows-style credential store using `secretsdump.py`, demonstrate pass-the-hash via `psexec.py` and `smbexec.py`, and explain the conditions under which PTH is possible vs. impossible.

## The core idea

Windows stores a user's credential as an **NT hash** — specifically, the MD4 hash of the UTF-16LE encoding of the password. This matters because NTLM authentication doesn't transmit the password; it uses the hash in a challenge-response protocol where the server sends a nonce, the client signs it with the NT hash, and the server verifies. The consequence: if you possess the NT hash, you can authenticate as the user without ever knowing the underlying password. This is what "pass the hash" means — not a vulnerability in the protocol but a property of how NTLM was designed.

Where do hashes live? The primary sources are: the **SAM database** on local machines (protected by SYSKEY, but extractable with SYSTEM privileges), **LSASS memory** on any machine where the user has authenticated (protected by PPL — Protected Process Light — on newer Windows, but bypassed by various techniques), and most importantly for a DC, **the NTDS.dit database** — the Active Directory credential store on the domain controller. `secretsdump.py` can extract from all three sources, using different techniques: VSS shadow copy + offline parsing for NTDS.dit, or live DRSUAPI replication (DCSync) when the attacker has sufficient rights.

The reason PTH is so dangerous in practice is that Windows historically used the *same* NTLM hash for local and domain authentication, and local admin credentials were historically shared across machines (the same local admin password on every workstation). LAPS (Local Administrator Password Solution) was introduced precisely to break this — it rotates the local admin password per machine and stores it in AD. Without LAPS, one cracked or stolen local admin hash gives you lateral movement across the entire estate. Even with LAPS, you still face the domain credential hash problem: a domain account that logs on to multiple machines leaves its NTLM hash in LSASS on every one of them.

The specific impacket tools: `psexec.py` authenticates via SMB using PTH, creates a named pipe, and drops a service binary — noisy, creates Event 7045. `smbexec.py` achieves the same result without dropping a binary, instead executing commands via a temporary service that reads from SMB shares — quieter on disk, but still creates service events. `wmiexec.py` uses WMI (DCOM) instead of SMB, leaving a different artefact profile. Each tool leaves a distinct event signature, and defenders should know all three.

## Learn (~3 hrs)

**Pass the hash mechanics**
- [T1550.002 — Pass the Hash (MITRE ATT&CK)](https://attack.mitre.org/techniques/T1550/002/) — procedure examples and detections. Note the sub-technique distinction from pass-the-ticket.

**Secretsdump and DCSync**
- [Impacket secretsdump.py — source and usage (GitHub)](https://github.com/fortra/impacket/blob/master/examples/secretsdump.py) — read the module docstring and the argument descriptions. Understand the difference between SAM extraction, LSASS extraction, and DCSync.
- [DCSync Attack Explained (adsecurity.org)](https://adsecurity.org/?p=1729) — the DCSync technique: using DRSUAPI replication rights to pull any credential from the DC without touching NTDS.dit on disk.

**LAPS and mitigation**
- [LAPS — Local Administrator Password Solution (Microsoft Docs)](https://learn.microsoft.com/en-us/windows-server/identity/laps/laps-overview) — what LAPS solves (shared local admin passwords) and what it does not solve (domain credential replay). Read the overview section.

## Key concepts
- NT hash = MD4(UTF-16LE(password)) — the value NTLM uses for authentication, not the password itself.
- Pass-the-hash authenticates with the hash directly — no password needed.
- `secretsdump.py` can extract from SAM (local), LSASS (remote, privileged), or NTDS.dit via DCSync (domain admin).
- DCSync uses legitimate DRSUAPI replication to pull credentials from a DC — no need to touch NTDS.dit on disk.
- LAPS breaks shared local admin passwords; it does not prevent domain credential PTH.
- Detection: Event 4624 (Logon Type 3) with NtLmSsp provider from an unexpected source host; Event 4776 for NTLM authentication events.
- Mitigation: Protected Users group, Credential Guard (virtualises LSASS), SMB signing to prevent relay.

## AI acceleration

Ask a model to write a Python script using the `impacket` library to perform a read-only secretsdump against a local SAM file (no live target needed). Verify the script compiles and runs against the bundled SAM dump in `data/`. The model is good at impacket API calls but often confuses the SAM vs. NTDS.dit extraction paths — check each method name against the impacket source.
