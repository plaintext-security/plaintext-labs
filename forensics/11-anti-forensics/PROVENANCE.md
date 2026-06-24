# Provenance — Lab 11 Anti-Forensics data

## Real timestomp artifact: EVTX-ATTACK-SAMPLES

- **Dataset:** EVTX-ATTACK-SAMPLES — ~200 real Windows `.evtx` event logs mapped to MITRE ATT&CK.
- **Author / source:** sbousseaden, https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- **License / status:** public repository of research/detection samples (GPL-3.0), freely fetchable.
- **How it is used here:** the real `.evtx` is wired **alongside** the synthetic ext2/disk timestomp
  demo as a real-log cross-check of the same technique (ATT&CK T1070.006 — Timestomp). It does not
  replace the disk image; it complements it. `make fetch-data` downloads it into `data/`.

### File wired

| Purpose | File | Raw URL |
|---|---|---|
| Real timestomp (Sysmon EID 2, file-creation-time modified) | `sysmon_2_11_evasion_timestomp_MACE.evtx` | https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Defense%20Evasion/sysmon_2_11_evasion_timestomp_MACE.evtx |

### SHA-256 (fill after fetch)

```
<fill after fetch>  sysmon_2_11_evasion_timestomp_MACE.evtx
```

> Fetch and SHA-256 validation are **deferred to runner-validation** — the download has not been
> executed in authoring.

## Synthetic disk image (retained)

- `data/disk.img` — generated in-container by `scripts/create_ext2_img.py` (or `scripts/create_disk.sh`
  on a Linux host). Small ext2 image (~2MB), label `BEACHHEAD-WS01`, containing a timestomped binary
  `sihosts.exe` (mtime backdated to 2019), benign files with coherent 2024 timestamps, and a deleted
  `notes.txt` recoverable from unallocated space. Modelled on the Lunar Spider intrusion (see
  `../ANCHOR.md`).
