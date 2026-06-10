# Module 11 — Privilege Escalation: Windows

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *from a user shell to SYSTEM, usually via misconfiguration.*

## Why this matters
On Windows, the path from a normal user to SYSTEM runs through service misconfigurations,
excessive privileges, and unpatched kernels — and it's the step that turns a phishing
foothold into domain compromise. The same misconfigurations you abuse here are what Track 07
hardens and Track 06 chains into Active Directory attacks.

## Objective
Enumerate a Windows host for privilege-escalation vectors and exploit one to reach SYSTEM in
your lab.

## The core idea
Same goal as the Linux module — low-privilege user → SYSTEM — and the same root cause, misconfiguration,
but Windows has its own idioms worth knowing, because this is the step that turns a phishing foothold
into domain compromise. The vectors cluster differently: **service misconfigurations** (an unquoted
service path, or a service whose binary or ACL you can overwrite, running as SYSTEM), **excessive token
privileges** (the `SeImpersonate` right the "potato" attacks abuse to become SYSTEM), unpatched kernels,
and scheduled-task or registry abuse. The method is identical to Linux — enumerate the misconfigurations
first (`winPEAS`/`PrivescCheck`), exploit second — only the catalog of where admins slip is different.

The bridge worth drawing: **Windows privesc runs straight into Active Directory.** The same token,
service, and privilege misconfigurations you abuse on one host are what the AD track chains across a
domain, and what the endpoint-hardening track locks down. Local SYSTEM is rarely the goal on Windows —
it's the springboard to the domain, which is why this module matters beyond the single box.

The judgment: Windows privesc is a minefield of **preconditions** — a specific service ACL, a token
right, a patch level — that decide whether a vector actually works, and a model can't see them on your
target. It will explain a vector cleanly and then confidently propose one whose preconditions your box
doesn't meet, wasting your time or alerting the defender. Confirm each precondition yourself before
exploiting.

## Learn (~4 hrs)

**The vectors**
- [LOLBAS Project](https://lolbas-project.github.io/) — the catalog of trusted Windows binaries abused to escalate and evade; the Windows counterpart to GTFOBins.
- [Windows Privilege Escalation for Beginners (video)](https://www.youtube.com/watch?v=uTcrbNBcoxQ) — a hands-on tour of the common vectors.

**Where it sits**
- [MITRE ATT&CK — Privilege Escalation (TA0004)](https://attack.mitre.org/tactics/TA0004/) — the tactic, mapped to Windows techniques.

## Key concepts
- Enumeration (what `winPEAS`/`PrivescCheck` automate)
- Service misconfigurations: unquoted paths, weak permissions
- Excessive token privileges (SeImpersonate and "potato" attacks)
- Unpatched kernel vulnerabilities
- Registry and scheduled-task abuse

## AI acceleration
A model reads `winPEAS` output and explains a vector quickly — but Windows privesc is full of
preconditions (service ACLs, token rights, patch level) the model can't see on your target.
Confirm each precondition yourself before exploiting.
