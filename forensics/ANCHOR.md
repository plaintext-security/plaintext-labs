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

## De-Meridian naming map (apply consistently everywhere)

| Old (invented "Meridian") | New (neutral, grounded) |
|---|---|
| "Meridian Financial", "Meridian" (the org) | "the affected organization" / drop the brand; cite the Lunar Spider case as the real parallel |
| `MERIDIAN-FIN-WS01`, `WORKSTATION-04`, `MERIDIAN-WS04` | `BEACHHEAD-WS01` (the initially compromised workstation) |
| `MERIDIAN-FS01`, `meridian-fs01` | `FILESHARE-SRV01` |
| (domain controller, where referenced) | `DC01` |
| `dev-svc01` | `jsmith` (compromised user) |
| `svc_batch_finance` | `svc-backup` (service account) |
| `update-cdn82.net` (C2) | `workspacin[.]cloud` (real Latrodectus C2 from the case) — defang in prose |
| `svchost32.exe`, `MeridianDropper` | dropper chain `Form_W-9.js` → `update.msi`; exfil tool `sihosts.exe` (renamed rclone) |
| `MeridianProdDeploy`, `meridian-fin-reports` (S3) | `prod-deploy`, `corp-fin-reports` (neutral) |
| YARA rule names `meridian*` | `latrodectus_loader` / `lunarspider_*` (family-grounded) |

Keep host/account names internally consistent across a lab's lab.md, scripts, and seed/fixture files.
