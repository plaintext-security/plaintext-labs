# Provenance — Lab 10 Log & Cloud Forensics data

## Windows half — EVTX-ATTACK-SAMPLES (real)

- **Dataset:** EVTX-ATTACK-SAMPLES — ~200 real Windows `.evtx` event logs mapped to MITRE ATT&CK.
- **Author / source:** sbousseaden, https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- **License / status:** public repository of research/detection samples (GPL-3.0), freely fetchable.
- **How it is used here:** these real `.evtx` are the **primary artifact** for the Windows half of
  the lab (hayabusa / chainsaw triage), replacing the synthetic `data/evtx_triage_summary.txt` and
  `data/chainsaw_summary.txt` seeds (retained only as an offline fallback for `make demo`).
  `make fetch-data` downloads them into `data/evtx/`.

### Files wired

| Purpose | File | Raw URL |
|---|---|---|
| Network logon (4624) — who authenticated | `LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Lateral%20Movement/LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx |
| Execution (Sysmon EID 1 / cmd) — what ran | `revshell_cmd_svchost_sysmon_1.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Execution/revshell_cmd_svchost_sysmon_1.evtx |

### SHA-256 (fill after fetch)

```
<fill after fetch>  LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx
<fill after fetch>  revshell_cmd_svchost_sysmon_1.evtx
```

> Fetch and SHA-256 validation are **deferred to runner-validation** — the download has not been
> executed in authoring.

## Cloud half — CloudTrail (bundled, synthetic)

- `data/cloudtrail/cloudtrail.json` — small bundled AWS CloudTrail set, **modelled on the public
  Lunar Spider cloud TTPs** (see `../ANCHOR.md`) with neutral naming: principal `jsmith`, backdoor
  user `svc-backup`, role `prod-deploy`. Renamed from the prior `meridian_cloudtrail.json`. It stays
  synthetic on purpose (an IAM recon → CreateUser/CreateAccessKey → AssumeRole sequence) and is not
  fetched.
