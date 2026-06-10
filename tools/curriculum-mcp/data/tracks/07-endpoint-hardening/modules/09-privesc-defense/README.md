# Module 09 — Local Privilege-Escalation Defense

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 07 — Endpoint & Host Hardening]** — *The hardening baseline gets an attacker to user-level access; privilege-escalation defense is what stops them from going further.*

## Why this matters

Track 01 (Offensive) covered local privilege escalation as an attacker technique. This module closes the loop from the defender's side. An attacker who lands code execution on a Linux host — through a phishing payload, a web shell, or a supply chain compromise — will typically be running as a low-privileged user. Their next move is privilege escalation: abusing a SUID binary, a writable sudo rule, a misconfigured service, or a world-writable PATH entry to reach root. Closing these paths is the difference between a containable incident and a full host compromise.

## Objective

Identify a SUID binary misconfiguration in a container, demonstrate the privilege escalation path it enables, then close the path using a combination of file permission remediation and AppArmor confinement — and verify the closure.

## The core idea

Linux privilege escalation is a taxonomy problem. There are roughly six categories of local privesc path, each requiring a different defensive control. SUID/SGID misconfigurations (binaries that run as root regardless of who executes them) are closed by auditing the SUID set with `find / -perm -4000` and removing the bit from any binary that doesn't legitimately require it. Sudo misconfigurations (`(ALL) NOPASSWD: ALL` or a binary with a known GTFOBin) are closed by auditing `/etc/sudoers` with `visudo -c` and applying the principle of least privilege. Writable PATH entries allow an attacker to substitute their own binary for one a SUID or sudo rule calls — closed by enforcing a controlled PATH in sudo rules. Cron jobs running as root with world-writable scripts are closed by auditing `crontab -l` and file permissions together. Kernel vulnerabilities are closed by patching (module 08) and by namespace/capability restrictions.

[GTFOBins](https://gtfobins.org/) is the reference database for this category. It lists every standard Unix binary with a known privilege escalation, shell escape, or file read technique. The attacker-side knowledge — which binaries can be abused — is the same knowledge the defender uses to audit the SUID set. A defender who hasn't read GTFOBins is auditing blindly; a defender who has can enumerate the dangerous subset of SUID binaries on a system in under a minute.

AppArmor and `fapolicyd` (module 04) complement permission remediation by adding a second layer: even if a SUID binary is present, a mandatory access control profile can constrain what it can do. An AppArmor profile on `/usr/bin/find` that denies write access to `/etc/` means that even if an attacker finds a way to abuse `find`'s SUID bit, they cannot write the files they'd need to complete the escalation. This is defense-in-depth: the SUID bit removal is the first layer; the MAC profile is the second.

The audit workflow for a hardened host follows a checklist pattern: enumerate SUID/SGID with `find`, cross-reference with GTFOBins, remove unnecessary bits, audit sudoers for broad grants, audit cron for world-writable scripts, check PATH in privileged contexts, review installed kernel version against known local privesc CVEs. This checklist should run as part of the compliance scan (module 07) so that a newly-added SUID binary triggers an alert rather than waiting for the next manual audit.

## Learn (~4 hrs)

**Privilege escalation taxonomy (attacker perspective — to understand what to defend)**
- [GTFOBins](https://gtfobins.org/) — the reference for SUID/sudo binary abuse; scan the index and click through a few (find, vim, python) to understand the pattern and what binaries enable escalation.
- [MITRE ATT&CK — T1134 Access Token Manipulation & T1548 Abuse Elevation Control](https://attack.mitre.org/techniques/T1548/) — real-world privilege escalation techniques and how attackers leverage them; read the sub-techniques for SUID/sudo abuse.

**Defensive controls**
- [Sudo Configuration and Security — Official Manual](https://www.sudo.ws/) — official sudo documentation; read the man pages for sudoers configuration syntax, NOPASSWD restrictions, and `Defaults` directives for secure setup.
- [sysctl hardening for kernel privesc mitigations (KSPP)](https://kernsec.org/wiki/index.php/Kernel_Self_Protection_Project/Recommended_Settings) — kernel parameters that close namespace-based and memory-based escalation paths; read the "Recommended settings" table.

**Auditing tools**
- [LinPEAS (Linux Privilege Escalation Awesome Script)](https://github.com/peass-ng/PEASS-ng/tree/master/linPEAS) — the attacker's audit tool; understanding what it looks for tells you exactly what to harden. Read the README and the check categories (not the script itself — the categories).

## Key concepts

- Six privesc categories: SUID/SGID misconfigurations, sudo misconfigurations, writable PATH, cron with world-writable scripts, kernel vulnerabilities, capability misconfigurations.
- GTFOBins is the defender's reference for which SUID binaries are dangerous.
- Defense-in-depth: remove SUID bit first; add AppArmor/MAC confinement as second layer.
- The privesc audit checklist should be automated in the compliance scan (module 07) so new misconfigurations alert immediately.
- Least privilege in sudo rules: specify exact commands, not `(ALL) NOPASSWD: ALL`.

## AI acceleration

Give an AI the output of `find / -perm -4000 2>/dev/null` from a system and ask it to flag which binaries have known GTFOBins techniques. Cross-check against [gtfobins.org](https://gtfobins.org/) directly — the model's training data may be out of date for recently-added entries. AI accelerates the cross-reference; GTFOBins is the authority.
