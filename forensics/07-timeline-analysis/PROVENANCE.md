# Provenance — Lab 07 Timeline Analysis data

## Real reference case: DFIR Report "Lunar Spider"

- **Case (narrative anchor):** The DFIR Report — "From a Single Click: How Lunar Spider Enabled a
  Near Two-Month Intrusion" (2025-09-29).
  https://thedfirreport.com/2025/09/29/from-a-single-click-how-lunar-spider-enabled-a-near-two-month-intrusion/
- **How it is used here:** the bundled `data/timeline.csv` (25 events) and
  `data/artifacts/security-events.jsonl` are **modelled on that case's event sequence** (malicious
  JS → loader → C2 beacons → credential theft → lateral movement → file access on the share →
  log clear) with neutral naming. They are *derived-from / modelled-on* the real case — not a verbatim
  export (the case's full PCAP/EVTX are DFIR-Labs-gated). See `../ANCHOR.md` for the naming map.

### Neutral naming applied (replaced the prior synthetic brand)

| Real-case role | Neutral token used |
|---|---|
| Initially compromised workstation | `BEACHHEAD-WS01` (`.corp.internal`) |
| File share server | `FILESHARE-SRV01` |
| Compromised user | `jsmith` (domain `CORP`) |

## Real artifact to timeline yourself: EVTX-ATTACK-SAMPLES

- **Dataset:** EVTX-ATTACK-SAMPLES — ~200 real Windows `.evtx` event logs mapped to MITRE ATT&CK.
- **Author / source:** sbousseaden, https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- **License / status:** public repository of research/detection samples (GPL-3.0), freely fetchable.
- **How it is used here:** `make fetch-data` downloads a real execution-chain `.evtx` into
  `data/artifacts/` so the learner can run `log2timeline.py` / `psort.py` over a **genuine** event
  log rather than only the shaped JSON seed. It complements the bundled artifacts; it does not
  replace them.

### File wired

| Purpose | File | Raw URL |
|---|---|---|
| Real execution chain (cmd/svchost reverse shell, Sysmon EID 1) | `revshell_cmd_svchost_sysmon_1.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Execution/revshell_cmd_svchost_sysmon_1.evtx |

### SHA-256 (fill after fetch)

Run `sha256sum data/artifacts/revshell_cmd_svchost_sysmon_1.evtx` after `make fetch-data` and record
here to pin the artifact:

```
<fill after fetch>  revshell_cmd_svchost_sysmon_1.evtx
```

> Fetch and SHA-256 validation are **deferred to runner-validation** — the download has not been
> executed in authoring.

## Bundled seed (retained)

- `data/timeline.csv` — 25-event pre-computed plaso-style timeline modelled on the Lunar Spider case
  (window 2024-03-15 02:00–02:35 UTC), neutral naming. Replaces the prior synthetic seed.
- `data/artifacts/security-events.jsonl`, `data/artifacts/prefetch.json` — shaped artifacts for
  plaso ingestion, same neutral naming.
