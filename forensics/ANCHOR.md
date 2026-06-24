# Forensics track — real-incident anchor & naming (internal author note)

This track is anchored to a **named, public real intrusion** the way the cloud track anchors to
the LastPass breach. The narrative reference is:

> **The DFIR Report — "From a Single Click: How Lunar Spider Enabled a Near Two-Month Intrusion"**
> (2025-09-29) — https://thedfirreport.com/2025/09/29/from-a-single-click-how-lunar-spider-enabled-a-near-two-month-intrusion/

Real chain from that case (use as the connective narrative across modules):
malicious JavaScript disguised as a tax form (`Form_W-9*.js`) → MSI → **Latrodectus** loader →
**Brute Ratel C4** + **Cobalt Strike** beacons → Zerologon (CVE-2020-1472) → domain-admin creds from
`unattend.xml` → lateral movement / RDP → **Rclone** exfiltration (renamed `sihosts.exe`) over ~2 months,
actor evicted before ransomware. Public IOCs (C2 e.g. `workspacin[.]cloud`, `cloudmeri[.]com`) are in
the report; full PCAP/EVTX are DFIR-Labs-gated, so labs use **other public datasets** for hands-on
artifacts and cite this case as the *story*.

## Canonical naming (apply consistently everywhere)

No invented brand. The org is referred to neutrally as "the affected organization" and the Lunar
Spider case is cited as the real parallel. Use these grounded names across every lab's `lab.md`,
scripts, and seed/fixture files:

| Entity | Canonical name |
|---|---|
| The org | "the affected organization" / drop the brand; cite the Lunar Spider case as the real parallel |
| Initially compromised workstation | `BEACHHEAD-WS01` |
| File server (where referenced) | `FILESHARE-SRV01` |
| Domain controller (where referenced) | `DC01` |
| Compromised user | `jsmith` |
| Service / backdoor account | `svc-backup` |
| C2 domain | `workspacin[.]cloud` (real Latrodectus C2 from the case) — defang in prose |
| Dropper chain | `Form_W-9.js` → `update.msi`; on-disk masquerade `svchost32.exe`; exfil tool `sihosts.exe` (renamed rclone) |
| Production deploy role / finance S3 bucket | `prod-deploy`, `corp-fin-reports` |
| YARA rule names | `latrodectus_loader` / `lunarspider_*` (family-grounded) |

Keep host/account names internally consistent across a lab's `lab.md`, scripts, and seed/fixture files.
