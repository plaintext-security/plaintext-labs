# Module 09 — Detecting AD Attacks

*Module concept · [Go to the hands-on lab →](lab.md)*


**Active Directory & Windows Security** — *every attack in modules 03-08 left a signal; this module is about turning those signals into detections that fire before the attacker reaches the DC.*

## Why this matters

Detection of AD attacks is hard because the techniques use legitimate protocols and many organisations lack the specific audit policy configuration required to see the events. A domain that hasn't enabled "Audit Kerberos Service Ticket Operations" will never see Event 4769 — the primary signal for Kerberoasting. A domain without "Audit Directory Service Access" will never see Event 4662 — the only direct signal for DCSync. The detection work is 50% audit policy and 50% Sigma logic; without the former, the latter never fires.

## Objective

Write Sigma rules for Kerberoasting (Event 4769), AS-REP roasting (Event 4768), DCSync (Event 4662), and pass-the-hash (Event 4624), validate them against sample EVTX data using `chainsaw`, and document the audit policy required to make each rule fire.

## The core idea

The fundamental challenge with AD attack detection is that the techniques blend into the background of legitimate Kerberos traffic. Thousands of Event 4769 records are generated every day in a healthy domain. The Kerberoasting signal is not "a 4769 was logged" — it is "a 4769 with encryption type RC4 (0x17) was logged for a service account from a source that has never requested a ticket for that SPN before." The signal is a combination of field value, rate, and behavioural baseline. A Sigma rule can capture the field value and a threshold; the behavioural baseline requires a SIEM with user-entity behavioural analytics (UEBA) or a tuned time-window correlation.

The practical approach for most environments: write tight Sigma rules that catch the high-fidelity indicators (etype 23 TGS for a service account from a workstation, replication rights exercised by a non-DC account) and accept some false positives from lower-fidelity indicators (every 4624 Type 3 from a new source host). The high-fidelity rules should alert immediately; the lower-fidelity rules should feed a hunting dashboard for weekly review. This tiering — alert vs. hunt — is how mature SOCs manage detection without drowning in noise.

The tooling for offline validation — testing a Sigma rule against real EVTX data — is the essential practice. `chainsaw` (a Rust tool from WithSecure) can ingest EVTX files and apply Sigma rules natively, giving you a direct answer to "would this rule have fired on the real attack data?" The EVTX files in `data/evtx/` contain real-shaped events for each attack from modules 03-08, allowing you to validate each rule before it ever touches a live SIEM. This is detection-as-code applied to AD-specific attacks.

A note on honeytokens: the most reliable detection for credential-based attacks is not an event you generate during the attack — it is a deliberate trap. A Kerberoastable service account that no legitimate service ever authenticates with (a honeytoken SPN) generates a 4769 that, by definition, must be attacker activity. No false positives, near-zero baseline noise. Similarly, a user account that is never used (a honey account) generates a 4769 or 4625 only when someone is probing. These are the highest-fidelity signals available, and they require zero complex logic — just the alert "any authentication to this account is malicious."

## Learn (~4 hrs)

**Windows event log fundamentals**
- [Windows Security Log Reference (Randy Franklin Smith / UltimateWindowsSecurity.com)](https://www.ultimatewindowssecurity.com/securitylog/encyclopedia/) — the encyclopaedic reference for every Windows security event ID. Bookmark this. Use it to understand what each field in Events 4624, 4769, 4662, 4768 means before writing a rule.
- [Audit policy best practices (Microsoft Docs)](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/security-best-practices/audit-policy-recommendations) — the authoritative guide on which audit categories to enable. Required reading before the lab.

**Chainsaw**
- [Chainsaw (GitHub — WithSecure)](https://github.com/WithSecureLabs/chainsaw) — the EVTX hunting tool. Read the `--sigma` flag usage. `chainsaw hunt evtx/ -s rules/ --mapping mappings/sigma-event-logs-all.yml` is the core command pattern.

**Sigma for AD attacks**
- [SigmaHQ — Windows rules (GitHub)](https://github.com/SigmaHQ/sigma/tree/master/rules/windows) — the reference library of published Sigma rules. Look at `rules/windows/builtin/security/` for 4769/4768/4662/4624 rules. Read existing rules before writing your own.
- [T1558.003 detection (ATT&CK)](https://attack.mitre.org/techniques/T1558/003/) — read the detection section; it specifies exactly which field values are anomalous.

**Honeytokens**

## Key concepts
- Detection requires the right audit policy first — without it, the event never appears.
- Kerberoasting signal: Event 4769, TicketEncryptionType = 0x17 (RC4), for a service account from a user workstation.
- AS-REP roasting signal: Event 4768 with PreAuthType = 0 from an unexpected source.
- DCSync signal: Event 4662 with ObjectType = DS-Replication-Get-Changes-All from a non-DC account.
- PTH signal: Event 4624 Logon Type 3 with authentication package NtLmSsp from an unexpected source.
- Honeytoken approach: any Event 4769 for a never-used SPN = guaranteed attacker activity.
- Chainsaw validates Sigma rules against EVTX offline — the detection-as-code test harness.

## AI acceleration

Ask a model to draft all four Sigma rules (4769 Kerberoast, 4768 AS-REP, 4662 DCSync, 4624 PTH) from descriptions of the attack. The model is good at the YAML structure but will frequently get field names wrong (e.g., `TicketOptions` vs `TicketEncryptionType`, or confuse event IDs). Validate each field name against the ultimatewindowssecurity.com event reference before running the rule through chainsaw.
