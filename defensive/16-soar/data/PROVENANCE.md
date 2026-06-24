# Data provenance — Module 16, Build a Response Playbook (Track Capstone)

## What ships in this repo (the seed)

`alerts.json` (3 incoming alerts) and `intel.json` (IP verdicts) are a **curated
synthetic alert queue** so the SOAR pipeline runs fully offline and deterministically
with `make demo`. Hosts (`WS-JSMITH`), users (`jsmith@corp.local`), and RFC 1918
internal IPs are neutral placeholders — this is a teaching scenario, not a capture of
a real org. The three alerts are chosen to exercise the three routing outcomes:
a true positive (C2 + macro chain), a false positive (benign browser download), and a
brute-force success (lateral-movement amplifier).

## The real artifacts it is anchored to

The pipeline's enrichment and scoring map onto real intel sources and ATT&CK
technique, so the playbook transfers to a production SOAR:

- **`intel.json` verdicts use real feed schemas and families:**
  - `185.220.101.47` → "Cobalt Strike C2", source **abuse.ch ThreatFox**
    (malware family `win.cobalt_strike`). ThreatFox publishes live Cobalt Strike C2
    IOCs: https://threatfox.abuse.ch/ — recent CSV
    https://threatfox.abuse.ch/export/csv/recent/ — API
    `https://threatfox-api.abuse.ch/api/v1/` (docs https://threatfox.abuse.ch/api/).
  - `45.155.204.42` → "SSH brute-force scanner", source **AbuseIPDB**, the real
    crowd-sourced IP-abuse database: https://www.abuseipdb.com/
    (API docs: https://docs.abuseipdb.com/).
  - The example IOC values are illustrative placeholders — the lab's enrichment step
    is meant to be re-pointed at the **live** ThreatFox feed (module 15's
    `make fetch-data`), which is exactly what the YAML playbook's `enrich` step calls.
- **ATT&CK mapping:** the alerts model T1566.001 (macro phishing) → T1059.001
  (encoded PowerShell) → C2, and T1110 Brute Force
  (https://attack.mitre.org/techniques/T1110/) with a successful logon.
- **Workflow-as-code targets are real tools:** the `--export` YAML imports into
  **Shuffle** (https://github.com/Shuffle/Shuffle) or **Tines**
  (https://www.tines.com/), opens a case in **TheHive**
  (https://github.com/TheHive-Project/TheHive), and the live `enrich` step calls the
  ThreatFox API above. The optional LLM triage step uses the **Ollama API**
  (https://github.com/ollama/ollama/blob/main/docs/api.md).

## Use real intel (deferred — you run it locally)

No `make fetch-data` here (the alert queue is a fixed teaching scenario), but the
intended progression wires the playbook's `enrich` step to the live ThreatFox API
above and sends the human-gate approval to a real Slack webhook (the lab's
Automate & own it step).

## One-line citation

> Synthetic SOAR alert queue anchored to abuse.ch ThreatFox
> (https://threatfox.abuse.ch/), AbuseIPDB (https://www.abuseipdb.com/), MITRE
> ATT&CK (T1566.001/T1059.001/T1110), and workflow-as-code for Shuffle/Tines +
> TheHive.
