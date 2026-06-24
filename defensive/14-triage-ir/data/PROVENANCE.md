# Data provenance — Module 14, Run an Incident

## What ships in this repo (the seed)

`incident_pack.json` is a **curated synthetic incident pack** for
INC-2024-0315-001 — a Cobalt Strike macro-phishing compromise. It is a *teaching
walkthrough*, not a raw capture: hosts (`WS-JSMITH`, `SRV-01`), users
(`jsmith@corp.local`), and RFC 1918 internal IPs are neutral placeholders, so the
lab runs fully offline with `make demo` and never references a real victim org. The
pack exists because IR practice needs a *complete, structured* incident — alert,
observables, timeline, enrichment, per-phase questions — which no single public
capture hands you ready-made.

## The real artifacts it is anchored to

Every malicious element in the pack maps to a real, citable artifact so the triage
reasoning transfers to the job:

- **Kill chain — Cobalt Strike via Office macro → encoded PowerShell → `certutil`
  LOLBin → scheduled-task + Run-key persistence.** This is a real-world commodity
  intrusion pattern, mapped to MITRE ATT&CK:
  - T1566.001 Phishing: Spearphishing Attachment — https://attack.mitre.org/techniques/T1566/001/
  - T1059.001 PowerShell — https://attack.mitre.org/techniques/T1059/001/
  - T1105 Ingress Tool Transfer (`certutil`) — https://attack.mitre.org/techniques/T1105/
  - T1053.005 Scheduled Task — https://attack.mitre.org/techniques/T1053/005/
  - T1547.001 Registry Run Keys — https://attack.mitre.org/techniques/T1547/001/
- **Threat-intel verdict.** The C2 `ip:port` verdict ("Cobalt Strike C2",
  confidence 90, source ThreatFox) uses the real abuse.ch ThreatFox malware family
  `win.cobalt_strike` and the real ThreatFox `ip:port` IOC type and confidence
  scale (50–100). ThreatFox publishes live Cobalt Strike C2 IOCs daily:
  - ThreatFox: https://threatfox.abuse.ch/
  - Live recent-IOC CSV: https://threatfox.abuse.ch/export/csv/recent/
  - API (search a single IOC): `https://threatfox-api.abuse.ch/api/v1/`
    (POST `{"query":"search_ioc","search_term":"<ioc>"}`). Docs:
    https://threatfox.abuse.ch/api/
  - MalwareBazaar (the payload-hash verdict): https://bazaar.abuse.ch/
- **The example IOCs (`185.220.101.47`, the payload hash) are illustrative
  placeholders, not attributed live indicators** — to enrich against *real* current
  Cobalt Strike infrastructure, query ThreatFox for `malware:win.cobalt_strike` and
  swap a live `ip:port` into the pack.

## Use real intel (deferred — you run it locally)

This lab has no `make fetch-data` (the pack is a fixed teaching scenario), but the
intended progression is to enrich the pack's C2 indicator against the **live**
ThreatFox feed from module 15's `make fetch-data`, and to push the pack to a real
TheHive instance via its API (the lab's Automate & own it step).

## One-line citation

> Synthetic IR walkthrough anchored to MITRE ATT&CK (T1566.001, T1059.001, T1105,
> T1053.005, T1547.001) and abuse.ch ThreatFox (`win.cobalt_strike` C2 intel,
> https://threatfox.abuse.ch/) / MalwareBazaar (https://bazaar.abuse.ch/).
