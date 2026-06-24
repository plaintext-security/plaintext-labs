# Provenance — Lab 04 Windows Artifacts data

## Primary dataset: EVTX-ATTACK-SAMPLES (real)

- **Dataset:** EVTX-ATTACK-SAMPLES — ~200 real Windows `.evtx` event logs mapped to MITRE ATT&CK,
  organized by tactic directory.
- **Author / source:** sbousseaden, https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- **License / status:** public repository of research/detection samples (GPL-3.0). Freely
  fetchable; intended for detection engineering and DFIR training.
- **How it is used here:** these real `.evtx` files are the **primary artifact** for the lab,
  replacing the synthetic `data/security-events.jsonl` seed (which is retained only as an offline
  fallback for `make demo`). `make fetch-data` downloads them into `data/`.

### Files wired (mapped to the lab's three questions)

| Question | File | Raw URL |
|---|---|---|
| Who authenticated (4624) | `LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Lateral%20Movement/LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx |
| What ran (process creation / Sysmon EID 1) | `revshell_cmd_svchost_sysmon_1.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Execution/revshell_cmd_svchost_sysmon_1.evtx |
| Log cleared (EID 1102) | `DE_1102_security_log_cleared.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Defense%20Evasion/DE_1102_security_log_cleared.evtx |

### SHA-256 (fill after fetch)

Run `sha256sum data/*.evtx` after `make fetch-data` and record here to pin the artifacts:

```
<fill after fetch>  LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx
<fill after fetch>  revshell_cmd_svchost_sysmon_1.evtx
<fill after fetch>  DE_1102_security_log_cleared.evtx
```

> Fetch and SHA-256 validation are **deferred to runner-validation** — the download has not been
> executed in authoring.

## Synthetic fallback (retained)

- `data/security-events.jsonl` — pre-shaped Security events; offline fallback so `make demo` runs
  before `fetch-data`. Modelled on the Lunar Spider intrusion (see `../ANCHOR.md`); neutral host
  `BEACHHEAD-WS01.corp.internal`, account `svc-backup`.
- `data/ntuser-parsed.json` — small synthetic `NTUSER.DAT` representation (persistence + MRU).
