# Module 04 — Windows Artifacts

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *Windows leaves a detailed record of everything that ran — if you know where to look.*

## Why this matters
Windows is the dominant enterprise endpoint, and it is extraordinarily artifact-rich. Every program that runs leaves traces across event logs, the registry, prefetch files, the shellbag, and the timeline. An attacker who compromises a Windows host is operating in a recording studio: they may wipe the most obvious logs, but they can rarely erase all traces across all artifact sources simultaneously. The forensic investigator who knows all the sources — and which ones survive each anti-forensics technique — has a decisive advantage. This module maps the terrain.

## Objective
Parse Windows Security event logs with `chainsaw` to surface authentication and execution events; extract key forensic data from a registry hive with Python's `python-registry`; and explain which artifacts survive common anti-forensics techniques like log clearing and prefetch deletion.

## The core idea
Windows is designed for accountability — it was built for enterprise environments that need audit trails, and that design decision benefits the forensic investigator far more than it inconveniences the attacker. The registry is a structured database, not a log file: it's always-on, always-consistent, and resistant to partial corruption. The event log system (EVTX) is a structured binary format with embedded checksums and forward-recovery from incomplete writes. Prefetch is a performance optimization that happens to record the first 8 seconds of a program's I/O — which is exactly what an investigator needs to prove execution. These weren't designed to help investigators, but they do.

**The most important Windows forensic principle** is that artifacts cross-corroborate each other, and that an attacker who clears one source usually leaves the clearing event itself in another source. A `wevtutil cl Security` command to clear event logs creates Event ID 1102 (log cleared) in the Security log — you can't clear the log without recording that you cleared it. Wiping prefetch requires either deleting the files (which leaves filesystem artifacts about the deletion) or using a specialized tool (which itself leaves an execution trace). The investigator's job is to build a case that doesn't rest on any single artifact source, so that knocking out one source doesn't knock out the investigation.

**Event logs (EVTX)** are the most commonly examined Windows artifact. The Security log is the richest: Event IDs 4624/4625 (logon success/failure), 4688 (process creation — gold for execution analysis), 4768/4769 (Kerberos ticket activity), 4720–4726 (account management), and 1102 (log cleared). The System and Application logs add hardware, service, and application events. `chainsaw` is a Rust-powered tool that parses EVTX files directly (no Windows needed), applies Sigma rules to surface suspicious events, and supports custom field queries. It is the forensic analyst's first pass over a log archive before hunting manually.

**The registry** is a hierarchical key-value store that encodes almost everything about a Windows system's configuration and user activity. The forensically important hives are `SYSTEM` (boot configuration, device history, network interfaces), `SOFTWARE` (installed applications, run keys), `SECURITY` (policy, cached credentials), and per-user `NTUSER.DAT` (MRU lists, typed paths, shellbags, run keys, autorun persistence). Registry timestamps only record the *last write time* of a key — not creation or access — which limits timestamp analysis but is still useful for placing activity in time. `python-registry` reads raw hive files without needing a Windows OS, making it suitable for offline forensic analysis.

**Persistence and execution artifacts** deserve special attention because they answer the investigator's core question: "what ran, and how did it get there?" Persistence lives predominantly in run keys (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`, scheduled tasks in `SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache`), services (`SYSTEM\CurrentControlSet\Services`), and startup folders. Execution evidence comes from prefetch (`C:\Windows\Prefetch\MALWARE.EXE-XXXXXXXX.pf` — proves the file ran, when, and how many times), the Shimcache (`SYSTEM` hive, AppCompatCache key — records executable metadata even if prefetch is disabled), and Amcache (`C:\Windows\appcompat\Programs\Amcache.hve` — SHA1 hash of the binary, proving the specific file that ran). These sources survive each other's deletion in different ways, which is why experienced investigators check all of them.

## Learn (~4 hrs)

**Event logs (~1.5 hrs)**
- [chainsaw — GitHub README and usage guide](https://github.com/WithSecureLabs/chainsaw) — read "Hunt Mode" and the Sigma rule integration; this is the tool you'll use in the lab.
- [Windows Security Event Log Reference (Microsoft)](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/security-auditing-overview) — the canonical reference for Security event IDs. Focus on 4624, 4625, 4688, 4768, and 1102.
- [EVTX-ATTACK-SAMPLES (sbousseaden)](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) — a curated repo of real attack-shaped EVTX files organized by ATT&CK technique; the lab bundles a small slice of these.

**Registry forensics (~1.5 hrs)**
- [python-registry — GitHub](https://github.com/williballenthin/python-registry) — the library's README and examples; understand the `Registry`, `RegistryKey`, and `RegistryValue` classes.
- [Windows Registry Forensics — Eric Zimmerman's tool docs](https://ericzimmerman.github.io/#!index.md) — the "Registry Explorer / RECmd" section explains the forensically important keys; focus on NTUSER.DAT MRU lists and run keys.
- [SANS FOR508 Registry Cheat Sheet](https://www.sans.org/posters/windows-forensic-analysis/) — one-page reference of the most forensically relevant keys; keep it open during the lab.

**Execution artifacts (~1 hr)**
- [Amcache and Shimcache — SANS](https://www.sans.org/white-papers/38630/) — white paper on the two execution history artifacts that survive prefetch deletion; understand what each records (file hash vs. metadata).

## Key concepts
- EVTX is a structured binary format; `chainsaw` parses it without Windows and applies Sigma rules.
- Key Security event IDs: 4624 (logon), 4625 (failed logon), 4688 (process creation), 4768/4769 (Kerberos), 1102 (log cleared).
- Registry timestamps record last *write* time only; forensically important hives include `NTUSER.DAT`, `SYSTEM`, `SOFTWARE`.
- Persistence: run keys, scheduled tasks, services, startup folders.
- Execution artifacts: prefetch (ran, when, how many times), Shimcache (metadata even without prefetch), Amcache (SHA1 of binary).
- Artifacts cross-corroborate: clearing one source usually leaves evidence in another.
- Anti-forensics moves (log clearing, prefetch deletion) are themselves recorded somewhere else.

## AI acceleration
AI excels at explaining unfamiliar Event IDs ("what does Event 4769 with failure code 0x12 mean?") and drafting registry parsing scripts from a description of the key structure. Where it falls short: it cannot read your EVTX or hive files, and it will invent specific event details. Use it to draft the parsing logic and to interpret output you've already collected — then verify every finding against the raw event data.
