# Track 02 — Defensive Operations

**Find attackers in the noise and respond before they reach their goal.** Detection
engineering, SIEM, log analysis, hunting, and incident response — treated as code:
telemetry in, tested detections out, mapped to attacker behaviour.

## What you'll be able to do
- Build a telemetry pipeline from host, network, and cloud into a searchable store.
- Write, test, and version detections mapped to MITRE ATT&CK.
- Hunt proactively across endpoint and network data.
- Triage and drive an incident from alert to root cause.

## Modules

| # | Module | What you'll learn | OSS tools |
|---|--------|-------------------|-----------|
| 01 | [Telemetry & Log Centralisation](modules/01-telemetry/README.md) | What to collect and how to ship it | `elastic`, `fluent-bit`, `vector` |
| 02 | [Windows & Endpoint Telemetry](modules/02-endpoint-telemetry/README.md) | Process/file/auth events worth alerting on | `sysmon`, `wazuh` |
| 03 | [Linux Telemetry](modules/03-linux-telemetry/README.md) | Auditd and kernel-level visibility | `auditd`, `osquery` |
| 04 | [Network Security Monitoring](modules/04-network-monitoring/README.md) | Protocol logs and connection records | `zeek`, `arkime` |
| 05 | [Intrusion Detection](modules/05-intrusion-detection/README.md) | Signature and anomaly detection on the wire | `suricata` |
| 06 | [SIEM Fundamentals](modules/06-siem/README.md) | Indexing, querying, and dashboards | `elastic`/`kibana`, `wazuh` |
| 07 | [Log Parsing & Normalisation](modules/07-log-parsing/README.md) | Turning raw logs into a common schema | `vector`, `logstash` |
| 08 | [Detection-as-Code](modules/08-detection-as-code/README.md) | Writing portable rules in Sigma | `sigma` |
| 09 | [Detection Testing & Tuning](modules/09-detection-testing/README.md) | Validating coverage, cutting false positives | Atomic Red Team |
| 10 | [ATT&CK Mapping & Coverage](modules/10-attack-coverage/README.md) | Measuring and closing detection gaps | ATT&CK Navigator |
| 11 | [Threat Hunting — Endpoint](modules/11-hunting-endpoint/README.md) | Hypothesis-driven host hunting | `osquery`, `velociraptor` |
| 12 | [Threat Hunting — Network](modules/12-hunting-network/README.md) | Hunting across protocol and flow data | `zeek`, `jupyter` |
| 13 | [PowerShell Logging & Hunting](modules/13-powershell-logging-hunting/README.md) | Script-block/module logging and hunting PowerShell abuse | `pwsh`, `chainsaw`, `sigma` |
| 14 | [Alert Triage & Incident Response](modules/14-triage-ir/README.md) | A repeatable process from alert to verdict | `TheHive` |
| 15 | [Threat Intelligence](modules/15-threat-intel/README.md) | Managing IOCs and enriching detections | `MISP`, `OpenCTI` |
| 16 | [Response Automation (SOAR primer)](modules/16-soar/README.md) | Automating enrich → contain → ticket | `Shuffle` |

## Phases & projects

The sixteen modules run in three phases; each ends in a **project** that integrates its modules.

- **Phase 1 · Get the data** (01–07) — **Project:** a working telemetry pipeline that ingests host
  *and* network data into a searchable SIEM, with a real attack dataset flowing through it.
- **Phase 2 · Find the attacker** (08–13) — **Project:** a set of detections-as-code mapped to MITRE
  ATT&CK, tested against a real attack dataset, plus one documented threat hunt.
- **Phase 3 · Respond** (14–16) — **Project:** an incident handled from alert to root cause, with an
  automated enrich → contain → ticket step (the track capstone).

> **Standalone by design.** Every detection lab here sources a **real public dataset** (and a
> generate-it-here option), so you can complete this track without having done Offensive. If you
> *did* do Track 01, bring your own attack artifacts instead — same skill.

## Prerequisites
Complete Track 00 — Foundations first.

> Labs use open-source tooling and free sample datasets (Malware-Traffic-Analysis.net,
> public PCAPs, EVTX-ATTACK-SAMPLES). Only analyse data you're authorised to handle.

## Capstone
Stand up a telemetry pipeline, simulate an attack (Atomic Red Team or a replayed PCAP),
and catch it: ship the logs, write the detection-as-code mapped to ATT&CK, and produce an
incident write-up from alert to root cause. **Deliverable:** the tested detections plus the
investigation.

## AI & automation
A small local model triages and classifies log lines cheaply at volume; a frontier model
drafts an incident narrative or a Sigma rule. The skill is review: a generated detection
with broken logic ships false confidence, and automation that buries a real signal is
worse than none. AI authors the rule — you map it to ATT&CK, test it, and own the alert.

## Standards & further reading
- MITRE ATT&CK and the ATT&CK Navigator
- Sigma rule specification
- NIST SP 800-61 (Incident Handling Guide)
- The Pyramid of Pain
