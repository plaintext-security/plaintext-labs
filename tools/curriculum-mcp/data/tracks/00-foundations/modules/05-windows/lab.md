# Lab 05 — Inspect a Windows System (and Find a Real Attack in the Logs)

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/05-windows
make demo   # parse bundled EVTX-shaped sample + print PowerShell guide
```

No Docker required — the log analysis runs on macOS/Linux/Windows with Python 3.

For the live Windows steps (local admins, services, Run keys), you need:
- A Windows machine you own — a free
  [Windows evaluation VM](https://developer.microsoft.com/windows/downloads/virtual-machines/)
  in your lab (module 02) is ideal; snapshot it first.
- [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) — real Windows
  event logs (`.evtx`) captured during actual attack techniques.

## Scenario
Profile a Windows host the way a defender would — then find a real attacker's activity in a
genuine event-log sample.

> Use only a VM or machine you own. The sample EVTX is safe to open — it's a log, not malware.

## Do
1. [ ] On your own Windows VM, enumerate local users and groups and identify which have
   administrative rights. (PowerShell has cmdlets for this — find them.)
2. [ ] List running processes and services, and spot anything set to start automatically.
3. [ ] Load a **real** event log: open an `.evtx` from
   [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) in Event Viewer
   (or query it with PowerShell's `Get-WinEvent`) and find the logon events — then pick out a
   suspicious one. (What Event ID is a successful logon? Which logon *type* is a remote one?)
4. [ ] Inspect a registry "Run" key — a classic persistence location, MITRE ATT&CK
   [T1547.001](https://attack.mitre.org/techniques/T1547/001/) — and explain what it controls.

## Success criteria — you're done when
- [ ] You can list local admins and auto-start services from the command line.
- [ ] You found logon events in a **real** sample EVTX and can name the key Event IDs (and
  what a remote logon type looks like).
- [ ] You can explain how a Run key (T1547.001) gives an attacker persistence.

## Deliverables
`windows-recon.md`: the admin accounts and auto-start items from your VM, the logon event(s)
you flagged in the real EVTX sample (with Event IDs), and the persistence implication of the
Run key.

## AI acceleration
Ask a model for the PowerShell to enumerate admins or query logon events — then verify each
cmdlet does only what you expect before running it as administrator.

## Connects forward
This is the Windows literacy Track 06 (Active Directory), Track 07 (endpoint hardening), and
Track 03 (forensics) assume — and reading a real EVTX previews Track 02 detection.

## Marketable proof
> "I can profile a Windows host and find an attacker's logon and persistence in a real
> event-log sample — not just Linux."

## Automate & own it
**Required.** Write a PowerShell script that collects the local admins, auto-start services, and
recent logon events into a single report (AI-assisted, reviewed before you run it as admin); commit it.

## Stretch
- Map the suspicious activity you found to its MITRE ATT&CK technique, and note which Event
  ID(s) would detect it.
