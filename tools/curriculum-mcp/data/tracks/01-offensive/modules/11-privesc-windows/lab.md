# Lab 11 — Escalate to SYSTEM on Windows

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

**Windows VM required.** This lab needs a Windows host; Docker won't work here.

**Option A — Windows eval VM (local):**
1. Download the [Windows Server eval ISO](https://www.microsoft.com/en-us/evalcenter/)
   (180-day free trial, no license key).
2. Create a VM in VirtualBox or VMware. Snapshot the clean state before planting misconfigs.
3. Run the lab seeder (as Administrator in PowerShell):
   ```powershell
   git clone https://github.com/plaintext-security/plaintext-labs.git
   cd plaintext-labs\offensive\11-privesc-windows
   Set-ExecutionPolicy -Scope Process Bypass
   .\plant-misconfigs.ps1
   ```
4. Create a standard (non-admin) user: `net user labuser P@ssw0rd123 /add`

**Option B — Triage-only demo (no Windows needed):**
The triage tool runs on macOS/Linux against a sample winPEAS output:
```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/11-privesc-windows
make demo
```

## Scenario

You've obtained a low-privilege shell as `labuser` on Meridian Financial's
application server. Enumerate the host with winPEAS, triage the findings, and
exploit the highest-confidence vector to reach SYSTEM.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] On the Windows VM, run winPEAS as `labuser` (standard user) and save its output, then run
   `triage.py` over that output on your analysis machine. (winPEAS ships a single self-contained
   `.exe` in the PEASS-ng releases; pipe its output to a file to capture it.) Note which vectors
   the tool ranks P0 (reliable) vs P3 (informational).

2. [ ] From the triage output, confirm the planted vectors and identify which are P0:
   - `AlwaysInstallElevated` registry keys
   - the unquoted service path (`MeridianUpdater`)
   - a weak service-binary ACL

3. [ ] Exploit **AlwaysInstallElevated** (P0 — most reliable) to get a SYSTEM shell. (What does this
   misconfig let any user do with an `.msi`? Which msfvenom payload/format produces one, and how do
   you trigger an install that runs as SYSTEM?) Confirm with `whoami`.

4. [ ] Exploit the **unquoted service path** (P1):
   - What path would Windows search before finding the real service binary?
   - Create a stub at that path and restart the service.
   - What privilege does the service run as?

5. [ ] State the fix for each vector (see `triage.py` output for hints).

## Success criteria — you're done when

- [ ] You ran `triage.py` on real winPEAS output from the planted-misconfig VM.
- [ ] You escalated to SYSTEM via at least one P0 vector.
- [ ] You can explain the unquoted service path mechanism — why Windows searches multiple paths.
- [ ] You can state the remediation for all three planted misconfigs.

## Deliverables

`windows-privesc.md`: the three vectors (finding, exploit command, proof-of-SYSTEM output),
a comparison of P0 vs P1 reliability, and the fix for each.

## Automate & own it

**Required.** Extend `triage.py` to:
- Accept a winPEAS output file
- Add rules for at least two additional vectors (token privileges, writable PATH)
- Output a ranked report with an "exploit confidence" score per vector

AI drafts the additional regex rules; you validate each against real winPEAS output.
Commit the extended `triage.py` and `windows-privesc.md`.

## AI acceleration

Paste your `winPEAS` output (or a section of it) to a model and ask it to explain
the top-priority vector and the exact exploit preconditions. Then verify those
preconditions on the target before acting — models confidently miss a detail that
makes the exploit fail or crash the service.

## Connects forward

SYSTEM on a Windows host is the launchpad for Track 06 (Active Directory) — credential
dumping with Mimikatz, Pass-the-Hash, and Kerberoasting all start from a SYSTEM or
admin context. Module 12 (pivoting) shows how to use that access to reach adjacent hosts.

## Marketable proof

> "I enumerate and escalate privilege on Windows — AlwaysInstallElevated, unquoted
> service paths, and weak binary ACLs via winPEAS — and I can map each finding to the
> LOLBAS/registry fix."

## Stretch

- Research **PrintNightmare (CVE-2021-34527)**: how did it reach SYSTEM, and what
  Windows patch closed it?
- Run `accesschk.exe -uwcqv "labuser" *` and compare service ACL output to winPEAS
  findings. Which tool surfaces more service vectors?
