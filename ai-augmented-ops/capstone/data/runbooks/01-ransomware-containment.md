# Runbook — Ransomware: early containment

**Class:** Impact / encryption-for-impact (MITRE ATT&CK T1486). **Severity:** Critical.

## Recognising it
High-confidence early indicators, in order of how fast they demand action:
- `vssadmin.exe Delete Shadows /All /Quiet` or `wmic shadowcopy delete` — the attacker is
  destroying Volume Shadow Copies so you cannot roll back. ATT&CK T1490 (Inhibit System Recovery).
- A burst of file renames to a new extension (e.g. hundreds of files gaining `.locked` within
  seconds) and a ransom note (`RESTORE_FILES.txt`) appearing in each directory.
- Real-time AV/EDR protection disabled on the host immediately before the above.

## Immediate actions
1. **Isolate the host** from the network (EDR network-contain or pull the link) — do not power it
   off if you want memory for forensics; isolation stops lateral spread without losing volatile state.
2. **Identify the source/patient-zero** and any hosts that received lateral-movement traffic
   (PsExec service installs — Windows Event ID 7045 for `PSEXESVC` — are a common spread vector).
3. **Preserve** the ransom note, a sample encrypted file, and the process tree before remediation.
4. **Do not** auto-restore or auto-wipe without a human decision — recovery is irreversible and a
   miscall is costly.

## Notes for an automated/AI playbook
A ransomware signal is a *high-confidence, high-impact* case where auto-isolation is defensible.
But "delete the host / restore from backup" must route to a human: the cost of an automated wrong
move on an irreversible action is the lesson of every runaway-automation failure
(cf. Knight Capital, 2012 — dormant code took irreversible actions at machine speed with no
kill-switch and lost ~$440M in 45 minutes).
