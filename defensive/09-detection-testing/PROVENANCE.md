# Provenance — Module 09, Detection Testing (Purple Team)

## What ships in this repo

The `atomics/` here are **synthetic emulators**, not the real attacker tooling. Each
produces a Sysmon-shaped event record so the bundled Sigma rules can be exercised
**offline, deterministically, in a Linux container** — no Windows host, no SIEM, no
network. They use neutral placeholder naming (`CORP\auser`, `deploy`). The held-out
corpus (`heldout/corpus.jsonl`) is likewise curated, labelled, and synthetic.

This is honest by design: the emulators are clearly labelled as stand-ins, and each
one **points at the genuine Atomic Red Team test it mirrors**. The real validation
move — running the actual atomic on a Windows lab host and watching your SIEM — is
in `lab.md`.

## The real tests each emulator mirrors

Atomic Red Team (https://github.com/redcanaryco/atomic-red-team) — Red Canary's
library of small, reproducible ATT&CK technique tests. **License: MIT.**

| Emulator (this repo)                | Real Atomic Red Team atomic (verified)                                                        |
|-------------------------------------|-----------------------------------------------------------------------------------------------|
| `atomics/T1059_001_encoded_command.py` | **T1059.001** — PowerShell (encoded command) — https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1059.001 |
| `atomics/T1547_001_run_key.py`         | **T1547.001** — Registry Run Keys / Startup Folder — https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1547.001 |
| `atomics/T1003_001_lsass.py`           | **T1003.001** — OS Credential Dumping: LSASS Memory — https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1003.001 |
| `atomics/T1059_001_benign_fp.py`       | (no atomic — a benign false-positive control: a legitimate base64-over-SSH admin task)        |

The T1059.001 directory includes published encoded-command tests (e.g. the
`-EncodedCommand` parameter-variation tests and *"PowerShell Command Execution"*,
GUID `a538de64-1c74-46ed-aa60-b995ed302598`), which is exactly the behaviour our
encoded-PowerShell emulator stands in for.

## Score the shipped rules over REAL telemetry (`make fetch-events`)

You don't need a Windows host to judge these rules against *real* attacker
telemetry. `make fetch-events` clones **EVTX-ATTACK-SAMPLES** (registered as
`evtx-attack-samples` in `lib/sources.tsv`) and converts the genuine Sysmon
captures for this lab's techniques into `heldout/corpus-real.jsonl` (gitignored);
`make eval-real` then scores the **same shipped Sigma rules** over them.

Real EVTX used (paths discovered from the clone, so they survive upstream
renames within a tree — adjust the `find` globs in the Makefile if a file moves):

| Rule (this lab)            | Real EVTX-ATTACK-SAMPLES capture                                                       | What you see |
|----------------------------|----------------------------------------------------------------------------------------|--------------|
| `registry_run_key.yml` (T1547.001) | `Persistence/evasion_persis_hidden_run_keyvalue_sysmon_13.evtx` (real Sysmon EventID 13) | **Fires** — `TargetObject` is a genuine `…\CurrentVersion\Run\` set. |
| `lsass_access.yml` (T1003.001)     | `Credential Access/sysmon_10_1_memdump_comsvcs_minidump.evtx`, `…/sysmon_10_11_lsass_memdump.evtx` (real Sysmon EventID 10) | **Misses** — real `GrantedAccess` is `0x1fffff`, not the textbook `0x1410` the synthetic corpus and rule assume. A real, valuable finding to investigate. |
| `encoded_powershell.yml` (T1059.001) | (no Sysmon-1 sample) | EVTX-ATTACK-SAMPLES carries encoded PowerShell as **ScriptBlock 4104**, not a `-enc` process-creation command line — itself the lesson that this detection needs PowerShell Script Block Logging, which the synthetic corpus stands in for. |

This is deliberately a **malicious-recall probe**: every record comes from an
attack capture, so each is labelled `malicious`. It measures whether your rule
*fires on real attacker behaviour* — the LSASS miss is the headline result, not a
corpus bug. The committed synthetic `heldout/corpus.jsonl` stays the deterministic
CI gate; this is the "point `--corpus` at real events" move `eval.py` describes.

> Source: sbousseaden/EVTX-ATTACK-SAMPLES (GPL-3.0),
> https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES — converted to the lab's
> corpus shape by `evtx_to_corpus.py` (python-evtx).

## Running the genuine tests

For real host validation, install
[Invoke-AtomicRedTeam](https://github.com/redcanaryco/atomic-red-team/wiki/Installing-Invoke-AtomicRedTeam)
on **your own Windows lab VM**, run the atomic for the technique above, and confirm
your detection fires in the SIEM you stood up in module 06. Run atomics only on a
host you own.

## One-line citation

> Atomic Red Team (T1059.001, T1547.001, T1003.001),
> https://github.com/redcanaryco/atomic-red-team (MIT). The `atomics/` in this lab
> are synthetic emulators of these tests for offline, deterministic CI.
